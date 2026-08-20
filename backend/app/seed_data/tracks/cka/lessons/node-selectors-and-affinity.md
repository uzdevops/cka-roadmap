## nodeSelector with a vocabulary

Node affinity does what `nodeSelector` does - restrict which nodes a Pod may
land on, by node labels - with operators, OR, and the ability to *prefer*
rather than require.

```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: size
                operator: In
                values: [large, medium]
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 80
          preference:
            matchExpressions:
              - key: disktype
                operator: In
                values: [ssd]
  containers:
    - name: app
      image: data-processor:2.1
```

Read the two long names literally:

| Field | During scheduling | Once running |
|---|---|---|
| `requiredDuringSchedulingIgnoredDuringExecution` | must match or the Pod stays Pending | label changes on the node do not evict it |
| `preferredDuringSchedulingIgnoredDuringExecution` | try to match; fall back to any node | likewise |

"IgnoredDuringExecution" is the only variant that exists today: affinity is
checked at scheduling time and never again. (A `RequiredDuringExecution`
version that evicts Pods when labels change has been planned for years.)

## Operators

| Operator | Meaning | `values` |
|---|---|---|
| `In` | label value is one of | required |
| `NotIn` | label value is none of | required |
| `Exists` | label key is present | omit |
| `DoesNotExist` | label key is absent | omit |
| `Gt` / `Lt` | numeric comparison | one value |

`NotIn` and `DoesNotExist` give you **node anti-affinity** - "not on the small
nodes", "not on control plane nodes" - which `nodeSelector` cannot say.

## AND, OR, and the shape of the block

- Several `matchExpressions` in **one** `nodeSelectorTerms` entry are ANDed.
- Several entries in `nodeSelectorTerms` are ORed.
- Preferred rules carry a `weight` 1-100; the scheduler adds up the weights of
  the rules a node satisfies and the highest total wins the scoring phase.

```yaml
nodeSelectorTerms:
  - matchExpressions:                    # (size=large AND disktype=ssd)
      - {key: size, operator: In, values: [large]}
      - {key: disktype, operator: In, values: [ssd]}
  - matchExpressions:                    # OR (zone=b)
      - {key: topology.kubernetes.io/zone, operator: In, values: [b]}
```

:::exam-tip
The nesting is the hard part, not the idea. `kubectl explain
pod.spec.affinity.nodeAffinity --recursive` prints the exact tree. Copy the
field names from there rather than from memory - `nodeSelectorTerms` is a
list, `matchExpressions` is a list, `values` is a list.
:::

## Two tasks you will meet

**"Pods of Deployment blue must only run on nodes labelled color=blue":**

```bash
kubectl label node node01 color=blue
kubectl create deployment blue --image=nginx --replicas=3 $do > blue.yaml
```
then add under `spec.template.spec`:
```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: color
              operator: In
              values: [blue]
```

**"Deployment red must run only on control plane nodes":** the label is
`node-role.kubernetes.io/control-plane` with an empty value, so the operator
is `Exists` - and because the control plane is tainted you **also** need a
toleration:

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: node-role.kubernetes.io/control-plane
              operator: Exists
tolerations:
  - key: node-role.kubernetes.io/control-plane
    operator: Exists
    effect: NoSchedule
```

## Pod affinity, briefly

The same block shape exists as `podAffinity` and `podAntiAffinity`, matching
the labels of **other Pods** instead of nodes, within a `topologyKey`
(`kubernetes.io/hostname` = same node, `topology.kubernetes.io/zone` = same
zone). "Spread my replicas across nodes" is a podAntiAffinity on the app's own
label with `topologyKey: kubernetes.io/hostname`. It appears in the exam
rarely; know that it exists and that `topologyKey` is required.

## Check yourself

1. What does "IgnoredDuringExecution" mean in practice when a node's label is
   removed?
2. Write the matchExpression for "the node does **not** have label
   `size=small`".
3. A Deployment must run only on control plane nodes. Which two blocks does the
   Pod template need, and why two?
