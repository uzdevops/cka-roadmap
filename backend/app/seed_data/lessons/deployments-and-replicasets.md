## Three objects, one workload

```text
Deployment          you write this - declares rollout strategy and template
    |  creates and owns
    v
ReplicaSet          one per revision - keeps N Pods matching a template
    |  creates and owns
    v
Pod  Pod  Pod       the actual containers
```

The Deployment does not manage Pods. It manages ReplicaSets. Every time you
change the Pod template, it creates a **new** ReplicaSet and scales it up while
scaling the old one down. That is what makes rollback trivial: the old ReplicaSet
is still there at zero replicas.

```bash
kubectl get deploy,rs,pods -l app=web
# deployment.apps/web           3/3     3            3
# replicaset.apps/web-6f4c9d8   3       3            3     <- current
# replicaset.apps/web-5b8a7c2   0       0            0     <- previous revision
# pod/web-6f4c9d8-abc12  1/1  Running
```

## A complete Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  labels:
    app: web
spec:
  replicas: 3
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      app: web             # immutable after creation
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%        # extra Pods allowed above replicas
      maxUnavailable: 25%  # Pods allowed to be missing during the roll
  template:
    metadata:
      labels:
        app: web           # must satisfy the selector above
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          ports:
            - containerPort: 80
          readinessProbe:
            httpGet: {path: /, port: 80}
            periodSeconds: 5
          resources:
            requests: {cpu: 100m, memory: 64Mi}
            limits:   {cpu: 500m, memory: 128Mi}
```

:::warning
`spec.selector` cannot be changed after the Deployment exists. If a task requires
different selector labels, delete and recreate. Attempting `kubectl edit` returns
`field is immutable`.
:::

## Rollouts

```bash
# Trigger a rollout by changing the template
kubectl set image deployment/web nginx=nginx:1.28
kubectl annotate deployment/web kubernetes.io/change-cause="nginx 1.28"

kubectl rollout status deployment/web        # blocks until complete or stuck
kubectl rollout history deployment/web
kubectl rollout history deployment/web --revision=2

kubectl rollout pause deployment/web         # batch several edits
kubectl set resources deployment/web -c=nginx --limits=cpu=1
kubectl rollout resume deployment/web

kubectl rollout undo deployment/web          # back one revision
kubectl rollout undo deployment/web --to-revision=2
kubectl rollout restart deployment/web       # recreate Pods, same template
```

`kubectl rollout restart` is worth remembering separately: it forces new Pods
without changing the image, which is how you pick up a changed ConfigMap or
Secret that is mounted as environment variables.

## RollingUpdate maths

With `replicas: 10`, `maxSurge: 25%`, `maxUnavailable: 25%`:

- maxSurge = 2 (rounded down from 2.5) -> at most 12 Pods exist at once
- maxUnavailable = 2 -> at least 8 Pods must be available throughout

Two special configurations:

```yaml
# Zero downtime, needs spare capacity
rollingUpdate:
  maxSurge: 1
  maxUnavailable: 0

# Fixed capacity, accepts brief reduced capacity
rollingUpdate:
  maxSurge: 0
  maxUnavailable: 1
```

`maxSurge: 0` **and** `maxUnavailable: 0` is rejected - the rollout could never
make progress.

## Recreate strategy

```yaml
strategy:
  type: Recreate
```

Terminates every old Pod before creating any new one. Guarantees downtime. Use it
when two versions genuinely cannot run simultaneously - a schema migration, or a
`ReadWriteOnce` volume that only one Pod can mount.

## Readiness probes are what make a rollout safe

The rollout only counts a new Pod as available when its readiness probe passes.
Without a readiness probe, "available" means "the container process started",
so the Deployment happily replaces every working Pod with a broken one.

:::exam-tip
"The rollout completed but the site is down" almost always means there is no
readiness probe. "The rollout is stuck at 1/3 updated" usually means the new
Pods *have* a readiness probe and are failing it - go straight to
`kubectl describe pod` on a new Pod and read the probe failure events.
:::

## Diagnosing a stuck rollout

```bash
kubectl rollout status deployment/web --timeout=60s
kubectl get rs -l app=web                       # which RS is not scaling
kubectl describe deployment web | tail -20      # conditions
kubectl describe pod <new-pod>                  # the real reason
```

Two Deployment conditions carry the answer:

```text
Type           Status  Reason
Available      False   MinimumReplicasUnavailable
Progressing    False   ProgressDeadlineExceeded
```

`ProgressDeadlineExceeded` means no progress for
`spec.progressDeadlineSeconds` (default 600). The Deployment gives up; it does
**not** roll back automatically.

Common causes: image pull failure, failing readiness probe, insufficient cluster
resources for the surge Pods, or a PVC that cannot be mounted twice.

## Scaling

```bash
kubectl scale deployment web --replicas=5
kubectl scale deployment web --current-replicas=3 --replicas=5   # conditional
```

Scaling does not create a new revision - it edits the existing ReplicaSet.

## ReplicaSets directly

You rarely create one, but you must be able to read one.

```bash
kubectl get rs
kubectl describe rs web-6f4c9d8
```

The ownership chain is visible on the Pod:

```bash
kubectl get pod web-6f4c9d8-abc12 -o jsonpath='{.metadata.ownerReferences}'
# [{"apiVersion":"apps/v1","kind":"ReplicaSet","name":"web-6f4c9d8",...}]
```

Delete a Pod and the ReplicaSet recreates it. Delete the ReplicaSet and the
Deployment recreates it. To actually remove the workload, delete the Deployment.

## Check yourself

1. You change a Deployment's image. How many ReplicaSets exist afterwards, and
   what are their replica counts?
2. What does `ProgressDeadlineExceeded` mean, and does Kubernetes roll back
   automatically?
3. A mounted ConfigMap changed but Pods still use the old values. Which single
   command fixes it?
