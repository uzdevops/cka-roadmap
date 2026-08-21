## LFCS mock exam 1

Two hours. Fifteen tasks, weights in brackets, total 100. Ubuntu LTS VM
with a spare disk (`/dev/sdb`, ≥5 GB) attached. Snapshot first. `man` only.

---

**1.** (5) Create a user `jdoe` with home directory `/home/jdoe`, shell
`/bin/bash`, full name "John Doe", and an account expiry date of
`2027-01-31`.

**2.** (5) Create a group `analysts` and make `jdoe` a member of it
without removing any of their existing groups.

**3.** (6) Create the directory `/srv/analytics` owned by group
`analysts`, writable by the group, inaccessible to others, and such that
every file created inside it is group-owned by `analysts`.

**4.** (7) Find every file under `/var/log` larger than 1 MB that was
modified in the last 7 days, and write the list to `/root/biglogs.txt`.

**5.** (6) Create a hard link `/root/hosts.hard` and a symbolic link
`/root/hosts.soft`, both to `/etc/hosts`. Show, in `/root/links.txt`, the
inode of the hard link and the target of the soft link.

**6.** (8) Create a 1 GiB partition on `/dev/sdb`, format it ext4 with the
label `data01`, and mount it **persistently** at `/mnt/data01` with the
`noexec` option.

**7.** (7) Create a 512 MiB swap **file** at `/swapextra`, enable it, and
make it persistent.

**8.** (8) Create a systemd service named `heartbeat` that runs
`/usr/local/bin/heartbeat.sh` (write it: append the date to
`/var/log/heartbeat.log` every run), as user `nobody`, restarting on
failure. Enable and start it.

**9.** (6) Schedule `/usr/local/bin/heartbeat.sh` to run every 10 minutes
for user `root` via cron, logging output to `/var/log/heartbeat-cron.log`.

**10.** (7) Configure the system to forward IPv4 packets, **persistently**,
and show the effective value in `/root/forward.txt`.

**11.** (7) Install `nginx`, make sure it starts at boot, and confirm it
is listening on port 80. Write the relevant `ss` output to
`/root/nginx-port.txt`.

**12.** (8) Allow inbound SSH and HTTP through the firewall, deny
everything else inbound, and make the configuration persistent. Do not
lock yourself out.

**13.** (8) Set the system time zone to `Asia/Tashkent` and ensure time is
synchronised by an NTP service. Write `timedatectl` output to
`/root/time.txt`.

**14.** (6) Give user `jdoe` read and write access to the file
`/srv/analytics/report.txt` (create it) using an ACL, without changing its
owner or group.

**15.** (6) Create a tar archive `/root/etc-backup.tar.gz` containing
`/etc/ssh` and `/etc/hosts`, compressed with gzip, and verify its contents
without extracting.

---

Score, then the review quiz. Anything below full marks: the lesson and its
lab, same day.

:::exam-tip
Six of these fifteen require **persistence** (6, 7, 8, 9, 10, 12, 13). If
you finished them all in under two hours but skipped an fstab line or a
`systemctl enable`, your real score is far below what it felt like. Verify
persistence explicitly: `mount -a`, `swapon --show`, `systemctl
is-enabled`, `sysctl <key>`, `ufw status`.
:::

## Check yourself

1. Which tasks did you skip on the first pass, and did you return to
   them?
2. For each task you completed, what single command proved the end state?
3. Which task took the longest, and was it knowledge, `man` navigation, or
   typing speed?
