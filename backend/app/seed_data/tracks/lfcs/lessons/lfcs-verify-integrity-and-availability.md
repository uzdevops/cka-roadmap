## "Is this system healthy?"

The objective is broad on purpose: check that resources are available
(disk, memory, CPU), that processes and services are running, and that
what is on disk is intact. This is the first five minutes on any machine
you are handed.

## Disk space and inodes

```bash
df -h                       # space per filesystem
df -h /var                  # one path's filesystem
df -i                       # INODES - a disk can be "full" with space free
du -sh /var/log             # how big is this tree
du -sh /var/* | sort -rh | head
du -xh /var --max-depth=1 | sort -rh    # -x: stay on one filesystem
ncdu /var                   # interactive, if installed
find / -xdev -type f -size +500M -exec ls -lh {} + 2>/dev/null
lsof +L1                    # deleted-but-open files still holding space
```

Two "full disk" failures look identical in an application log: **no space**
(`df -h` shows 100%) and **no inodes** (`df -i` shows 100%, usually
millions of tiny files in one directory). Check both.

## Memory and swap

```bash
free -h
#                total   used   free  shared  buff/cache  available
# Mem:            7.7G   2.1G   1.2G    250M        4.4G        5.1G
# Swap:           2.0G     0B   2.0G
```

Read **available**, not free: `buff/cache` is memory Linux is using as
cache and will hand back instantly. Swap in constant use (`si`/`so` in
`vmstat`) means real pressure.

```bash
vmstat 1 5                  # r b | swpd free buff cache | si so | bi bo | in cs | us sy id wa
cat /proc/meminfo | head -5
dmesg -T | grep -i "out of memory\|oom-killer"     # who got killed and why
ps aux --sort=-%mem | head -5
```

## CPU and load

```bash
uptime                      # load average 1/5/15 min
nproc                       # how many CPUs - the number to compare load against
top -b -n1 | head -15
mpstat 1 5                  # per-CPU, from the sysstat package
sar -u 1 5                  # historical too, if sysstat collection is on
```

`%wa` (I/O wait) high with low `%us` means the disk, not the CPU, is the
bottleneck.

## Services and processes

```bash
systemctl --failed                       # the single most informative command
systemctl is-active nginx sshd
systemctl list-units --type=service --state=running | head
ps -ef --forest | head -30
pgrep -a nginx
ss -tulpn                                # which ports are open and who holds them
ss -s                                    # socket summary
curl -sS -o /dev/null -w '%{http_code}\n' http://localhost/health
systemctl status myapp
journalctl -p err -b --no-pager | tail -20
```

## A quick health script

```bash
#!/bin/bash
echo "== uptime";        uptime
echo "== failed units";  systemctl --failed --no-legend
echo "== disk";          df -h -x tmpfs -x devtmpfs
echo "== inodes";        df -i -x tmpfs -x devtmpfs | awk 'NR==1 || $5+0 > 80'
echo "== memory";        free -h
echo "== top mem";       ps aux --sort=-%mem | head -4
echo "== recent errors"; journalctl -p err -b --no-pager | tail -10
```

## Filesystem integrity

```bash
sudo touch /forcefsck                  # legacy: force a check at next boot
sudo tune2fs -l /dev/sda1 | grep -i "mount count\|check"
sudo umount /dev/sdb1                  # NEVER fsck a mounted filesystem
sudo fsck -n /dev/sdb1                 # -n: report, change nothing
sudo fsck -y /dev/sdb1                 # answer yes to repairs
sudo xfs_repair /dev/sdb1              # XFS has its own tool (and cannot be checked while mounted)
sudo smartctl -H /dev/sda              # is the DRIVE failing? (smartmontools)
sudo smartctl -a /dev/sda | grep -i "reallocated\|pending"
sudo badblocks -sv /dev/sdb            # slow surface scan
```

:::warning
Running `fsck` on a **mounted** filesystem corrupts it. Unmount first, or
run from rescue mode / a live image. For the root filesystem, that means
`touch /forcefsck` and reboot, or boot into rescue.
:::

## File integrity

```bash
sha256sum -c SHA256SUMS               # verify downloads
rpm -Va                                # every changed file of every RPM package
sudo debsums -c                         # the Debian equivalent (install debsums)
sudo apt install aide && sudo aideinit  # a full file-integrity database and periodic checks
sudo aide --check
```

## Availability over time

```bash
uptime -s; last reboot | head          # has it been rebooting?
sar -q                                 # historical load (sysstat)
systemd-analyze                         # boot time
journalctl --since "24 hours ago" -p warning --no-pager | wc -l
```

:::exam-tip
Expect small, precise asks: "report the filesystem with the least free
space to a file", "list all failed services", "show how much memory is
available". The commands are `df -h`, `systemctl --failed`, `free -h` -
with redirection to the file the task names. And remember `df -i` when a
disk is "full" but `df -h` says otherwise.
:::

## Check yourself

1. Two different causes make a filesystem report "no space left". Which
   commands distinguish them?
2. In `free -h`, which column tells you how much memory is really
   usable, and why not `free`?
3. Why must a filesystem be unmounted before `fsck`, and how do you check
   the root filesystem?
