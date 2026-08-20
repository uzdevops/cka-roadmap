## When the default scheduler is not enough

The default scheduler is general-purpose. Occasionally a workload needs
different placement logic - bin-packing for batch jobs, a custom algorithm, a
scheduler from a vendor. Kubernetes lets you run **more than one scheduler** at
the same time and lets each Pod say which one should place it.

```yaml
spec:
  schedulerName: my-scheduler       # default is "default-scheduler"
  containers: [...]
```

A Pod that names a scheduler is ignored by all the others. If the named one
is not running, the Pod stays **Pending with no events** - which is also a
classic troubleshooting task: the fix is either to start that scheduler or to
remove the `schedulerName` so the default one picks the Pod up.

## Deploying a second scheduler

The second scheduler is the same binary with a different name, running as a
Pod (or a static Pod, or a Deployment). Its name comes from a
**KubeSchedulerConfiguration**:

```yaml
# my-scheduler-config.yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
  - schedulerName: my-scheduler
leaderElection:
  leaderElect: false            # a single instance does not need a lock
```

```bash
kubectl create configmap my-scheduler-config -n kube-system --from-file=my-scheduler-config.yaml
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-scheduler
  namespace: kube-system
spec:
  serviceAccountName: my-scheduler          # needs RBAC to read Pods/Nodes and write bindings
  containers:
    - name: kube-scheduler
      image: registry.k8s.io/kube-scheduler:v1.30.0   # same version as the cluster
      command:
        - kube-scheduler
        - --config=/etc/kubernetes/my-scheduler/my-scheduler-config.yaml
      volumeMounts:
        - name: config
          mountPath: /etc/kubernetes/my-scheduler
  volumes:
    - name: config
      configMap:
        name: my-scheduler-config
```

The RBAC half - a ServiceAccount bound to the `system:kube-scheduler` and
`system:volume-scheduler` ClusterRoles, plus a Role for leases - is in the
documentation under "Configure Multiple Schedulers"; the exam lets you copy
it. The image version must match the control plane:

```bash
kubectl get pod kube-scheduler-controlplane -n kube-system -o jsonpath='{.spec.containers[0].image}'
```

## Confirming which scheduler placed a Pod

```bash
kubectl get events -o wide | grep Scheduled
# ...  Scheduled  pod/nginx  my-scheduler  Successfully assigned default/nginx to node02
kubectl describe pod nginx | grep -A1 Events
```

The `SOURCE` column of the event names the scheduler. That is the proof a
task asks for.

```bash
kubectl logs my-scheduler -n kube-system        # the scheduler's own view
```

:::exam-tip
The three things that go wrong: the Pod's `schedulerName` and the profile's
`schedulerName` do not match exactly; `leaderElect` left `true` on a single
instance with no lease permissions, so it waits forever; the image tag does
not match the cluster version. Each shows up in `kubectl logs` of the
scheduler Pod within seconds.
:::

## Several profiles in one scheduler

You do not always need a second process. One scheduler binary can serve
several **profiles**, each with its own name and plugin set:

```yaml
profiles:
  - schedulerName: default-scheduler
  - schedulerName: bin-packing
    plugins:
      score:
        disabled:
          - name: NodeResourcesBalancedAllocation
        enabled:
          - name: NodeResourcesMostAllocated
```

Pods choose a profile by `schedulerName` exactly as if it were a separate
scheduler. Lighter, no extra RBAC, and the subject of the next lesson.

## Check yourself

1. A Pod names `schedulerName: foo` and `foo` is not running. What do you see,
   and what are the two fixes?
2. Which event field proves which scheduler placed a Pod?
3. When would you prefer a second profile over a second scheduler process?
