## Questions before the first command

"Install Kubernetes" is not a plan. The plan is the answers to five
questions, because each one changes what you install and where.

### 1. What is it for?

| Purpose | Shape |
|---|---|
| learning, a laptop | minikube / kind: one node, control plane and worker together |
| development, testing | a small multi-node cluster, often kubeadm on VMs, or a managed cluster per team |
| production | multiple control plane nodes, separate etcd or stacked with ≥3, workers sized to the load, HA load balancer in front of the API |

A single-node cluster is fine for learning and useless for anything that must
stay up: every component shares one failure domain.

### 2. Cloud or on-prem?

- **Managed** (EKS, GKE, AKS): the provider runs the control plane; you do
  not upgrade the API server or back up etcd - and you cannot tune them
  either. Most teams should start here.
- **Self-managed on cloud VMs**: kubeadm (or kops, Cluster API); full control,
  full responsibility, cloud integrations (LoadBalancer Services, CSI disks)
  still available.
- **On-prem / bare metal**: kubeadm, or a distribution (Rancher/RKE2,
  OpenShift, k3s); you also provide the load balancer (MetalLB), storage
  (Ceph, NFS, a SAN's CSI) and the machines.

The CKA is the self-managed world: kubeadm on Linux hosts.

### 3. How big?

| Limit (upstream-tested) | Value |
|---|---|
| nodes per cluster | 5,000 |
| Pods per cluster | 150,000 |
| containers per cluster | 300,000 |
| Pods per node | 110 (kubelet default `maxPods`) |

Plus the arithmetic from the IPAM lesson: a `/16` Pod CIDR with `/24` per
node is 256 nodes. Size the control plane to the node count - the API server
and etcd need more CPU and memory (and faster disks for etcd) as the cluster
grows; the upstream docs have a table.

### 4. How many control plane nodes?

| Count | Survives | Notes |
|---|---|---|
| 1 | nothing | lab only |
| 3 | 1 failure | the standard; etcd quorum 2 of 3 |
| 5 | 2 failures | large or critical clusters |

Even numbers buy nothing (4 nodes, quorum 3, survives 1 - same as 3). And the
**etcd topology**: stacked (etcd on the control plane nodes, kubeadm default,
simpler) or external (etcd on its own machines, independent failure, more
boxes). Both are the HA lesson.

### 5. Storage and networking choices

- **CNI**: Calico (policy, BGP or overlay), Cilium (eBPF, policy,
  observability), Flannel (simple, no policy). Pick one that enforces
  NetworkPolicy unless you are sure you will never need it.
- **Storage**: a CSI driver for your environment; on bare metal, Ceph/Rook,
  Longhorn, or a vendor's; NFS for shared filesystems.
- **Ingress/Gateway**: nginx Ingress or a Gateway implementation, and
  whether you need a load balancer (MetalLB on-prem).

## Node requirements

Per the kubeadm docs, every node needs: a supported Linux (Ubuntu, Debian,
RHEL-family, SUSE...), **2 GB RAM and 2 CPUs minimum** (more for control
plane), full network connectivity between nodes, **unique hostname, MAC and
product_uuid**, swap **off** (or the kubelet configured to tolerate it),
the required ports open, and a container runtime installed.

:::exam-tip
The exam does not ask design questions. It hands you nodes that already meet
the requirements and asks you to **bring up** or **join** or **fix** a
cluster. This lesson is the context for why the install steps are what they
are - and the "2 CPUs, swap off, unique machine-id" list is exactly what
`kubeadm init` preflight checks complain about when it fails.
:::

## Check yourself

1. Why are 3 control plane nodes the standard and 4 no better?
2. What does a managed cluster take off your plate, and what does it take
   away?
3. Name four things every node must have before `kubeadm init` will pass
   its preflight checks.
