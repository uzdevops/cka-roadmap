## Stop creating PVs by hand

Static provisioning - an admin writes a PV, a user writes a PVC, they bind -
needs someone to have made the disk first. A **StorageClass** inverts it:
the class names a provisioner (a CSI driver) and its parameters; a claim
names the class; when the claim appears, the provisioner **creates** the
disk and the PV to match. Nobody writes PVs.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"    # claims with no class get this one
provisioner: ebs.csi.aws.com          # pd.csi.storage.gke.io, disk.csi.azure.com, rbd.csi.ceph.com, ...
parameters:                            # provisioner-specific
  type: gp3
  iops: "3000"
reclaimPolicy: Delete                  # Delete (default) | Retain
volumeBindingMode: WaitForFirstConsumer   # Immediate (default) | WaitForFirstConsumer
allowVolumeExpansion: true
```

```bash
kubectl get sc
# NAME             PROVISIONER          RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
# fast (default)   ebs.csi.aws.com      Delete          WaitForFirstConsumer   true                   30d
# standard         kubernetes.io/no-provisioner   Retain   WaitForFirstConsumer   false              30d
```

The claim just names it:

```yaml
kind: PersistentVolumeClaim
spec:
  storageClassName: fast
  accessModes: [ReadWriteOnce]
  resources: {requests: {storage: 20Gi}}
```

```bash
kubectl apply -f pvc.yaml
kubectl get pvc          # Pending (WaitForFirstConsumer) or Bound (Immediate) to pvc-<uuid>
kubectl get pv           # a PV named pvc-<uuid> appeared, created by the driver, reclaim Delete
```

## volumeBindingMode

| Mode | The PV is created |
|---|---|
| `Immediate` | as soon as the claim exists - in whatever zone/node the provisioner picks |
| `WaitForFirstConsumer` | only when a **Pod** using the claim is scheduled - so the disk is created where the Pod is |

For zonal cloud disks and `local` volumes `WaitForFirstConsumer` is the only
sane choice: otherwise the disk lands in zone A and the Pod is scheduled in
zone B and can never attach. It has one visible side effect that confuses
everyone the first time: **a PVC with no Pod sits Pending** with the event
`waiting for first consumer to be created before binding`. That is not an
error. Create the Pod.

:::exam-tip
"PVC is Pending, StorageClass is WaitForFirstConsumer" → it is waiting for a
Pod; not a fault. "PVC is Pending, StorageClass is Immediate" → the
provisioner is missing or failing: `kubectl describe pvc` names the driver,
`kubectl get pods -n kube-system | grep csi` shows whether it is running.
:::

## The default class

A claim with **no** `storageClassName` gets the default StorageClass (the one
with the `is-default-class` annotation), via the `DefaultStorageClass`
admission plugin. A claim with `storageClassName: ""` (empty string, set
explicitly) opts **out** and will only bind to a PV with no class - the
static-provisioning path.

```bash
kubectl get sc | grep default
kubectl patch storageclass fast -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
kubectl patch storageclass old -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
```

Two defaults at once is an error for new claims; zero means claims without a
class stay Pending forever.

## No provisioner: a class for local disks

```yaml
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

A class whose provisioner creates nothing, used to group hand-made `local` PVs
and to delay binding until the Pod is placed (so the scheduler can pick the
node that has the disk). You will meet exactly this in the storage lab: create
the PVC, watch it stay Pending, create the Pod, watch it bind.

## Reclaim policy and expansion, from the class

A dynamically created PV inherits `reclaimPolicy` from the class - `Delete`
by default, so **deleting the claim deletes the disk**. Set `Retain` on
classes for data you could not recreate. `allowVolumeExpansion: true` is what
lets `kubectl patch pvc` grow a volume later.

## Check yourself

1. What creates the PersistentVolume when a claim names a StorageClass, and
   what is the PV's name?
2. A PVC is Pending with "waiting for first consumer". Is something broken?
3. What is the difference between a claim with no `storageClassName` and one
   with `storageClassName: ""`?
