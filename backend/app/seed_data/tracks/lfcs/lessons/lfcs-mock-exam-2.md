## LFCS mock exam 2

Two hours. Fifteen tasks, total 100. Harder than mock 1: LVM, NFS, SSH
hardening, a broken service to repair. You need `/dev/sdb` and `/dev/sdc`
(≥3 GB each). Snapshot first.

---

**1.** (8) Create an LVM stack on `/dev/sdb`: a physical volume, a volume
group `vgdata`, and a 1 GiB logical volume `lvfiles`. Format it xfs and
mount it persistently at `/mnt/files`.

**2.** (8) Extend `lvfiles` by 500 MiB **including its filesystem**, while
it stays mounted. Show `df -h /mnt/files` in `/root/lvsize.txt`.

**3.** (7) Add `/dev/sdc` to `vgdata` and show the resulting free space in
`/root/vgfree.txt`.

**4.** (7) Export `/srv/share` over NFS to the `192.168.122.0/24` network,
read-write, with root squashing, and verify with `showmount -e localhost`
written to `/root/exports.txt`.

**5.** (8) Harden SSH: disable root login, disable password
authentication, and set `MaxAuthTries` to 3. Do not break your own
session; verify with `sshd -T`.

**6.** (7) Create a user `svc_backup` that cannot log in interactively,
has no home directory, and whose account is locked.

**7.** (6) Grant the group `operators` (create it) the ability to run
`/usr/bin/systemctl restart nginx` as root **without a password**, and
nothing else.

**8.** (7) The service `brokenapp` fails to start (create it first:
a unit whose `ExecStart` points at `/usr/local/bin/brokenapp` which does
not exist). Diagnose it, create a working script, and get the service
running and enabled. Write the failing message you found to
`/root/broken.txt`.

**9.** (7) Configure `logrotate` for `/var/log/myapp/*.log` (create the
directory and a log file): rotate daily, keep 7, compress, and do not fail
if missing. Test with `logrotate -d`.

**10.** (6) Find all files in the system with the SUID bit set and write
the list to `/root/suid.txt`.

**11.** (7) Set a static IP on the secondary interface persistently:
address `192.168.150.10/24`, no gateway, DNS `1.1.1.1`. Show `ip -br a` in
`/root/ipbr.txt`.

**12.** (6) Configure `journald` so the journal is stored persistently
across reboots, and show `journalctl --disk-usage` in `/root/journal.txt`.

**13.** (7) Write a script `/usr/local/bin/diskcheck.sh` that exits 1 and
prints a warning if any mounted filesystem is above 80% used, and exits 0
otherwise. Make it executable and run it, saving output to
`/root/diskcheck.txt`.

**14.** (5) Set the default umask for all users to `027` system-wide.

**15.** (4) Create the file `/root/facts.txt` containing, one per line:
the kernel version, the number of CPU cores, and the total memory in MB.

---

:::exam-tip
Tasks 1-3 are one continuous LVM story and are worth 23 points together -
if `lvextend -r` is not automatic for you yet, that is where an hour of
drilling pays for itself. Task 8 is the shape of every troubleshooting
question: `systemctl status` → `journalctl -xeu` → the message names the
cause → fix → `daemon-reload` → `enable --now` → verify.
:::

## Check yourself

1. Which single command did tasks 2 and 3 need, and in what order do LVM
   operations go?
2. In task 5, how did you confirm the change without risking your
   session?
3. Which tasks required a `daemon-reload` or a `--reload`, and did you
   remember them?
