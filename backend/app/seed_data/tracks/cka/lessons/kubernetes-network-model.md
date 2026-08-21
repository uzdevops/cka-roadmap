## The promise

Kubernetes does not implement Pod networking. It *specifies* it, and leaves
the implementation to a CNI plugin. The specification is three sentences:

1. Every Pod gets its own IP address.
2. Every Pod can reach every other Pod, on any node, using that IP, **without
   NAT**.
3. Agents on a node (the kubelet, a DaemonSet) can reach every Pod on that
   node.

Everything else - bridges, overlays, BGP - is a plugin's way of keeping those
promises.

## One node

From the namespaces lesson, on every node the plugin builds:

```
node01 (192.168.1.11)
  ├── cni0 bridge 10.244.1.1/24           one subnet per node
  ├── vethA ── Pod A (eth0 10.244.1.2)
  └── vethB ── Pod B (eth0 10.244.1.3)
```

Each Pod's namespace has a default route via `10.244.1.1` (the bridge). A
and B reach each other through the bridge; they reach the node through it;
with MASQUERADE they reach the outside world.

## Many nodes: the only new problem

Node02 has `10.244.2.0/24`. Pod A (10.244.1.2) sends to Pod C (10.244.2.4).
The packet goes to `cni0`, the node looks up 10.244.2.0/24 in its routing
table, and ... there is nothing. Two families of answer:

**Routes.** Teach every node where every other node's subnet is:

```bash
# on node01
ip route add 10.244.2.0/24 via 192.168.1.12     # node02's subnet lives at node02
ip route add 10.244.3.0/24 via 192.168.1.13
```

That works on a single L2 network (every node can reach every other node
directly). Scaled up, you put the routes in the router instead of on every
node - or let a plugin speak **BGP** to distribute them (Calico's default).
No encapsulation, full speed, packets carry Pod IPs end to end.

**Overlays.** When nodes are on different networks, or you cannot touch the
routers, wrap each Pod packet inside a node-to-node packet:

```
[outer: 192.168.1.11 -> 192.168.1.12][VXLAN][inner: 10.244.1.2 -> 10.244.2.4][data]
```

Flannel (VXLAN mode), Weave, Calico in IPIP/VXLAN mode. Slight overhead, and
it works anywhere nodes can reach each other on one UDP port. Still "no NAT"
from the Pods' point of view - the inner packet is untouched.

## What the plugin does per Pod

When the kubelet creates a Pod, it calls the CNI plugin (via containerd) with
`ADD`; the plugin:

1. creates the veth pair and moves one end into the Pod's namespace as
   `eth0`;
2. plugs the other end into the node's bridge (or sets up routes, for
   plugins without a bridge);
3. asks its **IPAM** for an address from this node's subnet and assigns it;
4. sets the Pod's default route;
5. returns the IP to the kubelet, which writes it into the Pod's
   `status.podIP`.

And the plugin's DaemonSet, once per node, did the cluster-level part: got
the node's subnet (from `node.spec.podCIDR`, which the controller manager
assigns from `--cluster-cidr`), created the bridge, and set up routes or the
overlay to the other nodes.

```bash
kubectl get nodes -o custom-columns=NAME:.metadata.name,CIDR:.spec.podCIDR
kubectl get pods -o wide                 # Pod IPs fall in their node's CIDR
ip route | grep 10.244                   # on a node: routes (or `flannel.1` / `tunl0` for overlays)
```

## Seeing which plugin and how

```bash
ls /etc/cni/net.d                                # 10-flannel.conflist, 10-calico.conflist, ...
kubectl get ds -A | grep -iE "flannel|calico|weave|cilium"
ip -d link show flannel.1 2>/dev/null            # VXLAN device -> overlay
ip route | grep tunl0                            # Calico IPIP
```

:::exam-tip
Exam network tasks do not ask you to choose routes versus overlay. They ask
you to **install** a CNI when there is none, to find the Pod CIDR, and to
debug "Pods on node01 cannot reach Pods on node02" - which is the CNI
DaemonSet not running on one node (`kubectl get pods -n kube-flannel -o
wide`), or a firewall on the CNI's port (8472/UDP for Flannel).
:::

## Check yourself

1. State the network model's three promises.
2. What is the one problem a multi-node cluster adds over a single node, and
   what are the two families of solution?
3. Which object tells you the Pod subnet assigned to a node, and who assigned
   it?
