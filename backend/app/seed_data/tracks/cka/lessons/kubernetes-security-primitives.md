## The shape of the problem

Everything in a cluster goes through the API server, so securing a cluster
starts with two questions about the API server and ends with a third about
the workloads:

1. **Who can reach the API server?** - authentication
2. **What may they do once there?** - authorization (and admission)
3. **What can the workloads do to each other and to the nodes?** - network
   policies, security contexts, Pod security

Plus the thing under all of it: every component talks to every other over
**TLS**, with certificates a cluster CA signed. This phase takes those in
order: TLS and certificates first, then authentication and authorization,
then the workload-level controls.

## Who reaches the API server

| Caller | Proves identity with |
|---|---|
| administrators, developers | client certificates, or tokens from an identity provider |
| kubelets, scheduler, controller manager | client certificates in their kubeconfigs |
| Pods | ServiceAccount tokens |
| external systems (CI, dashboards) | ServiceAccount tokens or OIDC |

The API server will refuse anonymous requests to almost everything (it
allows `/healthz`, `/version` and the like). Every other request is attached
to a user or a service account, and that identity is what authorization
works on.

```bash
kubectl config view --minify            # what identity is YOUR kubectl using?
kubectl auth whoami                     # the server's view of it
kubectl auth can-i create deployments -n dev
```

## What they may do

**Authorization modes**, enabled as a list on the API server; the first one
to decide wins:

- `Node` - kubelets may only touch their own node's objects;
- `RBAC` - Roles and ClusterRoles bound to users and groups: the one you
  write;
- `ABAC` - a policy file (legacy);
- `Webhook` - ask an external service.

```bash
ps -ef | grep kube-apiserver | grep -o -- '--authorization-mode=[^ ]*'
# --authorization-mode=Node,RBAC
```

After authorization, **admission** may still refuse or rewrite the object -
Pod Security admission is the workload-security piece that lives there.

## Workloads and nodes

Once a Pod is running, what stops it from reaching every other Pod and every
node? By default: nothing. All Pods can talk to all Pods (the network model
promises it), and a container runs as whatever user its image says, root
included. The controls you add:

| Risk | Control |
|---|---|
| any Pod reaches any Pod | NetworkPolicy (requires a CNI that enforces it) |
| container runs as root, with capabilities | securityContext, Pod Security admission |
| Pod reads Secrets it should not | RBAC on the ServiceAccount, not mounting the token |
| image from anywhere | imagePullSecrets, private registry, admission policy on registries |
| container escapes to the node | no privileged, no hostPath, no hostNetwork unless required |

## The certificates underneath

Every arrow in the architecture diagram is a TLS connection: kubectl → API
server, API server → etcd, API server → kubelet, kubelet → API server,
scheduler → API server. Each end has a certificate signed by a CA the other
end trusts. kubeadm creates all of them and puts them in
`/etc/kubernetes/pki`. When they expire, things stop working in ways that
look like network problems; when a path to one is wrong, a component
crash-loops. The next five lessons are about reading and issuing them.

:::exam-tip
Security tasks in the exam are concrete, not conceptual: create a Role and
bind it, generate a certificate and approve a CSR, write a NetworkPolicy,
set a securityContext, create a ServiceAccount and use it. This lesson is the
map; the marks are in the next ones.
:::

## Check yourself

1. Name the three questions cluster security answers, and the mechanism that
   answers each.
2. What are the default network rules between Pods in a fresh cluster?
3. Which file directory holds a kubeadm cluster's certificates?
