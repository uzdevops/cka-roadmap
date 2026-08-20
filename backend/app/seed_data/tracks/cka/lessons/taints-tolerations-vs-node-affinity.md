## Two halves of one problem

Imagine three teams - blue, red, green - each with a dedicated node, plus two
shared nodes for everyone else. You want:

1. team Pods **only** on their own node, and
2. other people's Pods **never** on the team nodes.

Neither mechanism does both.

## Taints and tolerations alone

Taint the three nodes (`color=blue:NoSchedule` and so on) and give each team's
Pods the matching toleration. Requirement 2 is met: a random Pod cannot land
on a team node. But requirement 1 is not - a blue Pod *tolerates* the blue
node, it is not *drawn* to it, and it may perfectly well be scheduled onto a
shared node.

```
blue Pod ──▶ blue node   ✓ allowed
blue Pod ──▶ shared node ✓ also allowed   <- the gap
red  Pod ──▶ blue node   ✗ untolerated taint
```

## Node affinity alone

Label the nodes (`color=blue`) and give each team's Pods a required node
affinity on their colour. Requirement 1 is met: blue Pods go only to the blue
node. But requirement 2 is not - a Pod with no affinity rule at all may land
anywhere, including the blue node.

```
blue Pod ──▶ blue node   ✓ required
blue Pod ──▶ shared node ✗ affinity not matched
other Pod ─▶ blue node   ✓ nothing stops it   <- the gap
```

## Both together

Taint **and** label the team nodes; give team Pods a toleration **and** an
affinity. Now blue Pods can only go to blue (affinity) and only blue Pods can
go there (taint). Shared nodes, with neither taint nor label, take everyone
else.

| | taints/tolerations | node affinity | both |
|---|---|---|---|
| keep others off my node | yes | no | yes |
| keep my Pods on my node | no | yes | yes |

```yaml
# the blue team's Pod template
spec:
  tolerations:
    - key: color
      operator: Equal
      value: blue
      effect: NoSchedule
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: color
                operator: In
                values: [blue]
```

```bash
kubectl taint nodes node01 color=blue:NoSchedule
kubectl label  nodes node01 color=blue
```

:::exam-tip
When a task describes a *dedicated* node - "only the monitoring Pods may run
on node03, and they must run there" - it is asking for both. When it says only
one of the sentences, it is asking for only one. Read which verbs are present:
"must run on" = affinity; "nothing else may run on" = taint.
:::

## Which to reach for when

| Situation | Tool |
|---|---|
| keep general workloads off special nodes (GPU, control plane, maintenance) | taint |
| put specific workloads on specific nodes | nodeSelector / affinity |
| both | both |
| "prefer" rather than "must" | preferred affinity (taints have `PreferNoSchedule` for the other direction) |
| drain a node for maintenance | `kubectl drain` (which is a `NoExecute` taint plus eviction, done for you) |

:::tip
`kubectl cordon` is a taint in disguise: it marks the node unschedulable
(`node.kubernetes.io/unschedulable:NoSchedule`). `kubectl drain` adds eviction.
Knowing that helps when a node shows `SchedulingDisabled` and you wonder who
tainted it.
:::

## Check yourself

1. With only taints and tolerations, can you guarantee a blue Pod runs on the
   blue node? Why not?
2. With only node affinity, can you guarantee nothing else runs on the blue
   node? Why not?
3. A task says "Pods of Deployment `mon` must run on node03 and no other Pods
   may run there." List every command and YAML block you need.
