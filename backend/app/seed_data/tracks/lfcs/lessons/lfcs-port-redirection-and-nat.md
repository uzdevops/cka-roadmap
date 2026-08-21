## Three things called NAT

| Name | Rewrites | Used for |
|---|---|---|
| **SNAT / masquerade** | the **source** address of outgoing packets | many private hosts sharing one public address |
| **DNAT / port forwarding** | the **destination** of incoming packets | reaching an internal server from outside |
| **REDIRECT** | the destination **port** on the same host | 80 → 8080 for a service that cannot bind 80 |

Masquerade is SNAT that takes the outgoing interface's current address -
the right choice when that address is dynamic.

## The prerequisite: IP forwarding

A host that passes packets between interfaces must be told to:

```bash
sysctl net.ipv4.ip_forward
sudo sysctl -w net.ipv4.ip_forward=1                       # now
echo "net.ipv4.ip_forward = 1" | sudo tee /etc/sysctl.d/99-forward.conf
echo "net.ipv6.conf.all.forwarding = 1" | sudo tee -a /etc/sysctl.d/99-forward.conf
sudo sysctl --system                                        # persistent
```

Without it, every NAT rule below silently does nothing.

## firewalld

```bash
# masquerade: let 192.168.100.0/24 reach the internet through this host
sudo firewall-cmd --permanent --zone=public --add-masquerade
sudo firewall-cmd --permanent --zone=internal --add-source=192.168.100.0/24
sudo firewall-cmd --reload
firewall-cmd --list-all --zone=public | grep masquerade

# port forwarding on the same host: 80 → 8080
sudo firewall-cmd --permanent --add-forward-port=port=80:proto=tcp:toport=8080

# forward to ANOTHER host (needs masquerade too)
sudo firewall-cmd --permanent --add-forward-port=port=443:proto=tcp:toport=443:toaddr=192.168.100.10
sudo firewall-cmd --permanent --add-masquerade
sudo firewall-cmd --reload
firewall-cmd --list-forward-ports
```

Remember the port itself must also be **allowed** by the filter:
`--add-port=80/tcp`.

## nftables

```bash
sudo nft add table ip nat
sudo nft 'add chain ip nat prerouting  { type nat hook prerouting  priority -100; }'
sudo nft 'add chain ip nat postrouting { type nat hook postrouting priority 100; }'

# masquerade everything leaving eth0
sudo nft add rule ip nat postrouting oifname "eth0" masquerade
# or explicit SNAT to a fixed public address
sudo nft add rule ip nat postrouting oifname "eth0" ip saddr 192.168.100.0/24 snat to 203.0.113.5

# DNAT: incoming 8080 on eth0 → an internal host
sudo nft add rule ip nat prerouting iifname "eth0" tcp dport 8080 dnat to 192.168.100.10:80
# REDIRECT: 80 → 8080 on this host
sudo nft add rule ip nat prerouting iifname "eth0" tcp dport 80 redirect to :8080

sudo nft list table ip nat
sudo nft list ruleset | sudo tee /etc/nftables.conf       # persist
```

The forward chain must also permit the traffic when the filter policy is
`drop`:

```bash
sudo nft add rule inet filter forward ct state established,related accept
sudo nft add rule inet filter forward iifname "eth1" oifname "eth0" accept
```

## iptables (same rules, older syntax)

```bash
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -t nat -A POSTROUTING -s 192.168.100.0/24 -o eth0 -j SNAT --to-source 203.0.113.5
sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8080 -j DNAT --to-destination 192.168.100.10:80
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080
sudo iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT
sudo iptables -t nat -L -n -v
sudo netfilter-persistent save
```

## ufw

ufw has no first-class NAT commands; edit its rule files:

```bash
sudo sed -i 's/^DEFAULT_FORWARD_POLICY=.*/DEFAULT_FORWARD_POLICY="ACCEPT"/' /etc/default/ufw
sudo vi /etc/ufw/before.rules       # add a *nat block ABOVE the *filter section:
```

```
*nat
:POSTROUTING ACCEPT [0:0]
-A POSTROUTING -s 192.168.100.0/24 -o eth0 -j MASQUERADE
COMMIT
```

```bash
sudo ufw disable && sudo ufw enable
```

## Which hook runs when

```
 incoming ──▶ PREROUTING (DNAT) ──▶ routing decision ──▶ FORWARD/INPUT (filter) ──▶ POSTROUTING (SNAT) ──▶ out
```

Two consequences you will trip over:

- **DNAT happens before filtering**, so the filter rule must allow the
  **translated** destination (port 80 on the internal host), not the
  original port.
- **Only the first packet of a connection** traverses the NAT chains;
  the rest follow conntrack. That is why adding a rule mid-connection
  seems not to work - existing connections keep their old translation.

## Testing

```bash
# on the router
sysctl net.ipv4.ip_forward
sudo nft list table ip nat
sudo conntrack -L | head                   # live translations (conntrack-tools)
sudo tcpdump -ni eth0 'port 8080'          # is the packet arriving, and with which addresses?

# from a client behind the router
ip r                                        # is the router the default gateway?
curl -s ifconfig.me                         # which public address do I appear as?
ping -c2 8.8.8.8

# from outside
nc -zv <public-ip> 8080
curl -I http://<public-ip>:8080
```

| Symptom | Cause |
|---|---|
| clients cannot reach the internet | `ip_forward=0`, no masquerade rule, or FORWARD policy drop |
| forwarded port refused | the filter does not allow the translated port; or the backend is not listening |
| works from outside, not from inside using the public IP | hairpin NAT is not configured (add a matching rule for the internal source) |
| worked, then stopped after a reboot | rules not persisted, or `ip_forward` only set with `sysctl -w` |
| one client works, others do not | the clients' default gateway is not this host |

:::exam-tip
The exam ask is usually one of two: "make this host forward port A to
port B" (`firewall-cmd --add-forward-port=...` or an nft `redirect`
rule), or "let the machines on the internal network reach the internet"
(enable `ip_forward` **persistently** + masquerade on the external
interface). Persist both halves and verify with a real connection, not
just by listing rules.
:::

## Check yourself

1. What is the difference between SNAT, masquerade and DNAT?
2. Which sysctl must be set, and why is `sysctl -w` alone not enough?
3. A DNAT rule sends port 8080 to an internal host's port 80. Which port
   must the filter rules allow, and why?
