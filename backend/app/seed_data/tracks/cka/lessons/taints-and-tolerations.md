## Repelling Pods from nodes

A **taint** is a mark on a node that says "do not schedule here unless you
are allowed". A **toleration** is the matching mark on a Pod that says "I am
allowed". Taints push; tolerations permit. Neither *attracts* - a Pod with a
toleration can land on a tainted node, but nothing makes it prefer one. That
job belongs to affinity.

```bash
kubectl taint nodes node01 spray=mortein:NoSchedule
kubectl describe node node01 | grep Taints
# Taints:  spray=mortein:NoSchedule
kubectl taint nodes node01 spray=mortein:NoSchedule-      # the trailing minus removes it
```

A taint is `key=value:effect`. The effect is what happens to Pods that do not
tolerate it:

| Effect | Existing Pods | New Pods |
|---|---|---|
| `NoSchedule` | stay | are not placed here |
| `PreferNoSchedule` | stay | avoided if any other node will do |
| `NoExecute` | **evicted** (after `tolerationSeconds`, if set) | are not placed here |

## Writing a toleration

```yaml
spec:
  tolerations:
    - key: spray
      operator: Equal
      value: mortein
      effect: NoSchedule
```

Every line is a quoted string in YAML terms - `value: "mortein"` - and the
operator is `Equal` (key and value must match) or `Exists` (key alone; leave
`value` out). A toleration with **no key and `operator: Exists`** tolerates
everything, which is how some DaemonSets run on every node regardless.

```yaml
tolerations:
  - operator: Exists          # tolerate all taints
```

```yaml
tolerations:
  - key: node.kubernetes.io/not-ready
    operator: Exists
    effect: NoExecute
    tolerationSeconds: 300    # stay 5 minutes on a NotReady node, then leave
```

That last one is on every Pod by default - it is why Pods survive a node
flapping for a few minutes and get evicted if it stays down.

## The control plane taint

```bash
kubectl describe node controlplane | grep Taints
# Taints:  node-role.kubernetes.io/control-plane:NoSchedule
```

kubeadm taints control plane nodes so ordinary workloads stay off them. Two
consequences:

- On a single-node cluster nothing schedules until you remove it
  (`kubectl taint nodes controlplane node-role.kubernetes.io/control-plane:NoSchedule-`).
- Control plane components and kube-proxy/CNI DaemonSets carry a toleration
  for it; that is how they run there.

:::exam-tip
A Pod stuck Pending with the event `0/2 nodes are available: 1 node(s) had
untolerated taint {...}, 1 node(s) ...` is telling you the whole story. Read
the taint it names, decide: tolerate it on the Pod (task says the Pod must run
there) or remove it from the node (task says the node should accept workloads).
:::

## Taints vs tolerations vs what you wanted

Taints are node-centric: "this node is special, keep the riff-raff away" -
GPU nodes, nodes reserved for a team, a node under maintenance. They do not
say "put the GPU Pods *here*". A GPU Pod with the right toleration can still
be scheduled onto a plain node. To get both halves - reserved nodes **and**
Pods that only go there - you combine a taint with a **nodeSelector** or
**node affinity**, which is the subject of the next three lessons.

## Quick reference

```bash
kubectl taint nodes node01 key=value:NoSchedule        # add
kubectl taint nodes node01 key=value:NoSchedule-       # remove
kubectl taint nodes node01 key:NoExecute-              # remove by key+effect
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints
kubectl run bee --image=nginx $do > bee.yaml           # then add tolerations under spec
```

:::tip
There is no `kubectl run --toleration` flag. Generate the YAML, add the block
under `spec:` (not under the container), apply.
:::

## Check yourself

1. What is the difference in effect between `NoSchedule` and `NoExecute` for a
   Pod that is already running on the node?
2. Write a toleration that tolerates *any* taint.
3. A node is tainted `env=prod:NoSchedule` and a Pod tolerates it. Will the Pod
   necessarily run on that node? What else would you add to make sure?
