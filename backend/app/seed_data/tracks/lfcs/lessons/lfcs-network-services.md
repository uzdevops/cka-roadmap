## Start, stop, and check what is listening

Network services are ordinary systemd units - the systemd lesson covers
the verbs. What is specific here is the **second** check: not just "is the
unit active" but "is it listening, on which address and port, and can
anything reach it".

```bash
sudo systemctl start nginx
sudo systemctl enable --now sshd
sudo systemctl reload nginx           # re-read config without dropping connections
sudo systemctl status nginx
systemctl list-units --type=service --state=running | grep -Ei "ssh|nginx|named|chrony"
```

## ss: who is listening

```bash
ss -tulpn
# Netid State  Local Address:Port  Peer Address:Port  Process
# tcp   LISTEN 0.0.0.0:22          0.0.0.0:*          users:(("sshd",pid=812,fd=3))
# tcp   LISTEN 127.0.0.1:5432      0.0.0.0:*          users:(("postgres",pid=990,fd=5))
# tcp   LISTEN [::]:80             [::]:*             users:(("nginx",pid=1102,fd=6))
```

| Flag | |
|---|---|
| `-t` `-u` | TCP / UDP |
| `-l` | listening only |
| `-p` | the process (needs root to see other users') |
| `-n` | numeric ports (no `/etc/services` lookup) |
| `-a` | all sockets, including established |
| `-s` | summary counts |
| `-4` `-6` | address family |

```bash
ss -tulpn | grep :80
ss -tan state established
ss -tp dst 10.0.0.5              # connections to a host
ss -tuln sport = :22
lsof -i :8080                    # the other way to ask
sudo fuser -n tcp 8080           # and a third
sudo netstat -tulpn              # the old command, same idea (net-tools)
```

The **listen address** is the detail that matters: `0.0.0.0`/`[::]` means
every interface; `127.0.0.1` means loopback only, so no remote client can
connect no matter how open the firewall is. "The service is running but I
cannot reach it" is very often this line.

## Testing reachability

```bash
curl -I http://localhost                        # locally first
curl -I http://192.168.1.50                     # then from its own address
curl -sS -o /dev/null -w '%{http_code}\n' http://host/health
nc -zv 192.168.1.50 80                          # is the port open from here?
nc -zv -u 192.168.1.50 53
telnet host 25                                  # for line protocols (SMTP, HTTP)
ping -c2 host                                   # ICMP may be blocked even when TCP works
traceroute host; mtr host
dig @192.168.1.53 example.com                   # test a DNS server specifically
openssl s_client -connect host:443 </dev/null   # TLS handshake and certificate
```

The order that isolates the fault: **on the host** (`curl localhost`) →
**from the host's address** (`curl <its ip>`) → **from another machine**
(`nc -zv`). If the first works and the second does not, the service binds
loopback; if the second works and the third does not, it is the firewall
or routing.

## The common network services

| Service | Unit | Port | Config |
|---|---|---|---|
| SSH | `sshd` / `ssh` | 22 | `/etc/ssh/sshd_config` |
| HTTP(S) | `nginx`, `httpd`, `apache2` | 80, 443 | `/etc/nginx/`, `/etc/apache2/` |
| DNS | `named`, `unbound`, `systemd-resolved` | 53 | `/etc/named.conf` |
| DHCP | `isc-dhcp-server`, `dnsmasq` | 67/68 | `/etc/dhcp/dhcpd.conf` |
| NTP | `chronyd`, `systemd-timesyncd` | 123 | `/etc/chrony/chrony.conf` |
| NFS | `nfs-server` | 2049 | `/etc/exports` |
| Mail | `postfix` | 25, 587 | `/etc/postfix/main.cf` |
| Database | `postgresql`, `mariadb` | 5432, 3306 | per package |

## Config test before reload

Most servers can validate their configuration; do it **before** reloading,
because a reload with a broken file can stop the service:

```bash
sudo nginx -t
sudo apache2ctl configtest
sudo sshd -t                         # or: sshd -T to dump the effective config
sudo named-checkconf
sudo chronyd -Q
sudo postfix check
sudo exportfs -v
```

Then `systemctl reload` (graceful) rather than `restart` where the service
supports it.

## When it will not start

```bash
systemctl status nginx
journalctl -u nginx -n 50 --no-pager
journalctl -xeu nginx
sudo ss -tulpn | grep :80              # is something else already on the port?
sudo lsof -i :80
```

| Message | Cause |
|---|---|
| `Address already in use` | another process holds the port - `ss -tulpn \| grep :PORT` |
| `Permission denied` binding a low port | not root and no `CAP_NET_BIND_SERVICE`; or SELinux port label (week 7) |
| `Cannot assign requested address` | the configured address does not exist on this host |
| starts, unreachable remotely | listening on 127.0.0.1, or the firewall (next lesson) |
| `Failed to start ... configuration test failed` | the config test above would have caught it |

:::exam-tip
The likely task is "make service X run now and at boot, listening on port
P" - `systemctl enable --now X` plus a config edit, verified with `ss
-tulpn | grep P` and a `curl`/`nc`. Always check the **listen address**,
not just the port, and remember the firewall is a separate objective that
the same task may quietly depend on.
:::

## Check yourself

1. Which command lists listening TCP and UDP ports with the owning
   process, and which flags do that?
2. A service is active but unreachable from another host. Name three
   possible causes and how to tell them apart.
3. Why run `nginx -t` before `systemctl reload nginx`?
