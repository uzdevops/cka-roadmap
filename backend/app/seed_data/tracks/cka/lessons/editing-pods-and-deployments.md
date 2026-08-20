## Pods are mostly immutable

Once a Pod exists, you may change only a short list of its fields:

- `spec.containers[*].image`
- `spec.initContainers[*].image`
- `spec.activeDeadlineSeconds`
- `spec.tolerations` (additions only)
- `spec.terminationGracePeriodSeconds` (only to shorten, in some cases)
- labels and annotations in `metadata`

Everything else - resources, environment, volumes, command, security context,
nodeName, a new container - is **immutable**. Try it and the API server says
so:

```bash
kubectl edit pod web
# error: pods "web" is invalid: spec: Forbidden: pod updates may not change fields other than
#   `spec.containers[*].image`, `spec.initContainers[*].image`, ...
```

## The two honest ways to change an immutable field

**1. Delete and recreate from a file you control.**

```bash
kubectl get pod web -o yaml > web.yaml
# edit web.yaml
kubectl replace --force -f web.yaml
# or: kubectl delete pod web $now ; kubectl apply -f web.yaml
```

**2. Let `kubectl edit` save your rejected edit, then force it.**

When `kubectl edit` is refused, it keeps your edited copy and prints the path:

```
A copy of your changes has been stored to "/tmp/kubectl-edit-1a2b3c.yaml"
error: At least one of apiVersion, kind and name was changed
```

```bash
kubectl replace --force -f /tmp/kubectl-edit-1a2b3c.yaml
```

Same result, and you did not have to redo the edit. This is the exam move.

:::warning
Either way the Pod is **deleted**. Its IP changes, its emptyDir volumes are
wiped, and if it was not created by a controller nothing recreates it until
you do. For a lone Pod that is the cost of the change. Check the task did not
say "without deleting the Pod" - if it did, the field you are about to change
is probably one of the mutable ones.
:::

## Deployments are different

A Deployment's Pod template is fully editable, because the Deployment does
not change running Pods - it creates a new ReplicaSet with the new template
and rolls over to it. So:

```bash
kubectl edit deployment web          # change resources, env, volumes, anything
kubectl set image deployment/web nginx=nginx:1.27
kubectl set resources deployment/web --limits=memory=512Mi
kubectl set env deployment/web MODE=prod
```

... each triggers a rollout: new Pods with the new spec come up, old Pods go
away, zero hand-deleting. `kubectl rollout status deployment/web` watches it.

The same holds for anything with a Pod template: ReplicaSet, DaemonSet,
StatefulSet, Job (template immutable once created), CronJob.

:::exam-tip
If a task asks you to change the resources/env/volume of "the Pods of
Deployment X", edit the Deployment - never the Pods. Pods edited by hand are
overwritten the moment the Deployment reconciles, and you lose the marks
twice: once for the rejected edit, once for the Pod that came back unchanged.
:::

## Quick decision table

| You want to change | On a bare Pod | On a Deployment |
|---|---|---|
| image | `kubectl set image pod/...` | `kubectl set image deployment/...` |
| resources, env, volumes, command | delete + recreate | `kubectl edit deployment` / `set resources` / `set env` |
| labels | `kubectl label pod ...` | `kubectl edit` (template labels must still match the selector) |
| add a container | delete + recreate | `kubectl edit deployment` |

## Check yourself

1. Name three Pod fields you can change in place and three you cannot.
2. `kubectl edit pod` refuses your change. What is the fastest correct next
   command?
3. Why can a Deployment's resources be changed "live" when a Pod's cannot?
