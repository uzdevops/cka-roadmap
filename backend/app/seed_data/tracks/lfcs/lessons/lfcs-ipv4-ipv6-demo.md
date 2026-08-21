## Three layers of configuration

```
 ip / ifconfig     → the kernel, right now, LOST ON REBOOT
 NetworkManager (nmcli) / netplan / systemd-networkd → persistent configuration files
 DHCP             → configuration handed out by a server
```

Use `ip` to inspect and to test; use the persistent tool to make it stick.
Which persistent tool: Ubuntu server uses **netplan** (which drives either
NetworkManager or systemd-networkd); desktops and RHEL use
**NetworkManager** directly.

## Looking

```bash
ip a; ip addr show eth0
ip link show                       # state UP/DOWN, MAC, MTU
ip -br a                           # brief, one line per interface
ip -4 a; ip -6 a
ip r; ip -6 r; ip r get 8.8.8.8
ip neigh                           # the ARP table
nmcli device status
nmcli connection show
hostnamectl
resolvectl status
```

## Changing now (not persistent)

```bash
sudo ip link set eth0 up
sudo ip link set eth0 down
sudo ip addr add 192.168.1.50/24 dev eth0
sudo ip addr del 192.168.1.50/24 dev eth0
sudo ip route add default via 192.168.1.1
sudo ip route add 10.0.0.0/8 via 192.168.1.254 dev eth0
sudo ip route del default
sudo ip link set eth0 mtu 9000
sudo ip -6 addr add 2001:db8::10/64 dev eth0
```

Everything above is gone after a reboot or a NetworkManager restart. That
makes `ip` perfect for testing a theory ("is it the gateway?") and wrong
for configuration.

## Persistent with nmcli

```bash
nmcli con show                                   # the connection profiles
nmcli con show "Wired connection 1"              # every property
nmcli dev status

# static IPv4
sudo nmcli con mod eth0 \
  ipv4.method manual \
  ipv4.addresses 192.168.1.50/24 \
  ipv4.gateway 192.168.1.1 \
  ipv4.dns "1.1.1.1 8.8.8.8" \
  ipv4.dns-search example.com
sudo nmcli con up eth0                            # apply

# back to DHCP
sudo nmcli con mod eth0 ipv4.method auto ipv4.addresses "" ipv4.gateway ""
sudo nmcli con up eth0

# a new profile
sudo nmcli con add type ethernet con-name lab ifname eth1 \
  ip4 10.0.0.5/24 gw4 10.0.0.1
sudo nmcli con mod lab ipv6.method manual ipv6.addresses 2001:db8::5/64 ipv6.gateway 2001:db8::1
sudo nmcli con up lab
sudo nmcli con delete lab
sudo nmcli con mod eth0 connection.autoconnect yes
```

Profiles are files in `/etc/NetworkManager/system-connections/*.nmconnection`
(mode 600 - they can hold Wi-Fi keys).

## Persistent with netplan (Ubuntu)

```bash
ls /etc/netplan/
sudo vi /etc/netplan/01-netcfg.yaml
```

```yaml
network:
  version: 2
  renderer: networkd            # or NetworkManager
  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - 192.168.1.50/24
        - 2001:db8::10/64
      routes:
        - to: default
          via: 192.168.1.1
        - to: 10.0.0.0/8
          via: 192.168.1.254
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8]
        search: [example.com]
    eth1:
      dhcp4: true
```

```bash
sudo chmod 600 /etc/netplan/01-netcfg.yaml
sudo netplan generate                 # render backend config
sudo netplan try                      # apply with a 120-second automatic rollback  ← use this remotely
sudo netplan apply                    # apply immediately
ip a; ip r
```

:::warning
YAML: two-space indentation, **no tabs**, and the file is order-sensitive.
`netplan try` is the safe way to apply a change over SSH - if you lock
yourself out, it reverts by itself after two minutes. `netplan apply` does
not.
:::

## Hostname and hosts

```bash
hostnamectl                                   # static, pretty, transient hostnames
sudo hostnamectl set-hostname web01.example.com
hostname; hostname -f                          # short; fully qualified
cat /etc/hostname
sudo vi /etc/hosts
```

```
127.0.0.1       localhost
127.0.1.1       web01.example.com web01
192.168.1.60    db01.example.com db01
::1             localhost ip6-localhost ip6-loopback
```

An entry in `/etc/hosts` beats DNS (per `nsswitch.conf`) - handy for a fixed
mapping, and a classic cause of "it resolves to the wrong address on this
one machine".

## DNS resolution

```bash
cat /etc/resolv.conf
resolvectl status                          # the systemd-resolved truth
resolvectl query example.com
sudo resolvectl flush-caches
dig example.com; dig +short example.com; dig @1.1.1.1 example.com
dig -x 192.168.1.60                        # reverse lookup
host example.com; nslookup example.com
getent hosts example.com                    # resolution the way applications do it (hosts + DNS)
```

On systemd-resolved systems set DNS through nmcli/netplan, not by editing
`/etc/resolv.conf` - it is a symlink to a generated stub file.

## Verify, every time

```bash
ip -br a; ip r
ping -c2 <gateway>; ping -c2 8.8.8.8; ping -c2 example.com
ss -tulpn | head
traceroute 8.8.8.8
```

:::exam-tip
"Configure eth0 with a static address A/N, gateway G and DNS D,
persistently" → nmcli's four `ipv4.*` properties then `con up`, or a
netplan block then `netplan apply`. Verify with `ip a`, `ip r` and a `ping`
- and remember the DNS half, which is the part most often left out.
:::

## Check yourself

1. Why is `ip addr add` not enough to configure an address, and what is it
   good for?
2. Write the nmcli command that sets a static address, gateway and DNS on
   `eth0`.
3. Why should you use `netplan try` rather than `netplan apply` over SSH?
