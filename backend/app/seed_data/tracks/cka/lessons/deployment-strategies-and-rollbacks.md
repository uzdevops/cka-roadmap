## What a rollout is

Change a Deployment's Pod template - the image, an env var, a resource
request - and the Deployment controller does not touch the running Pods. It
creates a **new ReplicaSet** with the new template and shifts replicas from
the old ReplicaSet to the new one. That shift is a rollout, and how it
happens is the **strategy**.

```bash
kubectl get rs -l app=web
# NAME             DESIRED   CURRENT   READY   AGE
# web-5d4b9c8f7    0         0         0       2d     <- old, scaled to zero
# web-7c6f9b4d2    3         3         3       1m     <- current
```

Every rollout leaves the old ReplicaSet behind at zero replicas (up to
`revisionHistoryLimit`, default 10). Those are your rollback targets.

## The two strategies

```yaml
spec:
  strategy:
    type: RollingUpdate            # default
    rollingUpdate:
      maxSurge: 25%                # extra Pods allowed above desired during the rollout
      maxUnavailable: 25%          # Pods allowed below desired
```

| Strategy | Behaviour | Use when |
|---|---|---|
| **RollingUpdate** | new Pods come up while old ones go down, within `maxSurge`/`maxUnavailable` | almost always - zero downtime |
| **Recreate** | all old Pods are killed, then new ones are created | the app cannot run two versions at once (schema locks, single-writer) |

`maxSurge: 1, maxUnavailable: 0` is the conservative rolling setting: never
below capacity, at most one extra Pod. `maxUnavailable: 100%` with
`maxSurge: 0` is effectively Recreate.

## Driving a rollout

```bash
kubectl set image deployment/web nginx=nginx:1.27          # the usual trigger
kubectl edit deployment web                                # any template change triggers one
kubectl apply -f web.yaml

kubectl rollout status deployment/web                      # blocks until done (or stuck)
kubectl rollout history deployment/web
# REVISION  CHANGE-CAUSE
# 1         <none>
# 2         <none>
kubectl rollout history deployment/web --revision=2        # the template of that revision
kubectl rollout pause deployment/web                       # make several changes, then
kubectl rollout resume deployment/web
kubectl rollout restart deployment/web                     # new ReplicaSet, same template: a restart
```

`CHANGE-CAUSE` is filled from the annotation
`kubernetes.io/change-cause` - set it yourself with
`kubectl annotate deployment web kubernetes.io/change-cause="image 1.27"` if a
task wants the history to be readable.

## Rolling back

```bash
kubectl rollout undo deployment/web                        # to the previous revision
kubectl rollout undo deployment/web --to-revision=1
kubectl rollout status deployment/web
```

Undo is itself a rollout: the old ReplicaSet is scaled up and the current one
down, under the same strategy. The history gets a new revision number (the
rolled-back-to template becomes the newest revision), which confuses people
the first time.

:::exam-tip
A rollout that never finishes - `rollout status` hangs at "1 of 3 updated
replicas are available" - means the new Pods are not becoming Ready: bad
image tag (ImagePullBackOff), crashing container, failing readiness probe. The
old Pods are still serving, so the application is not down. Read `kubectl get
pods`, fix the template or `rollout undo`, and it completes.
:::

## Reading a Deployment's state

```bash
kubectl describe deployment web | grep -E "StrategyType|RollingUpdateStrategy|Replicas:|Conditions" -A1
kubectl get deployment web -o jsonpath='{.spec.strategy}'
kubectl get deployment web
# NAME   READY   UP-TO-DATE   AVAILABLE   AGE
# web    3/3     3            3           5d
```

- **READY** - Pods ready / desired.
- **UP-TO-DATE** - Pods running the *current* template. During a rollout this
  climbs from 0 to desired.
- **AVAILABLE** - Pods that have been Ready for `minReadySeconds`.

A Deployment showing `3/3` READY but `1` UP-TO-DATE is mid-rollout or stuck.

:::tip
`kubectl rollout` works on DaemonSets and StatefulSets too (`rollout status
ds/kube-proxy -n kube-system`), with their own strategy fields.
:::

## Check yourself

1. What object does the Deployment controller create when you change the
   image, and what happens to the old one?
2. Explain `maxSurge: 1, maxUnavailable: 0` in one sentence, and name the
   case where you would choose `Recreate` instead.
3. `rollout status` has been stuck for five minutes. Is the application down?
   What do you look at, and what is the quick way out?
