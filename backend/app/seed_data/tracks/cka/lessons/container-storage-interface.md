## A contract, not a plugin

The CSI is a specification: a set of gRPC calls a storage system's driver
must answer, and the rules for how an orchestrator calls them. Any storage
vendor who implements it works with Kubernetes (and Nomad, and Mesos)
without touching orchestrator code; Kubernetes does not know or care whether
the other end is EBS, Ceph or a NAS in a cupboard.

```
Kubernetes ──gRPC──▶ CSI driver ──vendor API──▶ the storage system
  "CreateVolume(10Gi)"         create an EBS disk / a Ceph RBD image / an NFS export
  "ControllerPublishVolume"    attach it to node01
  "NodeStageVolume"            format, mount once on the node
  "NodePublishVolume"          bind-mount into the Pod's path
  "DeleteVolume"               tear it down
```

The calls pair up: create/delete, attach/detach (publish/unpublish at the
controller), stage/unstage and publish/unpublish at the node. A driver
implements what its storage can do - a network filesystem has no "attach",
a block device does - and advertises its capabilities.

## What a driver looks like in the cluster

A CSI driver is delivered as ordinary Kubernetes workloads:

| Piece | Runs as | Does |
|---|---|---|
| **controller** plugin | a Deployment/StatefulSet, one or a few replicas | create/delete/attach - the calls that talk to the vendor's API |
| **node** plugin | a DaemonSet, every node | mount/unmount on the node where the Pod is |
| **sidecars** (external-provisioner, external-attacher, node-driver-registrar, ...) | containers alongside the above | translate Kubernetes objects (PVC, VolumeAttachment) into CSI calls |

```bash
kubectl get pods -n kube-system | grep -i csi
# ebs-csi-controller-...        5/5
# ebs-csi-node-...              3/3   (one per node)
kubectl get csidriver
# NAME              ATTACHREQUIRED   PODINFOONMOUNT   STORAGECAPACITY   MODES
# ebs.csi.aws.com   true             false            true              Persistent
kubectl describe csinode node01          # which drivers this node has registered
```

The sidecars are the clever part: they are written once by the Kubernetes
project; a vendor writes only the gRPC service. That is what made the
ecosystem of drivers possible.

## How Kubernetes uses it

You never call a CSI driver. You create a **PersistentVolumeClaim** naming a
**StorageClass**; the StorageClass names a `provisioner` which is the
driver's name; the external-provisioner sidecar sees the claim and calls
`CreateVolume`; a **PersistentVolume** appears, bound to your claim; when a
Pod using the claim lands on a node, the attacher and the node plugin get it
mounted. The next lessons take those objects one at a time - volumes, PVs,
PVCs, StorageClasses - and this is the machinery under all of them.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
provisioner: ebs.csi.aws.com          # <- the CSI driver's name
parameters:
  type: gp3
```

A PV created by a CSI driver records it:

```yaml
spec:
  csi:
    driver: ebs.csi.aws.com
    volumeHandle: vol-0abc123          # the vendor's ID for the disk
    fsType: ext4
```

## In-tree, and the migration away from it

Older manifests have `spec.awsElasticBlockStore:` or `spec.gcePersistentDisk:`
on a PV - the in-tree plugins. Those are gone from recent releases; the
`CSIMigration` work made the old field names transparently route to the CSI
driver while they were being removed. On a current cluster, write CSI (via a
StorageClass) or the always-in-tree basics: `hostPath`, `local`, `nfs`,
`emptyDir`, `configMap`, `secret`.

:::exam-tip
The exam does not ask you to install a CSI driver. It expects you to know
that a StorageClass's `provisioner` names one, that `kubectl get sc` shows
which exist, and that a PVC stuck Pending with a class whose provisioner is
not running will stay Pending - `kubectl describe pvc` says "waiting for a
volume to be created, either by external provisioner ... or manually".
:::

## Check yourself

1. In one sentence: what is the CSI, and who implements it?
2. Which two kinds of workload does a CSI driver run as in the cluster, and
   why two?
3. A PVC is Pending and its events mention "external provisioner". What is it
   waiting for?
