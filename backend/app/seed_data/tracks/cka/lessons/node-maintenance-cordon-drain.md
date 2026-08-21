## Taking a node out of service, safely

A kernel patch, a reboot, a hardware swap: the node will be gone for a while,
and you do not want Kubernetes to treat that as a surprise. Three commands
make it deliberate.

```bash
kubectl cordon node01        # mark unschedulable: nothing NEW lands here; existing Pods stay
kubectl drain node01 ...     # cordon + evict every Pod, gracefully, so controllers recreate them elsewhere
kubectl uncordon node01      # back in service
```

```bash
kubectl get nodes
# NAME     STATUS                     ROLES    AGE   VERSION
# node01   Ready,SchedulingDisabled   <none>   10d   v1.30.2
```

`SchedulingDisabled` is what cordon looks like. Under the hood it is a taint
- `node.kubernetes.io/unschedulable:NoSchedule` - which is why everything you
learned about taints applies.

## drain, and the flags it will demand

```bash
kubectl drain node01 --ignore-daemonsets
```

Drain refuses by default in two situations, and tells you which flag to add:

| Message | Because | Flag |
|---|---|---|
| `cannot delete DaemonSet-managed Pods` | a DaemonSet would recreate them on the same node anyway; evicting is pointless | `--ignore-daemonsets` |
| `cannot delete Pods not managed by ReplicationController, ReplicaSet, Job, DaemonSet or StatefulSet` | a bare Pod will **not** come back anywhere - you would be destroying it | `--force` |
| `cannot delete Pods with local storage` | emptyDir data is lost on eviction | `--delete-emptydir-data` |

`--force` is the one to pause on: it means "yes, delete that unmanaged Pod for
good". In the exam a task may say "the Pod must not be lost" - then you cannot
drain; you cordon, and move the Pod by hand.

```bash
kubectl drain node01 --ignore-daemonsets --delete-emptydir-data --force --grace-period=30
```

Drain **evicts** (through the Eviction API), so it respects
PodDisruptionBudgets: if a PDB says "at least 2 of 3 web Pods must stay up"
and evicting would break that, drain waits and retries. That is a feature -
and the cause of "my drain hangs forever" when a PDB can never be satisfied.

## What happens to the evicted Pods

They are deleted with their grace period; their controllers (ReplicaSet,
StatefulSet, Job) create replacements, which the scheduler places on the
remaining nodes - assuming there is room. On a two-node cluster draining one
worker means the other must hold everything; if it cannot, Pods sit Pending
until the node is back.

```bash
kubectl get pods -A -o wide | grep node01     # should be only DaemonSet Pods now
```

## The node-controller timeout, for contrast

If you *do not* drain and just reboot, the kubelet stops heartbeating, the
node goes `NotReady` after ~40 s, and after the **pod-eviction timeout**
(5 minutes by default, the `node.kubernetes.io/not-ready:NoExecute`
toleration with `tolerationSeconds: 300` on every Pod) the node controller
evicts the Pods. A reboot that takes under five minutes is invisible to the
workloads - except that the Pods on that node are unavailable the whole time.
Drain is the difference between "unavailable for five minutes" and "moved
before the reboot started".

## After the maintenance

```bash
kubectl uncordon node01
kubectl get nodes                       # Ready, no SchedulingDisabled
```

Uncordon does **not** move Pods back. The node is simply eligible again; new
Pods may land there, old ones stay where they went. If you want balance, you
roll the Deployments (`kubectl rollout restart`) or let the descheduler do it.

:::exam-tip
The sequence that scores: `drain --ignore-daemonsets` (add `--force` only if
the task accepts losing a bare Pod, `--delete-emptydir-data` if it complains),
do the work, `uncordon`. Forgetting uncordon is the classic half-mark: the
task passes its own check, and the next task's Pods mysteriously never
schedule on that node.
:::

## Check yourself

1. What is the difference between `cordon` and `drain`?
2. `drain` refuses because of a Pod "not managed by" a controller. What does
   `--force` do to that Pod, and when must you not use it?
3. After `uncordon`, do the evicted Pods return to the node? What would make
   them?
