## Three places a claim shows up

A PersistentVolumeClaim is consumed the same way in a Pod, a Deployment and
a StatefulSet - a `persistentVolumeClaim` volume plus a `volumeMounts` entry
- but what *owns* the claim differs, and that decides how many replicas can
use it and what happens when they die.

## In a Pod

```yaml
spec:
  containers:
    - name: app
      image: myapp
      volumeMounts:
        - name: data
          mountPath: /var/lib/app
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: app-data
```

The claim exists before the Pod; delete and recreate the Pod and the data is
there. This is the shape for a one-off, a Job, or a single replica you manage
yourself.

## In a Deployment

```yaml
kind: Deployment
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: app
          volumeMounts: [{name: data, mountPath: /var/lib/app}]
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: app-data            # ONE claim, shared by every replica
```

Every replica mounts the **same** claim. With an RWO volume that means every
replica must land on the same node - or the second replica sits
`ContainerCreating` with `Multi-Attach error`. And during a rolling update
the new Pod may not be able to attach until the old one releases the volume,
so `strategy: Recreate` is often the honest setting. Deployments with PVCs
are for **one replica**, or for RWX storage (NFS) where sharing is the point.

:::warning
`replicas: 3` with a single RWO claim is the classic mistake: one Pod Running,
two stuck, events full of `Multi-Attach error for volume`. The fix is a
StatefulSet, or RWX storage, or honesty about wanting one replica.
:::

## In a StatefulSet: a claim per replica

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: db
spec:
  serviceName: db                      # a headless Service for stable per-Pod DNS
  replicas: 3
  selector:
    matchLabels: {app: db}
  template:
    metadata:
      labels: {app: db}
    spec:
      containers:
        - name: postgres
          image: postgres:16
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:                # a PVC stamped out PER REPLICA
    - metadata:
        name: data
      spec:
        accessModes: [ReadWriteOnce]
        storageClassName: fast
        resources:
          requests:
            storage: 10Gi
```

```bash
kubectl get pvc
# data-db-0   Bound   pvc-3f1...   10Gi   RWO   fast
# data-db-1   Bound   pvc-8a2...   10Gi   RWO   fast
# data-db-2   Bound   pvc-c91...   10Gi   RWO   fast
```

`volumeClaimTemplates` creates `data-db-0`, `data-db-1`, `data-db-2` - one
claim per ordinal. When `db-1` is rescheduled it gets `data-db-1` back,
wherever it lands. Scaling down does **not** delete the claims (data is
kept for a scale-up); deleting the StatefulSet does not delete them either
unless `persistentVolumeClaimRetentionPolicy` says so. That is the shape for
databases, brokers, anything where each replica has its own identity and its
own disk.

## Choosing

| Workload | Claim ownership |
|---|---|
| one replica, or a Job | a hand-made PVC in a Pod / Deployment |
| N replicas sharing one filesystem (uploads, a shared cache) | one RWX PVC in a Deployment |
| N replicas each with their own disk (databases) | StatefulSet with `volumeClaimTemplates` |

:::exam-tip
If a task wants "each replica to have its own persistent volume", the word
is StatefulSet and the field is `volumeClaimTemplates`. If it wants "the
application to keep its data across restarts" with one replica, a PVC and a
Deployment (or Pod) is enough - do not over-engineer.
:::

## Reading the wiring

```bash
kubectl get pod db-0 -o jsonpath='{.spec.volumes[*].persistentVolumeClaim.claimName}'
kubectl describe pod db-0 | grep -A3 "Volumes:"
kubectl get pvc -l app=db
kubectl get events --field-selector involvedObject.name=db-1 | grep -i attach
```

## Check yourself

1. A Deployment with 3 replicas shares one RWO claim. What happens, and what
   are the two ways out?
2. What does `volumeClaimTemplates` create, and what happens to those claims
   when the StatefulSet scales down?
3. Which object owns the claim in each of the three shapes above?
