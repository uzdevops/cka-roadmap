## Containers have their own network stack

A container sees its own interfaces, its own routing table, its own ARP
cache - and not the host's. That isolation is a **network namespace**: a
copy of the kernel's networking state, private to the processes inside it.
Every Pod is one. Understanding them by hand is the fastest way to understand
what a CNI plugin does.

```bash
ip netns add red
ip netns add blue
ip netns                         # list
ip netns exec red ip link        # only `lo`, and it is DOWN
ip -n red link                   # same thing, shorter
ip netns exec red ip route       # empty
ip netns exec red arp           # empty
```

A fresh namespace has nothing: no interfaces but loopback, no routes. The
host's `eth0` is invisible from inside. The host's own state lives in the
**root namespace**.

## Connecting two namespaces: a veth pair

A **virtual Ethernet pair** is a cable with a plug at each end; whatever goes
in one end comes out the other. Put one end in each namespace:

```bash
ip link add veth-red type veth peer name veth-blue
ip link set veth-red netns red
ip link set veth-blue netns blue
ip -n red addr add 192.168.15.1/24 dev veth-red
ip -n blue addr add 192.168.15.2/24 dev veth-blue
ip -n red link set veth-red up
ip -n blue link set veth-blue up
ip netns exec red ping 192.168.15.2        # works: red <-> blue over the cable
ip netns exec red arp                      # blue's MAC learned
```

Two Pods, a cable between them. It does not scale: with four namespaces you
would need six cables.

## Connecting many: a bridge

A **bridge** is a software switch in the root namespace. Each namespace gets
a veth pair with one end in the namespace and the other end plugged into the
bridge:

```bash
ip link add v-net-0 type bridge
ip link set v-net-0 up
ip addr add 192.168.15.5/24 dev v-net-0          # give the HOST an address on the bridge too

ip link add veth-red type veth peer name veth-red-br
ip link set veth-red netns red
ip link set veth-red-br master v-net-0
ip -n red addr add 192.168.15.1/24 dev veth-red
ip -n red link set veth-red up
ip link set veth-red-br up
# same for blue with 192.168.15.2
ip netns exec red ping 192.168.15.2              # via the bridge
ping 192.168.15.1                                # from the host, because the host has 192.168.15.5 on the bridge
```

That is a Pod network on one node: `v-net-0` is what Docker calls `docker0`
and what a CNI plugin calls `cni0` or `cbr0`; the veth pairs are the Pods'
`eth0`s.

## Reaching the outside: a route and NAT

From `red`, `ping 192.168.1.3` (a host on the LAN) fails - red's routing
table has no idea where that is. Give it a gateway: the host, via the
bridge.

```bash
ip -n red route add 192.168.1.0/24 via 192.168.15.5
ip netns exec red ping 192.168.1.3       # sent... but no reply: 192.168.1.3 has no route back to 192.168.15.0/24
```

The reply goes nowhere because the outside network does not know the
private 192.168.15.0/24 exists. Two fixes, both used in real clusters:

```bash
# 1. NAT: rewrite the source to the host's address on the way out
iptables -t nat -A POSTROUTING -s 192.168.15.0/24 -j MASQUERADE
# 2. or teach the other hosts a route: "192.168.15.0/24 via 192.168.1.x (this host)"
```

And for the internet: `ip -n red route add default via 192.168.15.5` plus
the MASQUERADE above. Inbound to a service in `red` from outside is one more
rule - a DNAT/port forward on the host - which is exactly what a NodePort is.

## What you just built

| By hand | Kubernetes name |
|---|---|
| network namespace | Pod |
| veth pair | the Pod's `eth0` + a host-side `vethXXXX` |
| bridge `v-net-0` | `cni0` / `cbr0` / `docker0` |
| route in the namespace to the bridge IP | the Pod's default route |
| MASQUERADE | what lets Pods reach the internet |
| route on other hosts to this host's Pod range | how node-to-node Pod traffic works without an overlay |

The CNI plugin runs these commands, with different names, every time a Pod
starts. The next lessons are Docker's version and then the CNI standard.

:::tip
`ip netns exec <ns> <command>` runs any command inside the namespace - `ip`,
`ping`, `ss`, `curl`. It is the debugging move for "what does this Pod see",
when `kubectl exec` is not available or the image has no tools: find the
Pod's namespace with `crictl inspect` or `lsns -t net`, and run the host's
tools inside it.
:::

## Check yourself

1. What does a fresh network namespace contain?
2. What are the two ends of a veth pair, and where do they go in the bridge
   design?
3. A namespace can send to the LAN but gets no replies. What is missing, and
   what are the two ways to fix it?
