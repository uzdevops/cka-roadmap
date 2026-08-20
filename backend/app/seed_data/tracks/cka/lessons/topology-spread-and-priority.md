## Some Pods matter more than others

When a cluster is full, the scheduler has a choice to make: leave the new Pod
Pending, or **evict** something less important to make room. Priority is how
you tell it which Pods are less important.

A **PriorityClass** is a cluster-wide object that names an integer:

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 100000
globalDefault: false
preemptionPolicy: PreemptLowerPriority     # the default; the other value is Never
description: "Customer-facing workloads"
```

```bash
kubectl create priorityclass high-priority --value=100000 --description="urgent"
kubectl get priorityclass
# NAME                      VALUE        GLOBAL-DEFAULT
# high-priority             100000       false
# system-cluster-critical   2000000000   false
# system-node-critical      2000001000   false
```

The two `system-*` classes ship with every cluster and are what the control
plane components and CNI/kube-proxy DaemonSets use. User classes go up to one
billion (`1000000000`); higher values are reserved.

A Pod opts in by name:

```yaml
spec:
  priorityClassName: high-priority
  containers: [...]
```

Pods without one get priority **0**, unless a class has `globalDefault: true`
(at most one may).

## Preemption

When a high-priority Pod cannot be scheduled, the scheduler looks for a node
where evicting some *lower*-priority Pods would make it fit, evicts them (they
get their graceful termination), and places the new Pod. The evicted Pods go
back to Pending and are rescheduled if a controller owns them.

```bash
kubectl get events --sort-by=.lastTimestamp | grep -i preempt
# Normal  Preempted  pod/batch-7xk2  Preempted by default/important on node node02
```

`preemptionPolicy: Never` makes a class that is scheduled ahead of lower
priorities *in the queue* but never evicts anyone - useful for "important but
not worth killing for" batch work.

:::exam-tip
Priority only matters when something does not fit. On an empty cluster a
high-priority Pod schedules exactly like any other. If a task asks you to
"ensure Pod X is scheduled even under pressure", priority is the answer; if
it asks "why was Pod Y evicted", look for a preemption event naming a
higher-priority Pod.
:::

## Topology spread

A related scheduling control with a different goal: spreading replicas evenly
across failure domains so that losing one node or zone does not take down the
whole application.

```yaml
spec:
  topologySpreadConstraints:
    - maxSkew: 1
      topologyKey: topology.kubernetes.io/zone
      whenUnsatisfiable: DoNotSchedule        # or ScheduleAnyway
      labelSelector:
        matchLabels:
          app: web
  containers: [...]
```

Read it as: among the Pods labelled `app=web`, the number in any one zone may
not exceed the number in any other by more than `maxSkew`. With
`DoNotSchedule` it is a hard rule (Pods stay Pending rather than break it);
with `ScheduleAnyway` it is a preference. `kubernetes.io/hostname` as the key
spreads across nodes instead of zones.

This is the modern way to say "one replica per node, please" for a Deployment
- podAntiAffinity does the same more rigidly.

## Check yourself

1. A Pod with no `priorityClassName` has what priority, and can it ever
   preempt anything?
2. What does `preemptionPolicy: Never` change, and when would you want it?
3. Write the topologySpreadConstraint that spreads `app=api` Pods across
   nodes with at most one Pod of difference, as a hard rule.
