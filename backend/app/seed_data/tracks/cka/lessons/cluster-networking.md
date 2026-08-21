## What every node needs

Before Pods, the nodes themselves have to talk. Each node needs:

- at least one interface with an IP, a unique hostname, and a unique MAC -
  cloned VMs with the same MAC or `machine-id` are a classic cluster fault;
- the required ports open between nodes;
- kernel settings the CNI relies on.

```bash
hostname; ip -br addr; ip link show eth0 | grep ether
cat /sys/class/dmi/id/product_uuid          # must differ per node
```

## The ports

| Component | Port | Protocol | Who connects |
|---|---|---|---|
| kube-apiserver | **6443** | TCP | everyone |
| etcd | **2379** (clients), **2380** (peers) | TCP | API server; other etcd members |
| kubelet | **10250** | TCP | API server (logs, exec, metrics) |
| kube-scheduler | 10259 | TCP | localhost health/metrics |
| kube-controller-manager | 10257 | TCP | localhost health/metrics |
| kube-proxy | 10256 | TCP | health |
| NodePort Services | **30000-32767** | TCP/UDP | external clients, on every node |
| CNI | varies: Flannel VXLAN 8472/UDP, Calico BGP 179/TCP, Weave 6783 TCP/UDP + 6784 UDP | nodes to nodes |

```bash
ss -tlnp | grep -E "6443|2379|2380|10250"        # what this node actually listens on
kubectl get svc -A | grep NodePort                # which node ports are in use
```

A firewall between nodes that blocks 10250 gives you a cluster where
`kubectl get` works and `kubectl logs`/`exec` time out; one that blocks the
CNI's port gives Pods that reach other Pods on the same node only. Know the
table well enough to spot which symptom points where.

## Kernel and sysctl

```bash
cat /etc/modules-load.d/k8s.conf
# overlay
# br_netfilter
cat /etc/sysctl.d/k8s.conf
# net.bridge.bridge-nf-call-iptables  = 1
# net.bridge.bridge-nf-call-ip6tables = 1
# net.ipv4.ip_forward                 = 1
sysctl --system
```

`br_netfilter` plus `bridge-nf-call-iptables=1` lets iptables see traffic
crossing the bridge - without it, kube-proxy's Service rules do not apply to
Pod-to-Service traffic on the same node, and you get the "Service works from
node A but not from Pods on node A" mystery. `ip_forward` is the node
routing for its Pods. kubeadm's preflight checks complain if these are off.

## The three networks

A cluster has three address ranges that must not overlap:

| Range | Holds | Where set |
|---|---|---|
| node network | the nodes' own IPs | your infrastructure |
| **Pod CIDR** | Pod IPs; each node gets a slice | `kubeadm init --pod-network-cidr`, `--cluster-cidr` on controller manager, the CNI config |
| **Service CIDR** | ClusterIPs | `--service-cluster-ip-range` on the API server (`10.96.0.0/12` default) |

```bash
kubectl cluster-info dump | grep -m1 -- --cluster-cidr
kubectl cluster-info dump | grep -m1 -- --service-cluster-ip-range
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.podCIDR}{"\n"}{end}'
```

:::exam-tip
Questions like "what is the Pod CIDR / Service CIDR of this cluster / what
range is node01 assigned" are answered by those three commands, and by
reading the CNI's ConfigMap (`kubectl get cm kube-flannel-cfg -n kube-flannel
-o yaml` → `Network`). If the CNI's configured range and
`--pod-network-cidr` disagree, Pods get IPs the nodes cannot route - a
favourite install-phase fault.
:::

## What the exam expects about the CNI

The CKA does not care which CNI you know; it cares that you can:

- recognise a cluster with none (`NotReady` nodes, `ContainerCreating` Pods,
  empty `/etc/cni/net.d`);
- **install** one from its manifest, and set its Pod CIDR to match the
  cluster's;
- find which one is installed and what it runs as (usually a DaemonSet in
  `kube-system` or its own namespace);
- know that NetworkPolicy needs a CNI that enforces it.

```bash
kubectl get pods -A -o wide | grep -iE "flannel|calico|weave|cilium"
kubectl get ds -A | grep -iE "flannel|calico|weave|cilium"
```

## Check yourself

1. Which port must be open from the control plane to every node for
   `kubectl logs` to work?
2. Name the three address ranges in a cluster and which flag sets the
   Service one.
3. A Service is reachable from the node's shell but not from Pods on that
   same node. Which sysctl do you check?
