## Two numbers per container

```yaml
spec:
  containers:
    - name: app
      image: myapp:1.0
      resources:
        requests:
          cpu: 250m
          memory: 128Mi
        limits:
          cpu: "1"
          memory: 256Mi
```

- **requests** - what the Pod is *guaranteed*. The scheduler only places a
  Pod on a node with at least this much free (unrequested) capacity. Used for
  scheduling, not enforced at runtime.
- **limits** - what the container may *never exceed*. Enforced by the kubelet
  and the kernel.

Units: CPU in cores or millicores (`1` = `1000m`); memory in bytes with
`Ki/Mi/Gi` (powers of 1024) or `K/M/G` (powers of 1000). `Mi` is the one you
want.

## What happens at the limit - CPU vs memory are different

| Resource | Over the limit means |
|---|---|
| **CPU** | the container is **throttled** - it gets less time, it slows down, it does not die |
| **Memory** | the container is **OOMKilled** - the kernel kills the process, the kubelet restarts it, `RESTARTS` climbs |

```bash
kubectl describe pod elephant | grep -A5 "Last State"
#   Last State:     Terminated
#     Reason:       OOMKilled
#     Exit Code:    137
```

Exit code 137 = 128 + 9 (SIGKILL) is the fingerprint. The fix is a higher
memory limit (or a less hungry application) - and because `resources` is
immutable on a running Pod, it is `kubectl replace --force` after editing, or
an edit of the Deployment's template.

## What happens with no requests or limits

Without **requests**, the scheduler assumes the Pod needs nothing and packs
it anywhere - fine until a node is oversubscribed. Without **limits**, a
container may use everything its node has and starve its neighbours. The
quality-of-service class the Pod gets tells the kubelet whom to evict first
under pressure:

| Requests / limits | QoS class | Evicted |
|---|---|---|
| limits == requests for every container | `Guaranteed` | last |
| some requests or limits set | `Burstable` | middle |
| nothing set | `BestEffort` | first |

```bash
kubectl get pod app -o jsonpath='{.status.qosClass}'
```

## Defaults for a namespace: LimitRange

A **LimitRange** fills in requests and limits for containers that do not set
them, and can cap what anyone may ask for:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: cpu-defaults
  namespace: dev
spec:
  limits:
    - type: Container
      default:            # limit applied when none is set
        cpu: 500m
        memory: 256Mi
      defaultRequest:     # request applied when none is set
        cpu: 100m
        memory: 128Mi
      max:
        cpu: "2"
      min:
        cpu: 50m
```

It applies to Pods **created after** it exists; existing Pods are untouched.

## A budget for a namespace: ResourceQuota

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dev-quota
  namespace: dev
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "20"
```

```bash
kubectl create quota dev-quota --hard=pods=20,requests.cpu=4 -n dev
kubectl describe quota -n dev
```

:::warning
Once a namespace has a quota on `requests.cpu`, every Pod in it **must** set a
CPU request - or the API server rejects it with `must specify requests.cpu`.
The usual pairing is a ResourceQuota plus a LimitRange that supplies defaults,
so plain Pods keep working.
:::

## Reading and setting them fast

```bash
kubectl get pod app -o jsonpath='{.spec.containers[0].resources}'
kubectl top pod app                                   # actual usage (needs metrics-server)
kubectl set resources deployment app --requests=cpu=200m,memory=256Mi --limits=cpu=1,memory=512Mi
kubectl describe node node01 | grep -A8 "Allocated resources"   # how full the node is, by requests
```

:::exam-tip
"Pod stuck Pending, event says `Insufficient memory`" is a requests problem,
not a limits one: no node has that much *unrequested* memory left. Either
lower the request or free a node. "Pod restarting, OOMKilled" is a limits
problem. Two different numbers, two different fixes.
:::

## Check yourself

1. A container exceeds its CPU limit; a second exceeds its memory limit. What
   happens to each?
2. What does a Pod with no `resources` at all get as its QoS class, and what
   does that mean when the node runs out of memory?
3. You add a `requests.cpu` quota to a namespace and a plain `kubectl run
   nginx --image=nginx` starts failing. Why, and what object fixes it?
