## Changing a Pod's resources without killing it

For most of Kubernetes' life, `resources` was immutable on a running Pod: to
give a container more memory you deleted the Pod and created a bigger one,
and for a Deployment that meant a rollout. **In-place Pod vertical scaling**
removes that restriction: the kubelet can change a running container's CPU
and memory limits and requests, and - for CPU at least - without restarting
the container.

Status: alpha in 1.27 behind the `InPlacePodVerticalScaling` feature gate,
**beta and enabled by default from 1.33**. On an exam cluster check:

```bash
kubectl version --short
kubectl get --raw /metrics | grep -c InPlacePodVerticalScaling    # or read the API server flags
```

## resizePolicy

Each container says what should happen when each resource changes:

```yaml
spec:
  containers:
    - name: app
      image: myapp:1.0
      resizePolicy:
        - resourceName: cpu
          restartPolicy: NotRequired     # change it live
        - resourceName: memory
          restartPolicy: RestartContainer # some runtimes/apps need a restart to see a new memory limit
      resources:
        requests: {cpu: 250m, memory: 256Mi}
        limits:   {cpu: "1",  memory: 512Mi}
```

`NotRequired` is the default for both. Memory *decreases* often need a
restart in practice (the kernel will not shrink a cgroup below what is in
use); CPU changes are live on every runtime.

## Doing a resize

The resize goes through a subresource, not a plain edit:

```bash
kubectl patch pod app --subresource resize --patch \
  '{"spec":{"containers":[{"name":"app","resources":{"requests":{"cpu":"500m"},"limits":{"cpu":"2"}}}]}}'

kubectl get pod app -o jsonpath='{.spec.containers[0].resources}'     # the desired values
kubectl get pod app -o jsonpath='{.status.containerStatuses[0].resources}'   # what is actually applied
```

Older kubectl versions did it with a plain `kubectl edit pod` when the gate
was on; newer ones require `--subresource resize`, which is also what stops
an accidental edit from triggering a resize.

The Pod's **status** tells you how it went:

| `status.resize` / conditions | Meaning |
|---|---|
| `Proposed` → `InProgress` → (gone) | accepted and applied |
| `Deferred` | the node cannot fit it right now; the kubelet will retry when resources free up |
| `Infeasible` | the node can **never** fit it (asks for more than the node has) - the Pod stays as it was |

```bash
kubectl get pod app -o jsonpath='{.status.resize}'
kubectl describe pod app | grep -iA2 resize
```

## Where it fits

- The **VPA**, in its newer `InPlaceOrRecreate` update mode, uses this to
  apply recommendations without restarting Pods when it can.
- A Deployment's template change still triggers a rollout - in-place resize
  is a **Pod-level** operation. For a Deployment you resize its Pods one by
  one (or let the VPA do it), or you accept the rollout.
- QoS class does not change on resize: a `Guaranteed` Pod must stay
  Guaranteed (requests equal limits) or the resize is rejected.

:::exam-tip
In the 2025 curriculum this is a "know that it exists and what the fields
are" topic. If a task asks you to change a running Pod's CPU without
recreating it, the shape is: check `resizePolicy`, patch the `resize`
subresource, confirm in `status.containerStatuses[].resources`. If the
cluster does not have the feature enabled, the honest answer is still delete
and recreate.
:::

## Check yourself

1. What does `resizePolicy.restartPolicy: NotRequired` promise, and for
   which resource is it most reliably true?
2. A resize shows `Infeasible`. What happened to the Pod's resources?
3. Why does changing a Deployment's template still roll the Pods even on a
   cluster with in-place resize?
