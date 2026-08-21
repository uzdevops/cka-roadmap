## Who decides a Pod's address

The CNI plugin is asked for an IP every time a Pod starts. Where does it
come from, and how do two nodes avoid handing out the same one? That is
**IP Address Management**, and the CNI specification makes it a separate,
pluggable step: the network plugin calls an **IPAM plugin** named in its
config.

```json
"ipam": {
  "type": "host-local",
  "subnet": "10.244.1.0/24",
  "routes": [{"dst": "0.0.0.0/0"}]
}
```

## The two reference IPAM plugins

| Plugin | Allocates from | Records allocations in |
|---|---|---|
| `host-local` | a subnet given in the config - **this node's** slice of the Pod CIDR | files on the node: `/var/lib/cni/networks/<name>/<ip>` (one file per address, containing the container ID) |
| `dhcp` | a DHCP server on the network | the DHCP server's leases (a `dhcp` daemon runs on the node to keep leases alive) |

```bash
ls /var/lib/cni/networks/cbr0/
# 10.244.1.2  10.244.1.3  last_reserved_ip.0  lock
cat /var/lib/cni/networks/cbr0/10.244.1.2      # the container ID that holds it
```

`host-local` is what Flannel delegates to and what many plugins use under
the hood. Uniqueness across nodes is simple: each node has a **different
subnet**, so two nodes cannot collide - and within a node, the files are the
ledger.

## Where the per-node subnet comes from

```bash
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.podCIDR}{"\n"}{end}'
# controlplane   10.244.0.0/24
# node01         10.244.1.0/24
# node02         10.244.2.0/24
```

The **controller manager** (`--allocate-node-cidrs=true`,
`--cluster-cidr=10.244.0.0/16`, `--node-cidr-mask-size=24`) carves the
cluster Pod CIDR into per-node `/24`s and writes each into `node.spec.podCIDR`.
The CNI DaemonSet reads that and writes it into the node's IPAM config. So
the chain is: `kubeadm init --pod-network-cidr` → controller manager flags →
`node.spec.podCIDR` → CNI config → `host-local` → Pod IP.

A `/24` per node is **254 Pods per node at most** - plenty, given the
kubelet's default `maxPods=110`, but the reason a `/16` cluster CIDR tops out
at 256 nodes.

## Plugins with their own IPAM

Calico and Cilium do not use `host-local`. Calico's IPAM hands out smaller
blocks (`/26`) to nodes on demand from IP pools, so a node that runs many
Pods can take several and a node that runs few does not waste a `/24`; it
keeps the ledger in the Kubernetes API (Calico's `IPAMBlock` CRDs) rather
than in files. The idea is the same - a ledger, and a guarantee of
uniqueness - with more flexibility.

```bash
kubectl get ippools.crd.projectcalico.org -o yaml 2>/dev/null | grep cidr
calicoctl ipam show 2>/dev/null
```

:::exam-tip
The exam question is usually "what range are Pods on node01 assigned from"
(`node.spec.podCIDR`) or "which IPAM does this CNI use" (read the `ipam`
block of the file in `/etc/cni/net.d`). A Pod stuck with `failed to allocate
for range` in its events means that node's subnet is exhausted or the IPAM
ledger is wedged - stale files in `/var/lib/cni/networks` after a hard
reboot are a known cause, and deleting the stale entries fixes it.
:::

## Check yourself

1. Which plugin in a typical CNI config actually chooses the Pod IP, and
   where does it record what it handed out?
2. Who assigns `node.spec.podCIDR`, and from which flag?
3. Why can two nodes using `host-local` never allocate the same IP?
