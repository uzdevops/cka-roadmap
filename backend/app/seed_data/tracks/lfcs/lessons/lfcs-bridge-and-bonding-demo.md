## Building a bridge with nmcli

Do this on a VM with two NICs, from the **console**, not over the
interface you are about to enslave.

```bash
nmcli device status
# DEVICE  TYPE      STATE      CONNECTION
# eth0    ethernet  connected  Wired connection 1
# eth1    ethernet  connected  Wired connection 2
```

```bash
# 1. create the bridge
sudo nmcli con add type bridge ifname br0 con-name br0 stp no

# 2. give the bridge the address (static here; ipv4.method auto for DHCP)
sudo nmcli con mod br0 ipv4.method manual ipv4.addresses 192.168.1.50/24 \
  ipv4.gateway 192.168.1.1 ipv4.dns 1.1.1.1

# 3. enslave the physical interface
sudo nmcli con add type ethernet ifname eth1 con-name br0-port1 master br0

# 4. bring it up (the old profile on eth1 must go down)
sudo nmcli con down "Wired connection 2" 2>/dev/null
sudo nmcli con up br0
sudo nmcli con up br0-port1
```

```bash
ip -br a
# br0        UP   192.168.1.50/24        ← the IP is HERE
# eth1       UP                          ← no address of its own
bridge link show
ip link show master br0
nmcli con show br0 | grep -Ei "bridge|ipv4"
ping -c2 192.168.1.1
```

The `bridge` command inspects it:

```bash
bridge link            # ports and their state
bridge fdb show br br0 # the learned MAC table
bridge -d link show    # detail: STP state, path costs
```

Removing it:

```bash
sudo nmcli con delete br0-port1 br0
sudo nmcli con up "Wired connection 2"
```

## Attaching VMs to the bridge

```bash
sudo virsh attach-interface web01 --type bridge --source br0 --model virtio --config
# or in virt-install:  --network bridge=br0
virsh domiflist web01
```

The VM now gets an address from the LAN's DHCP, like any physical machine.

## Building a bond with nmcli

```bash
# 1. the bond, active-backup with link monitoring
sudo nmcli con add type bond ifname bond0 con-name bond0 \
  bond.options "mode=active-backup,miimon=100,primary=eth1"

# LACP instead:
# bond.options "mode=802.3ad,miimon=100,lacp_rate=fast,xmit_hash_policy=layer3+4"

# 2. address on the bond
sudo nmcli con mod bond0 ipv4.method manual ipv4.addresses 192.168.1.60/24 \
  ipv4.gateway 192.168.1.1 ipv4.dns 1.1.1.1

# 3. enslave the members
sudo nmcli con add type ethernet ifname eth1 con-name bond0-p1 master bond0
sudo nmcli con add type ethernet ifname eth2 con-name bond0-p2 master bond0

# 4. up
sudo nmcli con up bond0
sudo nmcli con up bond0-p1
sudo nmcli con up bond0-p2
```

```bash
ip -br a | grep bond
cat /proc/net/bonding/bond0
# Bonding Mode: fault-tolerance (active-backup)
# Primary Slave: eth1 (primary_reselect always)
# Currently Active Slave: eth1
# MII Status: up
# Slave Interface: eth1   MII Status: up   Link Failure Count: 0
# Slave Interface: eth2   MII Status: up   Link Failure Count: 0
```

Test the failover - the point of the whole exercise:

```bash
ping -i 0.2 192.168.1.1 &                  # keep traffic flowing
sudo ip link set eth1 down                 # simulate a cable pull
grep "Currently Active Slave" /proc/net/bonding/bond0     # now eth2
# ping loses at most a packet or two
sudo ip link set eth1 up
```

## The same with netplan (Ubuntu)

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth1: {dhcp4: false}
    eth2: {dhcp4: false}
  bonds:
    bond0:
      interfaces: [eth1, eth2]
      parameters:
        mode: active-backup
        primary: eth1
        mii-monitor-interval: 100
      addresses: [192.168.1.60/24]
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1]
  bridges:
    br0:
      interfaces: [bond0]
      addresses: [192.168.1.50/24]
      parameters:
        stp: false
```

```bash
sudo netplan generate
sudo netplan try            # 120-second auto-rollback - the safe way
```

## Quick, non-persistent versions (for testing only)

```bash
sudo ip link add br0 type bridge
sudo ip link set eth1 master br0
sudo ip link set br0 up
sudo ip addr add 192.168.1.50/24 dev br0

sudo modprobe bonding
sudo ip link add bond0 type bond mode active-backup miimon 100
sudo ip link set eth1 down && sudo ip link set eth1 master bond0
sudo ip link set eth2 down && sudo ip link set eth2 master bond0
sudo ip link set bond0 up
```

Gone after a reboot - useful to prove a theory, never as configuration.

## When it does not work

| Symptom | Look at |
|---|---|
| bridge up, no connectivity | the IP is still on the slave; STP delay (~30 s) - set `stp no` |
| bond shows one slave `MII Status: down` | cable, switch port, or a slave still owned by another connection profile |
| LACP bond passes no traffic | the switch side is not configured for LACP - use active-backup until it is |
| both slaves up, throughput unchanged | expected: aggregation balances flows, not a single stream |
| host unreachable after the change | you enslaved the interface you were connected through - console needed |

:::exam-tip
The exam version is short: create a bridge or a bond with given
parameters and an address, make it persistent, and show it works. The
sequence is always the same four steps - create the master, address the
master, enslave the members, bring everything up - then verify with
`ip -br a`, `bridge link` or `/proc/net/bonding/bond0`. Do it from the
console.
:::

## Check yourself

1. What are the four nmcli steps that create a working bridge?
2. Which file shows a bond's mode, active slave and per-link status?
3. How would you prove that an active-backup bond actually fails over?
