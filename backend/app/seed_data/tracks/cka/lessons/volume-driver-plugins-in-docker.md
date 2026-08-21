## Two plugin points

Docker's storage splits into two things, each with its own plugin interface:

| Concern | Plugin type | Default | Examples |
|---|---|---|---|
| how image layers are stacked into a filesystem | **storage driver** | `overlay2` | aufs, devicemapper, btrfs, zfs |
| where a **volume** actually lives | **volume driver** | `local` (`/var/lib/docker/volumes`) | RexRay, Portworx, Convoy, NetApp, GlusterFS, vSphere plugins |

The storage driver is about images and the container layer - ephemeral by
design. The volume driver is about data you mean to keep, and that is the one
that can reach **off the host**.

```bash
docker volume create --driver local my-vol
docker run -v my-vol:/data alpine

docker plugin install rexray/ebs EBS_ACCESSKEY=... EBS_SECRETKEY=...
docker run -it --volume-driver rexray/ebs --mount src=ebs-vol,target=/data mysql
```

With the RexRay EBS driver, the volume is an AWS EBS disk: the container can
be stopped on one host and started on another, and the same data is there.
That is the capability Kubernetes needs - storage that follows a workload
across nodes.

## Why Kubernetes could not just use Docker volume drivers

Kubernetes never depended on Docker's volume plugins, for three reasons that
together explain the next lesson:

1. Kubernetes runs on several container runtimes (containerd, CRI-O), and
   the volume concept had to be runtime-independent.
2. Kubernetes' own early storage plugins were **in-tree**: the code for AWS
   EBS, GCE PD, Azure Disk, NFS, Ceph and the rest was compiled into
   Kubernetes itself. Every vendor change meant a Kubernetes release; every
   vendor bug was Kubernetes' bug.
3. Vendors needed one interface they could implement once and have it work
   with every orchestrator.

The answer was the **Container Storage Interface (CSI)** - the storage
equivalent of the CRI for runtimes and the CNI for networking - and the
in-tree plugins have since been migrated out to CSI drivers. Kubernetes 1.30+
ships almost no in-tree cloud storage code at all.

```
Runtime  ─── CRI ──▶ containerd, CRI-O
Network  ─── CNI ──▶ Calico, Flannel, Cilium, Weave
Storage  ─── CSI ──▶ EBS CSI, GCE PD CSI, Ceph CSI, NFS CSI, Portworx, ...
```

:::tip
If you remember one thing: Docker volume drivers were the idea; the CSI is
the standard that idea became, and in Kubernetes you will only ever meet the
CSI side - as a **StorageClass** naming a `provisioner` such as
`ebs.csi.aws.com`.
:::

## Seeing it on a cluster

```bash
kubectl get csidrivers                 # CSI drivers registered with this cluster
kubectl get csinodes                   # which drivers each node has
kubectl get storageclass               # PROVISIONER column names the driver
kubectl get pods -n kube-system | grep csi    # the driver's controller and node Pods (a DaemonSet)
```

A cluster with no CSI driver can still use `hostPath`, `local` and NFS
volumes - and cannot dynamically provision anything, which is what the
StorageClass lesson is about.

## Check yourself

1. What is the difference between a storage driver and a volume driver in
   Docker?
2. Why did Kubernetes move its storage plugins out of tree, and what
   interface replaced them?
3. On a cluster, where do you see which storage drivers are installed?
