## Proven identity, now what may it do

Authentication established *who* sent the request. Authorization decides
whether **that identity may perform this verb on this resource**. It runs on
every request, it is configured on the API server, and it is where the
principle of least privilege is either implemented or not.

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
- --authorization-mode=Node,RBAC
```

The flag is a **list**; the modes are tried in order and the first one that
returns allow or deny wins. If none decides, the request is denied.

| Mode | Decides by | Used for |
|---|---|---|
| `Node` | the requester being a kubelet (`system:nodes` group) and the object belonging to *its* node | letting kubelets read their Pods/Secrets/ConfigMaps and write their Node status - and nothing else |
| `RBAC` | Roles/ClusterRoles bound to users, groups and ServiceAccounts | everything you configure yourself |
| `ABAC` | a JSON policy file on the API server (`--authorization-policy-file`) | legacy; needs an API server restart per change |
| `Webhook` | an external HTTP service (`--authorization-webhook-config-file`) | integrating an external policy engine |
| `AlwaysAllow` | - | a cluster with no security; the default if you set nothing |
| `AlwaysDeny` | - | testing |

`Node,RBAC` is the kubeadm default and the one to remember: Node authorizer
first (it only ever answers for kubelets), RBAC for everyone else.

## RBAC in one paragraph

A **Role** is a list of rules - verbs on resources in API groups - scoped to
one namespace; a **ClusterRole** is the same without the namespace scope (or
for cluster-scoped resources like nodes). A **RoleBinding** attaches a Role
*or a ClusterRole* to subjects within a namespace; a **ClusterRoleBinding**
attaches a ClusterRole to subjects across the whole cluster. Subjects are
users, groups, or ServiceAccounts. There is no deny rule: what is not granted
is forbidden. The next two lessons are the practice of it.

## Asking the server

```bash
kubectl auth can-i create deployments                        # as myself, in the current namespace
kubectl auth can-i delete nodes                              # cluster-scoped
kubectl auth can-i list pods --as dev-user -n dev            # impersonate (needs impersonate permission; admins have it)
kubectl auth can-i get pods/log --as system:serviceaccount:dev:builder
kubectl auth can-i --list --as dev-user -n dev               # everything they may do
kubectl auth whoami                                          # how the server sees you
```

`can-i` is the fastest way to test an RBAC change, and to prove to yourself
that a 403 is a permissions problem and not a typo in the object name.

## What a denial looks like

```
Error from server (Forbidden): pods is forbidden: User "dev-user" cannot list resource "pods" in API group "" in the namespace "dev"
```

The message is a complete RBAC rule in prose: **user**, **verb**, **resource**,
**API group**, **namespace**. Write a Role that grants exactly that and bind
it. `403 Forbidden` = authorization said no; `401 Unauthorized` = authentication
failed - different layer, different fix.

:::exam-tip
Read the Forbidden message *literally* and transcribe it into the Role:
resource `pods` → `resources: ["pods"]`; API group `""` → `apiGroups: [""]`;
verb `list` → `verbs: ["list"]`; namespace `dev` → the Role and RoleBinding
go in `dev`. Then `auth can-i` to confirm. Ninety seconds.
:::

## The Node authorizer, briefly

A kubelet authenticates as `system:node:node01` in group `system:nodes`. The
Node authorizer lets it read the Pods scheduled to node01, the Secrets and
ConfigMaps those Pods mount, and update node01's status - and refuses it the
same things for node02. Paired with the `NodeRestriction` admission plugin
(which stops a kubelet from labelling other nodes), a compromised node stays
a compromised node rather than a compromised cluster. You do not configure
this; you need to know it is why kubelets do not need a ClusterRoleBinding.

## Check yourself

1. What does `--authorization-mode=Node,RBAC` mean, in order?
2. Decode this into a Role: `User "ana" cannot create resource "deployments"
   in API group "apps" in the namespace "web"`.
3. Which command tells you whether a ServiceAccount may read Pod logs in a
   namespace, without switching credentials?
