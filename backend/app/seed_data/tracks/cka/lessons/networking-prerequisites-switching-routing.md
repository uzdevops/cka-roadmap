## Two machines, one switch

Before any Pod networking, the basics every node and every container rely
on. Two hosts on the same network:

```
A (eth0: 192.168.1.10) ──┐
                         ├── switch ── network 192.168.1.0/24
B (eth0: 192.168.1.11) ──┘
```

```bash
ip link                                  # interfaces: lo, eth0, ...
ip addr add 192.168.1.10/24 dev eth0     # give eth0 an address on that network
ip addr                                  # show addresses
ping 192.168.1.11                        # same network: the switch delivers it
```

A **switch** connects hosts on one network; frames are delivered by MAC
address, and ARP (`ip neigh`) is how a host learns the MAC for an IP on its
own network. Nothing routes; it is all local.

## Two networks, one router

```
A (192.168.1.10) ── switch 1 ── router ── switch 2 ── C (192.168.2.10)
                    192.168.1.0/24  │  │  192.168.2.0/24
                   router: 192.168.1.1  192.168.2.1
```

A **router** has an interface on each network and forwards packets between
them. For A to reach C, A needs a **route**: "to reach 192.168.2.0/24, send
to 192.168.1.1".

```bash
ip route add 192.168.2.0/24 via 192.168.1.1
ip route                                 # the routing table
```

And the one route every host has: the **default gateway** - "anything I do
not have a route for, send here".

```bash
ip route add default via 192.168.1.1
ip route
# default via 192.168.1.1 dev eth0
# 192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.10
```

:::tip
`ip route` reads top to bottom with "most specific prefix wins": a
`/24` route beats `default`. When a packet "goes nowhere", this table is the
first thing to read - is there a route for that destination, and does
`via` point at something reachable on a local network?
:::

## A Linux host as a router

Any Linux box with two interfaces can forward between them - if told to:

```bash
cat /proc/sys/net/ipv4/ip_forward       # 0 = drop packets not addressed to me
echo 1 > /proc/sys/net/ipv4/ip_forward  # forward them
# persist: net.ipv4.ip_forward = 1 in /etc/sysctl.d/99-k8s.conf, then sysctl --system
```

This matters more than it looks: **every Kubernetes node is a router** for
its Pods. `ip_forward=1` is one of the kernel settings kubeadm and the CNI
require, and a node with it off has Pods that cannot talk out.

## The tools, modern and old

| Old (net-tools) | Modern (iproute2) | Shows |
|---|---|---|
| `ifconfig` | `ip addr`, `ip link` | interfaces and addresses |
| `route -n` | `ip route` | routing table |
| `arp -a` | `ip neigh` | ARP cache |
| `netstat -nltp` | `ss -nltp` | listening sockets |
| `brctl show` | `ip link show type bridge`, `bridge link` | bridges |

Exam nodes have the modern set for sure; the old one maybe. Learn `ip`.

```bash
ip link show eth0                        # state, MAC
ip -br addr                              # brief, one line per interface
ip route get 8.8.8.8                     # which route and interface a destination would use
```

## Why this is the first networking lesson

The Pod network you will meet in a week is: a **bridge** on every node (a
software switch), **veth pairs** plugging each Pod into it, **routes** on
each node saying "Pod CIDR of node02 goes via node02's IP", and a node that
**forwards**. Every piece is on this page. The rest is naming.

## Check yourself

1. What is the difference between a switch and a router, in terms of what
   each looks at?
2. Write the command that adds a default gateway of 192.168.1.1 and the one
   that shows the routing table.
3. Why must `net.ipv4.ip_forward` be 1 on a Kubernetes node?
