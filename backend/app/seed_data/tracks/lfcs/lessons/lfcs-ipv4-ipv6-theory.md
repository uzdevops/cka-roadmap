## What has to be true for a host to talk

Four things, and every networking problem is one of them missing:

1. an **interface** that is up,
2. an **address** with a prefix length,
3. a **route** to everything else (usually a default gateway),
4. **name resolution** (DNS), if you want to use names.

```bash
ip a          # 1 and 2
ip r          # 3
cat /etc/resolv.conf   # 4
```

## Addresses and prefixes

An IPv4 address is 32 bits, written as four bytes: `192.168.1.10`. The
**prefix length** (`/24`) says how many leading bits are the network; the
rest identify the host.

| CIDR | Netmask | Hosts | Note |
|---|---|---|---|
| `/24` | 255.255.255.0 | 254 | the everyday LAN |
| `/25` | 255.255.255.128 | 126 | |
| `/16` | 255.255.0.0 | 65534 | |
| `/30` | 255.255.255.252 | 2 | point-to-point links |
| `/32` | 255.255.255.255 | 1 | a single host (loopbacks, routes) |

For `192.168.1.10/24`: network `192.168.1.0`, broadcast `192.168.1.255`,
usable `.1`-`.254`. Two addresses of every subnet are unusable - the
network and the broadcast - which is why a `/24` gives 254, not 256.

**Private ranges** (RFC 1918), never routed on the internet:
`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`. Plus `127.0.0.0/8`
loopback and `169.254.0.0/16` link-local (an address in that range means
"DHCP failed").

```bash
ipcalc 192.168.1.10/26        # network, broadcast, range - if installed
sipcalc 10.0.0.0/22
```

## IPv6, the parts you need

128 bits, eight groups of four hex digits, with rules to shorten:

```
2001:0db8:0000:0000:0000:ff00:0042:8329
2001:db8:0:0:0:ff00:42:8329        ← drop leading zeros in each group
2001:db8::ff00:42:8329             ← :: replaces ONE run of zero groups (only once)
```

| Prefix | Kind |
|---|---|
| `::1/128` | loopback (IPv4's 127.0.0.1) |
| `fe80::/10` | **link-local** - every interface has one, automatically; only valid on that link |
| `fc00::/7` | unique local (IPv4's private ranges) |
| `2000::/3` | global unicast - the routable internet |
| `ff00::/8` | multicast (IPv6 has no broadcast) |

The usual assignment is a `/64` per subnet, and hosts often configure
themselves by **SLAAC** from router advertisements - no DHCP needed. A
link-local address must be written with its interface: `ping6
fe80::1%eth0`.

## Routing

```bash
ip r
# default via 192.168.1.1 dev eth0 proto dhcp metric 100
# 192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.10
```

For each packet the kernel picks the **most specific** matching route;
`default` (`0.0.0.0/0`) matches everything else and points at the gateway.
The gateway must be **on a directly connected subnet** - that is why a
gateway outside your prefix gives "Network is unreachable".

```bash
ip r get 8.8.8.8          # which route and source address WOULD be used
ip -6 r
```

## Name resolution

```bash
cat /etc/nsswitch.conf | grep hosts
# hosts: files dns          ← /etc/hosts first, then DNS
cat /etc/hosts
cat /etc/resolv.conf
# nameserver 192.168.1.1
# search example.com        ← unqualified names get this appended
resolvectl status           # systemd-resolved's real view (resolv.conf may be a stub symlink)
```

Order: `/etc/hosts`, then the DNS servers in `/etc/resolv.conf`. On
systemd-resolved systems `/etc/resolv.conf` is a symlink to a stub
(`127.0.0.53`) and the real servers are in `resolvectl status` - editing
the file directly is then pointless, because it is regenerated.

## Ports, and who is listening

```bash
ss -tulpn
# tcp LISTEN 0 128 0.0.0.0:22   users:(("sshd",pid=800,fd=3))
```

An address plus a port identifies a service. `0.0.0.0:22` listens on every
interface; `127.0.0.1:5432` only on loopback - which is why a database can
be "running" and unreachable from another host. Ports below 1024 need
root (or `CAP_NET_BIND_SERVICE`). `/etc/services` names the well-known
ones: 22 ssh, 25 smtp, 53 dns, 80 http, 443 https, 3306 mysql, 5432
postgres.

## The diagnostic ladder

```bash
ip link show                     # 1. is the interface UP? (NO-CARRIER = cable/link problem)
ip a                             # 2. is there an address? 169.254.x.x = DHCP failed
ping -c2 192.168.1.1             # 3. can I reach the gateway? (layer 2 + 3 on my subnet)
ping -c2 8.8.8.8                 # 4. can I reach the internet by IP? (routing + NAT)
ping -c2 google.com              # 5. does DNS work? (if 4 works and 5 does not, it is DNS)
ss -tulpn                        # 6. is the service listening, and on which address?
traceroute 8.8.8.8               # where the path stops
```

Run it in order and the failing rung is the fault. "Works by IP, not by
name" is DNS; "gateway pings, internet does not" is routing or NAT;
"no address" is DHCP or configuration.

:::exam-tip
Know the theory well enough to answer the exam's practical asks: which
netmask a `/26` is, whether a gateway is reachable from a given address,
and why a service on `127.0.0.1` cannot be reached remotely. The next
lesson does the configuring; this ladder is what you run before and after
every change.
:::

## Check yourself

1. What four things must be true for a host to reach another host by name?
2. How many usable addresses does a `/26` have, and what are the two
   unusable ones?
3. Ping to `8.8.8.8` works but `ping google.com` fails. What is broken?
