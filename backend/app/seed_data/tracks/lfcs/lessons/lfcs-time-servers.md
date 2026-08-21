## Why clocks matter

A wrong clock breaks more than timestamps: TLS certificates are rejected
as "not yet valid", Kerberos and AD logins fail outside a five-minute
skew, log correlation across hosts becomes guesswork, cron fires at the
wrong time, and database replication and backups get confusing ordering.
Time synchronisation is not cosmetic.

## timedatectl: the overview

```bash
timedatectl
#                Local time: Fri 2026-08-21 14:03:11 +05
#            Universal time: Fri 2026-08-21 09:03:11 UTC
#                  RTC time: Fri 2026-08-21 09:03:11
#                 Time zone: Asia/Tashkent (+05, +0500)
# System clock synchronized: yes
#               NTP service: active
#           RTC in local TZ: no
```

Four things to read: the **time zone**, whether the clock is
**synchronised**, whether an **NTP service** is running, and that the RTC
is **not** in local time (it should be UTC on any Linux-only machine).

```bash
timedatectl list-timezones | grep -i tashkent
sudo timedatectl set-timezone Asia/Tashkent
sudo timedatectl set-ntp true                 # enable the synchronisation service
sudo timedatectl set-time "2026-08-21 14:00:00"    # manual - only works with NTP disabled
sudo timedatectl set-local-rtc 0                    # keep the hardware clock in UTC
date; date -u; date -R; date +%s
```

The time zone is a symlink to a zoneinfo file:

```bash
ls -l /etc/localtime          # → /usr/share/zoneinfo/Asia/Tashkent
cat /etc/timezone             # Debian
TZ=UTC date                   # one command in another zone
```

## chrony: the recommended NTP client

```bash
sudo apt install chrony        # Debian/Ubuntu
sudo dnf install chrony        # RHEL
sudo systemctl enable --now chronyd     # (chrony on Debian)
```

```bash
sudo vi /etc/chrony/chrony.conf         # /etc/chrony.conf on RHEL
```

```
pool 2.pool.ntp.org iburst              # a pool of servers; iburst = sync fast at startup
server ntp1.example.com iburst prefer   # a specific server, preferred
driftfile /var/lib/chrony/chrony.drift
makestep 1.0 3                          # allow big step corrections during the first 3 updates
rtcsync                                 # keep the hardware clock in step
# allow 192.168.1.0/24                  # SERVE time to this network (making this host an NTP server)
# local stratum 10                      # serve even when we ourselves are unsynchronised
```

```bash
sudo systemctl restart chronyd
chronyc sources -v
# MS Name/IP address    Stratum Poll Reach LastRx Last sample
# ^* ntp1.example.com         2    6   377     21   +14us[  +18us] +/-   12ms
chronyc sourcestats
chronyc tracking                 # our offset, drift and stratum
chronyc -a makestep              # force an immediate step correction
chronyc ntpdata
```

In `chronyc sources`, the leading characters are the story: `^*` the
selected synchronisation source, `^+` an acceptable alternative, `^-`
excluded by the combining algorithm, `^?` unreachable. `Reach 377` (octal,
all eight bits) means the last eight polls all answered.

## systemd-timesyncd: the minimal client

Ubuntu's default when chrony is not installed. An SNTP client - it can
sync a clock but cannot serve time or discipline it as precisely.

```bash
systemctl status systemd-timesyncd
timedatectl show-timesync --all
sudo vi /etc/systemd/timesyncd.conf     # [Time] NTP=ntp1.example.com  FallbackNTP=...
sudo systemctl restart systemd-timesyncd
timedatectl timesync-status
```

Only one time daemon at a time: installing chrony usually masks
timesyncd, and running both makes them fight.

```bash
systemctl is-active chronyd systemd-timesyncd ntpd     # exactly one should be active
```

## Serving time to a LAN

```
# on the server, in chrony.conf
allow 192.168.1.0/24
local stratum 10
```

```bash
sudo systemctl restart chronyd
sudo firewall-cmd --permanent --add-service=ntp && sudo firewall-cmd --reload   # UDP 123
sudo ufw allow 123/udp
chronyc clients                       # who is asking us
# on the clients:  server 192.168.1.10 iburst
```

## The hardware clock

```bash
sudo hwclock --show                  # the RTC
sudo hwclock --systohc               # system → hardware (write the correct time to the RTC)
sudo hwclock --hctosys               # hardware → system
```

Keep the RTC in **UTC** (`set-local-rtc 0`) unless the machine dual-boots
Windows. A VM usually inherits the host's clock, so guest time drift is
often a host problem.

## Diagnosing

```bash
timedatectl                                   # "System clock synchronized: no" is the headline
chronyc tracking | grep -E "System time|Stratum|Leap"
chronyc sources
journalctl -u chronyd --since today
sudo ss -ulpn | grep 123
ping -c1 pool.ntp.org
sudo chronyd -Q 'pool pool.ntp.org iburst'    # one-shot: what offset would we get?
```

| Symptom | Cause |
|---|---|
| `System clock synchronized: no` | no NTP service running, or no reachable source |
| all sources `^?` | UDP 123 blocked outbound, or DNS failure resolving the pool |
| big offset that never corrects | the step is too large - `makestep`, or `chronyc -a makestep` |
| clock jumps around | two time daemons running at once |
| certificates "not yet valid" | the clock is behind - fix time first, then re-test TLS |
| time correct, logs in the wrong zone | the time zone, not the clock - `timedatectl set-timezone` |

:::exam-tip
Two asks: "set the time zone to X" → `timedatectl set-timezone X`, verified
with `timedatectl`; "configure the system to synchronise time with server
Y" → add `server Y iburst` to chrony.conf, restart chronyd, verify with
`chronyc sources` showing `^*` and `timedatectl` showing synchronised.
Do not set the clock by hand when NTP is meant to be running.
:::

## Check yourself

1. Name three things that break when a server's clock is wrong.
2. Which command shows whether the clock is synchronised, and which shows
   the sources and their state?
3. Why should only one time daemon be active, and how do you check?
