## What a namespace is for

A namespace is a scope for names, plus an attachment point for policy. Two Pods
can both be called `web` as long as they are in different namespaces. RBAC
Roles, ResourceQuotas, LimitRanges and NetworkPolicies all apply per namespace.

What a namespace is **not**: a security boundary by itself. Without
NetworkPolicies, a Pod in `dev` can reach a Pod in `prod` directly by IP.

```bash
kubectl get namespaces
# NAME              STATUS   AGE
# default           Active   10d
# kube-node-lease   Active   10d
# kube-public       Active   10d
# kube-system       Active   10d
```

- `default` - where your objects go if you do not say otherwise.
- `kube-system` - control plane addons: CoreDNS, kube-proxy, CNI.
- `kube-public` - world-readable; holds cluster bootstrap information.
- `kube-node-lease` - node heartbeat Lease objects, used for node health.

## Creating and using namespaces

```bash
kubectl create namespace dev
kubectl create ns dev --dry-run=client -o yaml > ns.yaml
```

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dev
  labels:
    environment: development
```

```bash
kubectl get pods -n dev
kubectl get pods --all-namespaces        # or -A
kubectl apply -f app.yaml -n dev
```

:::warning
`kubectl delete namespace dev` deletes **everything inside it**, and there is no
confirmation prompt. On a shared or exam cluster, check what is in there first:

```bash
kubectl get all -n dev
```
:::

## Contexts: never type -n again

A context binds a cluster, a user and a default namespace.

```bash
kubectl config get-contexts
kubectl config current-context
kubectl config use-context kind-cka
kubectl config set-context --current --namespace=dev
kubectl config view --minify | grep namespace
```

:::exam-tip
Exam questions specify a namespace far more often than people notice, and the
grader checks the namespace. Two habits protect you: set the namespace on the
context at the start of a question, *and* still pass `-n` explicitly on the
command that creates the object. Belt and braces costs three seconds.
:::

## Cluster-scoped objects have no namespace

```bash
kubectl api-resources --namespaced=false
# NAME                  SHORTNAMES  APIVERSION  NAMESPACED  KIND
# namespaces            ns          v1          false       Namespace
# nodes                 no          v1          false       Node
# persistentvolumes     pv          v1          false       PersistentVolume
# storageclasses        sc          storage.k8s.io/v1  false  StorageClass
# clusterroles          ...         rbac.authorization.k8s.io/v1  false  ClusterRole
```

Note the asymmetry that catches people out: **PersistentVolume is cluster-scoped,
PersistentVolumeClaim is namespaced.** So is `Role` (namespaced) versus
`ClusterRole` (not).

## Cross-namespace DNS

Service DNS names encode the namespace:

```text
<service>.<namespace>.svc.cluster.local
```

From a Pod in `dev`:

```bash
curl http://api                       # api in dev (same namespace)
curl http://api.prod                  # api in prod
curl http://api.prod.svc.cluster.local
```

The short form works because of the search domains in `/etc/resolv.conf`:

```bash
kubectl exec -it mypod -- cat /etc/resolv.conf
# search dev.svc.cluster.local svc.cluster.local cluster.local
# nameserver 10.96.0.10
```

## ResourceQuota

Caps aggregate consumption in a namespace.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dev-quota
  namespace: dev
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "20"
    persistentvolumeclaims: "5"
    services.loadbalancers: "1"
```

```bash
kubectl create quota dev-quota --hard=cpu=4,memory=8Gi,pods=20 -n dev
kubectl describe quota -n dev
```

:::warning
Once a ResourceQuota specifying `requests.cpu` or `limits.memory` exists in a
namespace, **every** Pod created there must set those fields. Pods without them
are rejected outright:

`Error: failed quota: dev-quota: must specify limits.memory`

This is a favourite exam scenario: a Deployment that will not create any Pods,
with the reason visible only in the ReplicaSet's events, not the Deployment's.

```bash
kubectl describe rs <replicaset-name> -n dev
```
:::

## LimitRange

Supplies defaults and bounds per object, which is how you make a quota usable
without editing every manifest.

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: dev-limits
  namespace: dev
spec:
  limits:
    - type: Container
      default:                 # applied as limits when omitted
        cpu: 500m
        memory: 512Mi
      defaultRequest:          # applied as requests when omitted
        cpu: 100m
        memory: 128Mi
      max:
        cpu: "2"
        memory: 2Gi
      min:
        cpu: 50m
        memory: 64Mi
```

With this in place, a Pod that specifies nothing still gets requests and limits,
so it satisfies the quota.

## A namespace stuck Terminating

```bash
kubectl get ns dev -o json | jq '.status'
# {"conditions": [...], "phase": "Terminating"}
```

Usually one of two things: a resource with a finalizer that cannot complete, or
an unavailable APIService blocking discovery.

```bash
kubectl api-resources --verbs=list --namespaced -o name \
  | xargs -n1 kubectl get -n dev --ignore-not-found

kubectl get apiservice | grep -v True    # an unhealthy aggregated API
```

## Check yourself

1. Which of these are namespaced: PersistentVolume, PersistentVolumeClaim, Role,
   ClusterRole, StorageClass?
2. A Deployment in a quota-constrained namespace creates no Pods. Where is the
   error message?
3. From a Pod in `dev`, what DNS name reaches the `api` Service in `prod`?
