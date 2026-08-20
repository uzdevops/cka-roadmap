## The simplest way to pick a node

Nodes carry labels just like Pods do. `nodeSelector` says: only consider nodes
with these labels.

```bash
kubectl label nodes node01 size=large
kubectl get nodes --show-labels
kubectl get nodes -l size=large
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: data-processor
spec:
  nodeSelector:
    size: large
  containers:
    - name: app
      image: data-processor:2.1
```

The scheduler filters out every node without `size=large` and then scores the
rest as usual. If no node matches, the Pod stays Pending with a clear event:
`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`.

## The labels you already have

Every node carries a set of built-in labels worth knowing, because tasks use
them:

```bash
kubectl describe node node01 | grep -A12 Labels
```

| Label | Example |
|---|---|
| `kubernetes.io/hostname` | `node01` |
| `kubernetes.io/os` / `kubernetes.io/arch` | `linux` / `amd64` |
| `node-role.kubernetes.io/control-plane` | present (empty value) on control plane nodes |
| `topology.kubernetes.io/zone` / `region` | set by cloud providers |
| `node.kubernetes.io/instance-type` | cloud instance size |

```yaml
nodeSelector:
  kubernetes.io/hostname: node01     # pin to one node, the declarative way
```

## Where it stops being enough

`nodeSelector` is AND-only equality: every listed label must match exactly.
You cannot say

- "large **or** medium",
- "anything **except** small",
- "prefer large, but anything will do".

For those you need **node affinity**, the next lesson, which has operators
(`In`, `NotIn`, `Exists`, `DoesNotExist`, `Gt`, `Lt`) and a *preferred* mode.
`nodeSelector` stays the right tool when the rule is one or two exact labels -
it is shorter to write and impossible to get wrong.

:::exam-tip
A task that says "schedule the Pod on the node labelled `disktype=ssd`" is a
`nodeSelector` task - do not reach for the affinity block. A task that says
"on a node labelled `size=large` **or** `size=medium`" is affinity.
:::

## Labelling nodes, properly

```bash
kubectl label nodes node01 disktype=ssd                 # add
kubectl label nodes node01 disktype=nvme --overwrite    # change
kubectl label nodes node01 disktype-                    # remove
kubectl label nodes -l kubernetes.io/os=linux tier=app  # label many at once
```

:::warning
Labels on nodes are not persisted anywhere else: if the node is rebuilt, the
label is gone unless your provisioning re-applies it. In a kubeadm cluster the
kubelet's `--node-labels` flag (in `/var/lib/kubelet/kubeadm-flags.env`) is
where a label survives a rebuild.
:::

## Check yourself

1. Write the two commands that label node01 `disktype=ssd` and then remove
   that label.
2. A Pod with a `nodeSelector` stays Pending. What does its event say, and
   what are the two things you check?
3. Give two requirements `nodeSelector` cannot express that node affinity can.
