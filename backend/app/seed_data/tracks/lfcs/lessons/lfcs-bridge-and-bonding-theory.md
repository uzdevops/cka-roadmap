## Two different problems

**A bridge** joins interfaces into one layer-2 segment - a software
switch. **A bond** joins interfaces into one logical interface for
redundancy or throughput. They are often confused because both "combine
interfaces"; they combine them for opposite reasons.

```
 BRIDGE (a switch inside the host)          BOND (one link made of several)
   eth0 ─┐                                    eth0 ─┐
   vnet0 ─┼─ br0 ── has the IP                eth1 ─┼─ bond0 ── has the IP
   vnet1 ─┘                                          (one path, several cables)
```

## Bridges

A bridge learns MAC addresses on each port and forwards frames between
them, exactly like a physical switch. The host can give the **bridge** an
IP address and use it as its own interface.

Where you meet one:

- **Virtual machines**: `br0` contains the physical NIC and each VM's
  `vnetN`, so VMs appear on the LAN as ordinary hosts (the VM lesson's
  "bridge" network mode).
- **Containers**: `docker0` is a bridge with a private subnet and NAT.
- **Joining two segments** without buying a switch.

Facts worth remembering:

- A bridge is layer 2: it forwards by **MAC**, does not care about IP
  subnets, and does not route.
- Once an interface is enslaved to a bridge, **it should not carry its own
  IP** - the address moves to the bridge.
- Broadcast traffic crosses the bridge; the ports share one collision-free
  segment.
- **STP** (Spanning Tree Protocol) prevents loops when bridges are cabled
  in a ring; it costs ~30 seconds of forwarding delay unless you use
  `stp off` on a simple host bridge.

## Bonds (link aggregation, "teaming", "NIC teaming")

Several NICs behave as one interface. Two reasons: **survive a cable,
port, or switch failure**, and **use more than one link's bandwidth**.
Some modes need cooperation from the switch, some do not.

| Mode | Name | Switch support | Gives |
|---|---|---|---|
| 0 | `balance-rr` | needs static aggregation | round-robin; can reorder packets |
| **1** | **`active-backup`** | **none** | redundancy only - one link active, others idle |
| 2 | `balance-xor` | static aggregation | load balance by hash of MAC/IP |
| 3 | `broadcast` | none | every frame on every link (rare) |
| **4** | **`802.3ad` (LACP)** | **LACP configured** | the standard aggregation: negotiated, load-balanced, fault-tolerant |
| 5 | `balance-tlb` | none | transmit load balancing |
| 6 | `balance-alb` | none | transmit and receive load balancing |

The two you will actually use: **mode 1** when you cannot configure the
switch (or the NICs go to two different switches), and **mode 4 (LACP)**
when you can - it is the industry standard and detects failures properly.

Bond parameters:

| Option | Means |
|---|---|
| `miimon=100` | check link state every 100 ms (the basic failure detector) |
| `updelay` / `downdelay` | wait before declaring a link up/down - avoids flapping |
| `lacp_rate=fast` | LACP packets every second instead of every 30 |
| `xmit_hash_policy=layer3+4` | which fields choose the outgoing link (better spread) |
| `primary=eth0` | preferred active link in active-backup |

```bash
cat /proc/net/bonding/bond0        # mode, active slave, per-link status - the file to read when diagnosing
```

Important expectation-setting: aggregation balances **flows**, not
packets. Two 1 Gbit links do not make a single TCP connection go at
2 Gbit; they let two connections use one link each. Redundancy is
deterministic, throughput is statistical.

## Bridge on top of a bond

The production pattern for a virtualisation host: bond the NICs for
redundancy, bridge on top so VMs attach to it.

```
 eth0 ─┐
       ├─ bond0 (802.3ad) ─── br0 ─── vnet0, vnet1 (VMs)   ← br0 holds the host's IP
 eth1 ─┘
```

## VLANs, in one paragraph

A VLAN tag divides one physical link into several logical networks
(`eth0.10`, `eth0.20`). Bridges, bonds and VLANs stack: `bond0.10` is
VLAN 10 on the bond, and `br10` bridges it to VMs in that VLAN. Not a core
LFCS objective, but the vocabulary shows up in the same conversations.

:::warning
Both changes can cut your own connection: enslaving the interface you are
connected through moves the IP to the bridge or bond, and if any step is
wrong the session dies. Do this from the console (`virsh console`, IPMI),
or use `nmcli` with a scripted rollback, or accept that you may need
physical access. Never "just try it" on a remote production host.
:::

:::exam-tip
Know the vocabulary and the two mode names: `active-backup` (no switch
configuration) and `802.3ad` (LACP, needs the switch). Know that the IP
belongs to `br0`/`bond0`, not to the enslaved interfaces, and that
`/proc/net/bonding/bond0` is where you read a bond's real state. The next
lesson builds both.
:::

## Check yourself

1. What problem does a bridge solve and what problem does a bond solve?
2. Which bonding mode needs no switch configuration, and which is the
   negotiated standard?
3. After enslaving `eth0` to `br0`, which interface holds the IP address,
   and why?
