## Roles say what; bindings say who

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer
  namespace: dev
rules:
  - apiGroups: [""]                      # core group: pods, services, configmaps...
    resources: ["pods"]
    verbs: ["get", "list", "watch", "create", "delete"]
  - apiGroups: [""]
    resources: ["pods/log"]               # a subresource is its own resource
    verbs: ["get"]
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "create", "update", "patch"]
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["app-config"]         # optional: only this one object
    verbs: ["get", "update"]
```

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: developer-binding
  namespace: dev
subjects:
  - kind: User
    name: dev-user                        # CN of their certificate, or OIDC username
    apiGroup: rbac.authorization.k8s.io
  - kind: Group
    name: developers                      # O of their certificate
    apiGroup: rbac.authorization.k8s.io
  - kind: ServiceAccount
    name: builder
    namespace: dev                        # ServiceAccounts carry a namespace, not an apiGroup
roleRef:
  kind: Role
  name: developer
  apiGroup: rbac.authorization.k8s.io
```

A binding has **one** roleRef and **many** subjects. `roleRef` is immutable -
to point a binding at a different Role you delete and recreate it.

## The imperative way, which is the exam way

```bash
kubectl create role developer -n dev \
  --verb=get,list,watch,create,delete --resource=pods \
  --verb=get --resource=pods/log
kubectl create role developer -n dev --verb=get,list --resource=deployments.apps      # group after a dot when ambiguous

kubectl create rolebinding developer-binding -n dev --role=developer --user=dev-user
kubectl create rolebinding developer-binding -n dev --role=developer --group=developers
kubectl create rolebinding builder-binding -n dev --role=developer --serviceaccount=dev:builder

kubectl get roles,rolebindings -n dev
kubectl describe role developer -n dev            # a readable table of rules
kubectl describe rolebinding developer-binding -n dev
kubectl auth can-i create pods --as dev-user -n dev      # yes
kubectl auth can-i create pods --as dev-user              # no - wrong namespace
```

`kubectl create role` accepts several `--verb`/`--resource` pairs; the verbs
before each `--resource` apply to it. When in doubt, `$do` and read the YAML
it produced.

:::exam-tip
Three checks before you move on from any RBAC task: the **namespace** on
both Role and RoleBinding (a Role in `default` does nothing for `dev`); the
**apiGroups** (`""` vs `apps`); and `kubectl auth can-i <verb> <resource>
--as <user> -n <ns>` returning `yes`. If the task also says "and the user
should be able to run kubectl logs", add `pods/log`.
:::

## Binding a ClusterRole in a namespace

A RoleBinding may reference a **ClusterRole** instead of a Role. The
permissions are still confined to the binding's namespace - that is how you
define "what a viewer may do" once as a ClusterRole and hand it out per
namespace:

```bash
kubectl create rolebinding ana-view -n dev --clusterrole=view --user=ana
```

The built-in ClusterRoles `view`, `edit`, `admin` (namespace admin) and
`cluster-admin` are made for this; `kubectl describe clusterrole edit` shows
what a sensible "developer" set looks like.

## Reading what someone can do

```bash
kubectl auth can-i --list --as dev-user -n dev
kubectl get rolebindings -n dev -o wide                       # SUBJECTS column
kubectl get rolebindings -A -o json | jq -r '.items[] | select(.subjects[]?.name=="dev-user") | "\(.metadata.namespace)/\(.metadata.name)"'
```

No `kubectl get permissions-for user` exists; the last line is the honest
way, and `can-i --list` is the quick one.

## Mistakes that produce a silent "Forbidden"

| Mistake | Symptom |
|---|---|
| `apiGroups: ["apps"]` for Pods | `pods is forbidden ... in API group ""` |
| `resources: ["pod"]` (singular) or `["Pods"]` | forbidden; resource names are plural, lowercase |
| Role in the wrong namespace | forbidden in the namespace you meant |
| `verbs: ["get"]` but the user runs `kubectl get pods` | forbidden: that is `list` |
| subject `kind: User` with `name: dev-user` but the cert CN is `developer` | forbidden: the name must match exactly |
| ServiceAccount subject without `namespace:` | the binding is created but matches nothing |

## Check yourself

1. Write a Role granting get/list/watch on Pods and get on their logs, in
   namespace `dev`, and the RoleBinding for user `dev-user` - as two `kubectl
   create` commands.
2. What is the difference between binding a Role and binding a ClusterRole
   with a RoleBinding?
3. `kubectl auth can-i get pods --as dev-user -n dev` says yes, but
   `kubectl get pods -n dev` as dev-user says Forbidden. Which verb is
   missing?
