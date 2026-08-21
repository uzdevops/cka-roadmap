## What "stateful" actually needs

A stateless replica can be killed and replaced anywhere by anything; a
database replica cannot. It needs three things a Deployment does not give:

1. **a stable identity** - `db-0` is always the primary, `db-1` always the
   first replica, and they find each other by name;
2. **its own storage that follows it** - `db-1`'s data comes back to `db-1`,
   not to whichever Pod happens to be created next;
3. **ordered operations** - start `db-0` before `db-1`, stop `db-2` before
   `db-1`, so replication and quorum make sense.

The **StatefulSet** provides all three; this lesson is how they fit with the
storage objects of this week.

## Stable names: the headless Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: db
spec:
  clusterIP: None              # headless: no VIP, DNS returns the Pod IPs
  selector:
    app: db
  ports:
    - port: 5432
```

With `serviceName: db` on the StatefulSet, each Pod gets a DNS name:

```
db-0.db.default.svc.cluster.local
db-1.db.default.svc.cluster.local
db-2.db.default.svc.cluster.local
```

A replica can be configured with "primary is `db-0.db`" and that stays true
across restarts and reschedules. An ordinary Service (`db-rw`, selecting only
the primary via a label the operator maintains, or `db-ro` selecting all)
can sit alongside for clients who just want *a* connection.

## Storage that follows: volumeClaimTemplates

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: db
spec:
  serviceName: db
  replicas: 3
  podManagementPolicy: OrderedReady          # or Parallel
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0                           # >0: only ordinals >= partition are updated (canary)
  selector:
    matchLabels: {app: db}
  template:
    metadata:
      labels: {app: db}
    spec:
      containers:
        - name: postgres
          image: postgres:16
          ports: [{containerPort: 5432}]
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: [ReadWriteOnce]
        storageClassName: fast
        resources: {requests: {storage: 20Gi}}
```

Claims `data-db-0..2` are created from the template, one per ordinal; each
is RWO and private to its Pod; a `WaitForFirstConsumer` class places each
disk where its Pod is scheduled. The binding is by **name**: the Pod named
`db-1` always mounts the claim named `data-db-1`.

```bash
kubectl get sts db
kubectl get pods -l app=db -o wide          # db-0, db-1, db-2 - no random suffix
kubectl get pvc -l app=db
kubectl delete pod db-1                     # comes back as db-1, same PVC, same data
kubectl scale sts db --replicas=5           # db-3 then db-4, in order, each with a new claim
kubectl scale sts db --replicas=3           # db-4 then db-3 are removed; data-db-3/4 CLAIMS STAY
```

## Ordering

`OrderedReady` (default): Pods are created `0, 1, 2`, each waiting for the
previous to be Running and Ready; deleted in reverse. `Parallel` drops that
for workloads that do not care. Updates roll from the highest ordinal down;
`partition: 2` updates only `db-2`, a one-Pod canary you then lower to 0.

## What is not automatic

A StatefulSet gives you names, disks and order. It does **not** know
PostgreSQL: it will not promote a replica, rebuild one from the primary, or
run a backup. That knowledge lives in an **operator** (CloudNativePG, Zalando,
Crunchy for PostgreSQL; Strimzi for Kafka), which uses StatefulSets or its
own Pod management underneath. For the exam, the StatefulSet is the object;
in production, you almost always want the operator on top.

:::exam-tip
The exam's StatefulSet tasks are about the mechanics: create one with N
replicas and a volumeClaimTemplate, confirm the Pod names and the PVCs,
scale it, maybe set a headless Service. Check: `serviceName` matches a
headless Service that exists; `volumeClaimTemplates` is under `spec`, not
under `template`; the `volumeMounts` name equals the template's
`metadata.name`.
:::

## Check yourself

1. Name the three things a stateful workload needs that a Deployment does
   not provide.
2. After `kubectl delete pod db-1`, which PVC does the replacement mount, and
   why?
3. What is left behind when you scale a StatefulSet from 5 to 3, and why is
   that the right default?
