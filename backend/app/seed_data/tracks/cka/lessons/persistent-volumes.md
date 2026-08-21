## Storage as a cluster resource

Putting `nfs:` or `csi:` details into every Pod spec means every developer
has to know where the storage is, and changing it means editing every Pod.
Kubernetes separates the two sides:

- an administrator creates **PersistentVolumes** - pieces of storage with a
  size, access modes and a backend, as cluster-scoped objects;
- a user creates a **PersistentVolumeClaim** - "I need 5Gi, read-write" -
  and Kubernetes binds it to a suitable PV;
- the Pod references the claim.

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-vol1
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual            # optional; a label the claim must match
  hostPath:                           # the backend - any volume type: nfs, csi, local, ...
    path: /tmp/data
    type: DirectoryOrCreate
```

```bash
kubectl apply -f pv.yaml
kubectl get pv
# NAME      CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM   STORAGECLASS   AGE
# pv-vol1   1Gi        RWO            Retain           Available           manual         5s
```

PVs are **not namespaced** - they are a cluster pool; claims (namespaced)
draw from it.

## Access modes

| Mode | Short | Means |
|---|---|---|
| `ReadWriteOnce` | RWO | mounted read-write by **one node** (any number of Pods on that node) |
| `ReadOnlyMany` | ROX | mounted read-only by many nodes |
| `ReadWriteMany` | RWX | mounted read-write by many nodes - needs a shared filesystem (NFS, CephFS), not a block disk |
| `ReadWriteOncePod` | RWOP | one **Pod**, strictly |

A block disk (EBS, a local SSD) is RWO; a network filesystem can be RWX. A
claim asking for RWX will never bind to an RWO-only PV - the first thing to
check when a claim sits Pending.

## Reclaim policy

What happens to the PV when its claim is deleted:

| Policy | Then |
|---|---|
| `Retain` | the PV becomes `Released`; data is kept; an admin must clean it up (delete the PV, wipe or keep the backend) before it can be reused |
| `Delete` | the PV **and the backing storage** are deleted - the default for dynamically provisioned volumes |
| `Recycle` | deprecated; `rm -rf` the contents and make it Available again |

`Retain` is the safe default for anything you created by hand. The
`Released` state catches people out: the PV is not Available, a new claim
will not bind to it, and `kubectl get pv` shows it with the old CLAIM. To
reuse it, delete the PV and recreate it (the data on a `hostPath` or NFS
backend survives that).

## Status

```
Available  -> Bound (to a claim)  -> Released (claim deleted, Retain)  -> gone
                                  -> deleted (claim deleted, Delete)
Failed     (reclamation failed)
```

```bash
kubectl describe pv pv-vol1
kubectl get pv pv-vol1 -o jsonpath='{.spec.claimRef}'     # which claim owns it
```

## Static vs dynamic

Writing PV objects by hand is **static provisioning**: fine for a handful of
NFS exports or local disks, unworkable for a hundred teams. **Dynamic
provisioning** - a StorageClass that creates a PV on demand when a claim
appears - is the norm on any cluster with a CSI driver, and is the lesson
after PVCs. The PV object is the same either way; only who creates it differs.

:::exam-tip
Exam PV tasks give you the numbers - name, size, access mode, hostPath,
reclaim policy, sometimes a storageClassName. Write them exactly; the claim
in the next step will only bind if size ≤ capacity, modes match, and the
class name is the same string (or both empty). `kubectl get pv` then shows
`Bound` - that is the proof.
:::

## Check yourself

1. Is a PersistentVolume namespaced? Who usually creates one?
2. A claim asks for `ReadWriteMany`; the only PV is `ReadWriteOnce`. What
   happens?
3. After its claim is deleted, a `Retain` PV shows `Released`. Can a new
   claim bind to it? What do you do?
