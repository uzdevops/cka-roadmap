## LFCS mock exam 3

Two hours. Fifteen tasks, total 100. The networking-heavy one: NAT, a
reverse proxy, a bridge, plus containers, SELinux/AppArmor and quotas.
Two VMs help for tasks 4 and 8; a single VM with two NICs is enough for
the rest. Snapshot first.

---

**1.** (8) Configure this host to masquerade traffic from
`192.168.150.0/24` out through the primary interface, with IP forwarding
enabled persistently. Show the NAT rules in `/root/nat.txt`.

**2.** (8) Forward inbound TCP port 8080 on this host to port 80 on the
same host, persistently. Verify with `curl -I http://localhost:8080`.

**3.** (8) Install nginx and configure it as a reverse proxy: requests to
`/app/` on port 80 go to `http://127.0.0.1:8000`. Start a simple listener
on 8000 (`python3 -m http.server 8000`) to prove it. Save the `curl -I`
output to `/root/proxy.txt`.

**4.** (7) Create a bridge `br0` containing the second interface, holding
address `192.168.160.1/24`, persistently. Show `ip -br a` and `bridge
link` in `/root/bridge.txt`.

**5.** (7) Run a container named `web` from the `nginx:alpine` image,
publishing host port 8081 to container port 80, mounting `/srv/site` (with
an `index.html` you create) read-only at
`/usr/share/nginx/html`, restarting automatically. Verify with `curl`.

**6.** (6) Create a user `ops` whose processes are limited to 100
processes and 4096 open files, persistently. Show the effective limits
from a fresh login in `/root/limits.txt`.

**7.** (7) Enable user quotas on a filesystem you create on `/dev/sdb1`
mounted at `/mnt/quota`, and set a 100 MB soft / 120 MB hard block limit
for user `ops`. Show `repquota` output in `/root/quota.txt`.

**8.** (7) Mount the NFS export from another host (or `localhost` if you
exported one in mock 2) at `/mnt/remote`, persistently, so that a missing
server does not prevent booting.

**9.** (7) Configure `chrony` to use `pool.ntp.org` and to serve time to
`192.168.150.0/24`. Show `chronyc sources` in `/root/chrony.txt`.

**10.** (6) Create a self-signed certificate valid 365 days for
`server.local` at `/etc/ssl/certs/server.crt` with its key at
`/etc/ssl/private/server.key` (mode 600). Show the subject, issuer and
dates in `/root/cert.txt`.

**11.** (6) Add a repository key and source for any third-party repository
of your choice using the `signed-by` keyring method, then show
`apt-cache policy` for a package from it in `/root/repo.txt`.

**12.** (6) Find every world-writable file under `/var` that is not a
symbolic link, and write the list to `/root/worldwritable.txt`.

**13.** (6) Configure a systemd **timer** that runs a oneshot service
`report.service` every day at 02:30, with `Persistent=true`. Show
`systemctl list-timers` filtered to it in `/root/timer.txt`.

**14.** (5) Replace every occurrence of `oldhost.example.com` with
`newhost.example.com` in all `.conf` files under `/etc/myapp` (create a
few), in place, keeping a `.bak` of each.

**15.** (6) Show, in `/root/netcheck.txt`: the default route, the DNS
servers in use, and every listening TCP port with its process.

---

:::exam-tip
Tasks 1, 2 and 4 will cut your own connection if you get them wrong -
work from the VM console (`virsh console`), not over SSH. That is exactly
the constraint the real exam removes (its terminal is not affected by your
firewall rules) but the habit of thinking "does this change my own path
in?" is worth keeping.
:::

## Check yourself

1. Which task's change would most likely lock you out, and how did you
   protect against it?
2. For task 2, which port did the filter rules have to allow, and why?
3. Which of these fifteen tasks did you finish without consulting `man`?
