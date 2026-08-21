## Permissions that do not fit in a namespace

Some resources are not in any namespace - nodes, PersistentVolumes,
StorageClasses, Namespaces themselves, ClusterRoles, CSRs. A Role cannot
grant anything about them, because a Role lives in a namespace and those do
not. The **ClusterRole** and **ClusterRoleBinding** pair is the cluster-wide
version.

```bash
kubectl api-resources --namespaced=false        # the things that need a ClusterRole
```

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-admin                # no namespace
rules:
  - apiGroups: [""]
    resources: ["nodes"]
    verbs: ["get", "list", "watch", "create", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: michelle-node-admin
subjects:
  - kind: User
    name: michelle
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: node-admin
  apiGroup: rbac.authorization.k8s.io
```

```bash
kubectl create clusterrole node-admin --verb=get,list,watch,create,delete --resource=nodes
kubectl create clusterrolebinding michelle-node-admin --clusterrole=node-admin --user=michelle
kubectl auth can-i list nodes --as michelle                    # yes

kubectl create clusterrole storage-admin --verb='*' --resource=persistentvolumes,storageclasses
kubectl create clusterrolebinding michelle-storage-admin --clusterrole=storage-admin --user=michelle
```

## ClusterRoles for namespaced resources too

A ClusterRole may name namespaced resources - `pods`, `deployments`. Bound
with a **ClusterRoleBinding**, it grants them in **every** namespace; bound
with a **RoleBinding** in namespace `dev`, it grants them in `dev` only.

| Role kind | Binding kind | Effective scope |
|---|---|---|
| Role | RoleBinding | one namespace (the Role's) |
| ClusterRole | RoleBinding | one namespace (the binding's) |
| ClusterRole | ClusterRoleBinding | every namespace + cluster-scoped resources |
| Role | ClusterRoleBinding | **not allowed** |

That middle row is the one to remember: define once, bind per namespace.

```bash
kubectl create rolebinding ana-edit -n dev --clusterrole=edit --user=ana
```

## The built-in ones

```bash
kubectl get clusterroles | head -40
kubectl describe clusterrole view
```

| ClusterRole | Intended for |
|---|---|
| `cluster-admin` | everything, everywhere; bound to group `system:masters` by default |
| `admin` | full control in a namespace, including RBAC there (via RoleBinding) |
| `edit` | read/write most objects in a namespace; not RBAC |
| `view` | read-only in a namespace; cannot read Secrets |
| `system:*` | the components - `system:kube-scheduler`, `system:node`, `system:kube-controller-manager` ... |

Bind the built-ins before writing your own: "give ana read-only access to
namespace dev" is `rolebinding ... --clusterrole=view`, one line, and it is
maintained by the project.

:::exam-tip
The question usually tells you the scope in its nouns: **nodes**,
**persistentvolumes**, **storageclasses**, **namespaces** → ClusterRole +
ClusterRoleBinding. **pods**, **deployments** "in namespace X" → Role +
RoleBinding (or ClusterRole + RoleBinding). "in all namespaces" → ClusterRole
+ ClusterRoleBinding. Mixing them up produces a binding that exists and
grants nothing.
:::

## Aggregated ClusterRoles

`view`, `edit` and `admin` are **aggregated**: the controller manager builds
them from every ClusterRole labelled to be included. That is how a CRD's
author lets `view` see their new resource without editing the built-in role:

```yaml
metadata:
  labels:
    rbac.authorization.k8s.io/aggregate-to-view: "true"
```

You will not write one in the exam; you will see the label when you
`describe clusterrole view` and wonder where the rules come from.

## Reading cluster-wide grants

```bash
kubectl get clusterrolebindings -o wide | grep michelle
kubectl describe clusterrolebinding cluster-admin      # who is cluster-admin right now - a security audit in one line
kubectl auth can-i --list --as michelle                # no -n: cluster-scoped view
```

## Check yourself

1. Which three of these need a ClusterRole: pods, nodes, deployments,
   storageclasses, namespaces?
2. What does binding a ClusterRole with a RoleBinding achieve, and why would
   you do it?
3. How do you find out who currently holds `cluster-admin`?
