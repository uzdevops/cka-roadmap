## Identity for Pods

Users are for people and tools outside the cluster. A **ServiceAccount** is
the identity a **Pod** runs as, and the thing RBAC binds to when a program
inside the cluster needs to talk to the API - a dashboard listing Pods, a CI
runner creating Jobs, an operator watching its CRDs.

```bash
kubectl get serviceaccounts                  # every namespace has `default`
kubectl create serviceaccount dashboard-sa
kubectl describe sa dashboard-sa
```

```yaml
spec:
  serviceAccountName: dashboard-sa           # default: "default"
  automountServiceAccountToken: false         # if the Pod never calls the API, do not give it a token
  containers: [...]
```

Every Pod runs as *some* ServiceAccount - `default` if you say nothing.
`default` has no RBAC grants, so it is harmless but also useless: a Pod that
needs permissions gets its own account and a binding.

```bash
kubectl create sa dashboard-sa
kubectl create role pod-reader --verb=get,list --resource=pods
kubectl create rolebinding dashboard-binding --role=pod-reader --serviceaccount=default:dashboard-sa
kubectl set serviceaccount deployment web-dashboard dashboard-sa      # rolls the Pods
```

In RBAC subjects a ServiceAccount is `kind: ServiceAccount` with a
`namespace`; in `--as` and in messages it is `system:serviceaccount:<ns>:<name>`.

## Tokens: how a Pod proves it

Inside a Pod with a mounted token:

```bash
ls /var/run/secrets/kubernetes.io/serviceaccount/
# ca.crt  namespace  token
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
curl -s --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/namespaces/default/pods
```

The token is a JWT signed by the API server's `sa.key`; the API server
verifies it with `sa.pub` and maps it to the ServiceAccount. Since 1.24 it
is a **bound, projected, expiring** token: minted by the kubelet through the
TokenRequest API for that specific Pod, valid for an hour and refreshed in
place, invalid once the Pod is gone. The kubelet mounts it as a projected
volume - which is what `automountServiceAccountToken` controls.

For anything **outside** a Pod that needs a ServiceAccount identity - a CI
system, a `curl` from your laptop - you request a token:

```bash
kubectl create token dashboard-sa                    # 1 hour, by default
kubectl create token dashboard-sa --duration=8h
TOKEN=$(kubectl create token dashboard-sa)
curl -sk https://<apiserver>:6443/api/v1/pods -H "Authorization: Bearer $TOKEN"
kubectl config set-credentials dashboard --token=$TOKEN
```

## The old way, and why you may still see it

Before 1.24 every ServiceAccount got a **Secret** of type
`kubernetes.io/service-account-token` containing a non-expiring token, listed
under `describe sa` as `Tokens:`. New clusters do not create those any more.
If a task insists on a long-lived token, you can still make one by hand:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: dashboard-sa-token
  annotations:
    kubernetes.io/service-account.name: dashboard-sa
type: kubernetes.io/service-account-token
```

The controller manager fills in `data.token`. Treat it like a password that
never expires, because that is what it is.

:::exam-tip
"Create a ServiceAccount and grant it X" is three commands: `create sa`,
`create role` (or use an existing ClusterRole), `create rolebinding
--serviceaccount=<ns>:<name>`. "Get a token for it" is `kubectl create token
<name>`. Do not go looking for a Secret on a modern cluster - there is none
unless you make it.
:::

## Locking it down

- `automountServiceAccountToken: false` on the Pod spec (or on the
  ServiceAccount) for workloads that never call the API - most of them.
- Do not grant `default` anything; give each workload its own account.
- `imagePullSecrets` on a ServiceAccount are inherited by every Pod using it
  - a convenient place for registry credentials.
- Audit: `kubectl get rolebindings,clusterrolebindings -A -o json | jq` for
  `system:serviceaccounts` as a subject - that grants something to *every*
  Pod in the cluster.

## Check yourself

1. A Pod does not specify `serviceAccountName`. What identity does it have,
   and what may it do?
2. How do you get a token for a ServiceAccount to use from outside the
   cluster, and how long is it valid?
3. What is mounted at `/var/run/secrets/kubernetes.io/serviceaccount/`, and
   which Pod field turns that off?
