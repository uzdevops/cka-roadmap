## The scheduler is a pipeline of plugins

Every Pod the scheduler places goes through the same sequence of
**extension points**, and at each one a set of **plugins** runs:

```
queueSort ─▶ preFilter ─▶ filter ─▶ postFilter ─▶ preScore ─▶ score ─▶ reserve ─▶ permit ─▶ preBind ─▶ bind ─▶ postBind
```

| Point | What runs there | Example built-in plugins |
|---|---|---|
| `queueSort` | order the pending queue | `PrioritySort` (by PriorityClass) |
| `filter` | reject nodes that cannot host the Pod | `NodeResourcesFit`, `NodeName`, `NodeUnschedulable`, `TaintToleration`, `NodeAffinity`, `VolumeBinding` |
| `postFilter` | what to do when no node passes | `DefaultPreemption` |
| `score` | rank the survivors 0-100 | `NodeResourcesBalancedAllocation`, `ImageLocality`, `NodeAffinity`, `PodTopologySpread` |
| `reserve` / `permit` | hold resources, optionally wait | (gang scheduling, extenders) |
| `bind` | write `nodeName` | `DefaultBinder` |

Everything you learned in this phase is one of those plugins: taints are
`TaintToleration` at filter, node affinity is `NodeAffinity` at filter and
score, requests are `NodeResourcesFit` at filter, priority is `PrioritySort`
and `DefaultPreemption`.

## Profiles: a named plugin configuration

A **profile** is a `schedulerName` plus a list of which plugins are enabled
or disabled at each point. One scheduler process can serve several profiles,
and a Pod picks one with `spec.schedulerName`.

```yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
  - schedulerName: default-scheduler

  - schedulerName: no-image-locality
    plugins:
      score:
        disabled:
          - name: ImageLocality

  - schedulerName: bin-packing
    plugins:
      score:
        disabled:
          - name: "*"
        enabled:
          - name: NodeResourcesFit
      # and configure that plugin to prefer full nodes:
    pluginConfig:
      - name: NodeResourcesFit
        args:
          scoringStrategy:
            type: MostAllocated
```

`disabled: [{name: "*"}]` clears the default set at that extension point;
`enabled` then adds back what you want, in order. `pluginConfig` passes
arguments to a plugin.

## Wiring the file in

The configuration is passed to the scheduler with `--config`. On a kubeadm
cluster the default scheduler has none - so you add one:

```bash
# 1. write the config to the node, e.g. /etc/kubernetes/scheduler-config.yaml
# 2. edit the static Pod manifest
vim /etc/kubernetes/manifests/kube-scheduler.yaml
```

```yaml
    command:
      - kube-scheduler
      - --config=/etc/kubernetes/scheduler-config.yaml
      # keep the --authentication-kubeconfig / --authorization-kubeconfig / --kubeconfig flags
      #   OR move the kubeconfig into the file's clientConnection.kubeconfig
    volumeMounts:
      - mountPath: /etc/kubernetes/scheduler-config.yaml
        name: scheduler-config
        readOnly: true
volumes:
  - hostPath:
      path: /etc/kubernetes/scheduler-config.yaml
      type: FileOrCreate
    name: scheduler-config
```

The kubelet restarts the scheduler; `kubectl logs kube-scheduler-controlplane
-n kube-system` shows the profiles it loaded.

:::exam-tip
Two mistakes cost the most time here. Forgetting to **mount** the config file
into the static Pod - the scheduler crash-loops with "no such file". And a
`profiles` list that drops `default-scheduler` - then every ordinary Pod in the
cluster stays Pending, because nothing serves that name any more. Always keep
the default profile in the list.
:::

## Why profiles rather than a second scheduler

| | second scheduler process | second profile |
|---|---|---|
| RBAC, ServiceAccount, leader election | yes, all of it | none |
| can use different code | yes | no - same binary |
| risk of two schedulers fighting over a Pod | possible if names collide | no |
| good for | vendor/custom schedulers | turning built-in plugins on/off per workload |

Most "I need different placement" needs are a profile.

## Check yourself

1. Name the extension point and plugin that implements taints and
   tolerations.
2. What does `disabled: [{name: "*"}]` under `score` do, and what must follow
   it?
3. You add a config file to the kube-scheduler static Pod and every new Pod in
   the cluster becomes Pending. What did you most likely leave out?
