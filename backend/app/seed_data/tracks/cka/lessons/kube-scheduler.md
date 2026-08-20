## One decision, made many times a second

The scheduler answers exactly one question: **which node should this Pod run
on?** It does not start the Pod - the kubelet on the chosen node does that.
The scheduler only writes the answer (`spec.nodeName`) onto the Pod object,
and the kubelet on that node sees a Pod assigned to it and takes over.

```
new Pod (nodeName empty) ──▶ scheduler ──▶ Pod with nodeName=node02 ──▶ kubelet on node02
```

Two phases for every Pod:

1. **Filtering** - throw away nodes that cannot run it: not enough free CPU or
   memory for the Pod's *requests*, a taint the Pod does not tolerate, a
   `nodeSelector` or node affinity that does not match, a required port
   already in use, a volume that cannot attach there.
2. **Scoring** - rank the survivors: spread replicas across nodes, prefer
   nodes that already have the image, honour preferred affinities, balance
   resource usage. Highest score wins; ties are broken randomly.

Everything in the scheduling phase of this track - labels, taints, affinity,
resource requests, priority - is a way of changing the result of those two
steps.

## How it runs

```bash
cat /etc/kubernetes/manifests/kube-scheduler.yaml
kubectl get pods -n kube-system | grep scheduler
```

```yaml
- kube-scheduler
- --kubeconfig=/etc/kubernetes/scheduler.conf
- --authentication-kubeconfig=/etc/kubernetes/scheduler.conf
- --authorization-kubeconfig=/etc/kubernetes/scheduler.conf
- --bind-address=127.0.0.1
- --leader-elect=true
```

Short list of flags, because most scheduler behaviour is configured through a
**KubeSchedulerConfiguration** file (`--config`) rather than flags - that is
how profiles and plugins are tuned in the scheduler-profiles lesson.

## When there is no scheduler

If the scheduler is down, new Pods simply stay **Pending** with no events
about nodes at all - `kubectl describe pod` shows nothing after the creation
line, because nothing has looked at it. You can still place a Pod by hand by
setting `nodeName` yourself (manual scheduling lesson); the kubelet does not
care who wrote the field.

```bash
kubectl get pods -n kube-system | grep scheduler        # is it even Running?
kubectl logs -n kube-system kube-scheduler-controlplane
kubectl get events --sort-by=.lastTimestamp | tail
```

:::exam-tip
Pending Pods come in two flavours. **No events** = the scheduler never saw it:
scheduler down, or the Pod names a `schedulerName` that does not exist.
**FailedScheduling event** = the scheduler saw it and found no node: read the
message - it literally lists why each node was rejected ("1 node(s) had
untolerated taint", "Insufficient cpu").
:::

## Reading a scheduling decision

```bash
kubectl describe pod web | grep -A3 Events
#  Normal  Scheduled  12s  default-scheduler  Successfully assigned default/web to node02
```

The `default-scheduler` in that line is the scheduler's **name**. A Pod may ask
for a different one with `spec.schedulerName`, which is how you run a second,
custom scheduler side by side (multiple-schedulers lesson) - and how you get
a Pod stuck Pending forever by naming a scheduler that is not running.

```bash
kubectl get pods -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName,SCHED:.spec.schedulerName
```

## What it does not do

- It does not move running Pods. A Pod is scheduled once; if the node later
  becomes a bad fit, nothing happens unless something (the descheduler, or
  you) deletes the Pod.
- It does not enforce limits. Filtering uses *requests*; limits are the
  kubelet's and the kernel's business.
- It does not create Pods. That is the controller manager.

## Check yourself

1. What exactly does the scheduler write, and which component reacts to it?
2. A Pod is Pending with no events at all. Name two causes.
3. Why does filtering use resource requests rather than limits?
