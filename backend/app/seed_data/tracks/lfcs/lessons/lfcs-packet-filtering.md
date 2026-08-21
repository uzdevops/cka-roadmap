## Three interfaces to one filter

Under everything is the kernel's **netfilter**. Above it:

| Tool | Where | Note |
|---|---|---|
| **nftables** (`nft`) | modern default | replaces iptables; one framework for IPv4/IPv6 |
| **firewalld** (`firewall-cmd`) | RHEL family, also on Ubuntu | zones and services on top of nftables |
| **ufw** | Ubuntu default | simple rules on top of nftables/iptables |
| **iptables** | legacy | still everywhere in documentation; usually a shim over nftables now |

Run **one** of them. Two managers on the same host fight over the ruleset.

## ufw: the Ubuntu way

```bash
sudo ufw status verbose
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp                       # or: sudo ufw allow OpenSSH
sudo ufw allow 80,443/tcp
sudo ufw allow from 192.168.1.0/24 to any port 3306 proto tcp
sudo ufw allow in on eth1 to any port 53
sudo ufw deny from 10.20.30.40
sudo ufw limit 22/tcp                        # rate-limit repeated connections (brute force)
sudo ufw delete allow 80/tcp
sudo ufw status numbered && sudo ufw delete 3
sudo ufw enable                              # persistent across reboots
sudo ufw disable
sudo ufw reset
sudo ufw app list; sudo ufw app info OpenSSH
sudo ufw logging on
```

:::warning
`sudo ufw enable` with `default deny incoming` and **no SSH rule** ends
your session immediately. Always `sudo ufw allow 22/tcp` (or `allow
OpenSSH`) **before** enabling - on every firewall tool, the SSH rule comes
first.
:::

## firewalld: zones and services

A **zone** is a policy applied to interfaces or sources: `public`,
`internal`, `trusted`, `dmz`, `drop`, `work`, `home`.

```bash
sudo systemctl enable --now firewalld
firewall-cmd --state
firewall-cmd --get-active-zones
firewall-cmd --get-default-zone
firewall-cmd --list-all                                   # the default zone's whole policy
firewall-cmd --zone=public --list-all
firewall-cmd --get-services                                # named services it knows
```

Two-step rule: change the **runtime**, then make it **permanent** - or add
`--permanent` and `--reload`.

```bash
sudo firewall-cmd --add-service=http                       # runtime only, lost on reload
sudo firewall-cmd --permanent --add-service=http           # config only, not active yet
sudo firewall-cmd --reload                                 # activate the permanent config
sudo firewall-cmd --runtime-to-permanent                   # save what is currently active
```

```bash
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --permanent --remove-service=cockpit
sudo firewall-cmd --permanent --zone=internal --add-source=192.168.1.0/24
sudo firewall-cmd --permanent --zone=internal --add-service=ssh
sudo firewall-cmd --permanent --change-interface=eth1 --zone=internal
sudo firewall-cmd --permanent --set-default-zone=public
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="10.0.0.0/8" service name="mysql" accept'
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="10.20.30.40" drop'
sudo firewall-cmd --reload
firewall-cmd --list-all --zone=internal
```

Rich rules add sources, logging, rate limits and rejects that the simple
`--add-service` form cannot express.

## nftables directly

```bash
sudo nft list ruleset
sudo nft list tables
sudo nft add table inet filter
sudo nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
sudo nft add rule inet filter input ct state established,related accept
sudo nft add rule inet filter input iif lo accept
sudo nft add rule inet filter input tcp dport 22 accept
sudo nft add rule inet filter input tcp dport { 80, 443 } accept
sudo nft add rule inet filter input ip saddr 192.168.1.0/24 tcp dport 3306 accept
sudo nft add rule inet filter input icmp type echo-request limit rate 5/second accept
sudo nft -a list ruleset                       # with handles, needed for delete
sudo nft delete rule inet filter input handle 7
```

Persist:

```bash
sudo nft list ruleset | sudo tee /etc/nftables.conf
sudo systemctl enable --now nftables
```

A minimal `/etc/nftables.conf`:

```
#!/usr/sbin/nft -f
flush ruleset
table inet filter {
  chain input {
    type filter hook input priority 0; policy drop;
    ct state established,related accept
    iif lo accept
    ct state invalid drop
    tcp dport 22 accept
    tcp dport { 80, 443 } accept
    icmp type echo-request accept
  }
  chain forward { type filter hook forward priority 0; policy drop; }
  chain output  { type filter hook output  priority 0; policy accept; }
}
```

The order matters: **established/related first** (so replies to your own
traffic are allowed), loopback second, then the specific ports, with a
default `drop` policy.

## iptables, for reading old documentation

```bash
sudo iptables -L -n -v --line-numbers
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -P INPUT DROP
sudo iptables -D INPUT 3
sudo iptables-save > /etc/iptables/rules.v4       # persist (iptables-persistent)
sudo iptables-restore < /etc/iptables/rules.v4
```

Chains `INPUT`/`FORWARD`/`OUTPUT`, targets `ACCEPT`/`DROP`/`REJECT`, tables
`filter`/`nat`/`mangle` - the vocabulary nftables inherited.

## Testing your rules

```bash
sudo ufw status numbered; sudo firewall-cmd --list-all; sudo nft list ruleset
ss -tulpn                                     # what is listening at all
nc -zv <host> 22                              # from ANOTHER machine
nmap -Pn -p 22,80,443 <host>                  # if available
sudo journalctl -k | grep -i "UFW\|nft\|DROP" # logged drops
sudo tcpdump -ni eth0 port 8080               # is the packet even arriving?
```

Test from another host: a rule that blocks the world still lets loopback
through, so `curl localhost` proves nothing about the firewall.

:::exam-tip
The exam machine is Ubuntu, so `ufw` is most likely, but firewalld is
explicitly in the objectives - know both vocabularies. The pattern is the
same: allow SSH first, set the default policy, add the rules the task
names, make it persistent (`ufw enable`, or `--permanent` + `--reload`),
and verify with `status`/`--list-all`.
:::

## Check yourself

1. What must you always do before enabling a default-deny firewall
   remotely?
2. In firewalld, what is the difference between a runtime and a permanent
   change, and which two commands bridge them?
3. Why must an nftables input chain accept `ct state established,related`
   early?
