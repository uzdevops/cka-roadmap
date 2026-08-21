## LFCS mock exam 4

Two hours. Fifteen tasks, total 100. The last one before the real thing:
every domain, no hints, and three tasks that are deliberately
under-specified so you have to decide what "correct" means. Snapshot
first.

---

**1.** (7) A file `/root/records.csv` (create it with ten lines of
`name,dept,salary`) must be summarised: write to `/root/bydept.txt` each
department with the number of records, sorted by count, highest first.

**2.** (6) Extract every line from `/var/log/auth.log` (or the journal)
that records a failed authentication in the last 24 hours, into
`/root/failed.txt`, and put the count on the first line of
`/root/failed-count.txt`.

**3.** (7) Create a 2 GiB logical volume `lvbackup` in an existing or new
volume group, format it ext4, mount it at `/backup` persistently with
`nodev,nosuid`, and confirm the options are in effect.

**4.** (7) Take a snapshot of `lvbackup` named `lvbackup_snap` sized 500
MiB, mount it read-only at `/mnt/snap`, list its contents to
`/root/snap.txt`, then remove the snapshot.

**5.** (7) Write `/usr/local/bin/backup.sh` that creates
`/backup/etc-YYYY-MM-DD.tar.gz` from `/etc` and deletes archives older
than 7 days. Schedule it daily at 01:00 with a systemd timer (not cron),
and trigger one run manually to prove it works.

**6.** (7) Create users `dev1` and `dev2`, a group `devteam`, and a
directory `/srv/devteam` where both can create files, each can delete only
their **own** files, and files created inside belong to `devteam`.

**7.** (6) Configure password ageing for `dev1`: maximum 60 days, minimum
7, warning 10, and force a password change at the next login. Show `chage
-l dev1` in `/root/ageing.txt`.

**8.** (7) Configure the SSH server to listen on port 2222 **in addition
to** 22, ensuring the firewall (and SELinux, if enforcing) permits it.
Verify by connecting on the new port.

**9.** (7) Configure this host's second interface with a static address
and make the host reachable by the name `lab.local` from itself. Show the
resolution in `/root/resolve.txt`.

**10.** (7) A service must run at boot **after** the network is fully
online, as an unprivileged user, with a 10-second restart delay and a
memory cap of 256 MB. Create it (any long-running command) and show
`systemctl show` for the three relevant properties in `/root/unit.txt`.

**11.** (6) Identify the process using the most memory and the process
doing the most disk I/O right now, and record both, with PIDs, in
`/root/hogs.txt`.

**12.** (6) Set kernel parameters persistently: `vm.swappiness=10` and
`net.ipv4.tcp_syncookies=1`. Prove both are in effect after applying,
without rebooting.

**13.** (6) Give the group `auditors` (create it) read-only access to
every file under `/var/log`, now and for files created later, without
changing existing owners or groups.

**14.** (7) Archive `/srv` to `/root/srv-backup.tar.zst` (or `.tar.gz` if
zstd is unavailable), preserving ACLs and extended attributes, then verify
by listing the archive and by extracting one named file to `/tmp`.

**15.** (7) The system has an unmounted filesystem that should be mounted
at `/opt/extra` at boot but is not (arrange this: add an fstab entry that
is wrong - a bad UUID). Diagnose why `mount -a` fails, fix it, and record
the original error in `/root/fstab-error.txt`.

---

## After the four mocks

Add the scores. Comfortably above 66% **with time to spare** on the last
two means ready. Passing only by using every minute means the long tasks
(LVM, networking, systemd units) need drilling until they are mechanical.
A domain that failed in all four is the plan for the remaining days.

Then read the objectives list one final time and, for each line, say aloud
what you would type. Anything you cannot answer is the last thing to
study.

:::exam-tip
Tasks 6, 10 and 13 have more than one correct answer (SGID + sticky, or
ACLs; `After=network-online.target` with `Wants=`; default ACLs versus
group changes). The real exam is the same: it checks the **end state**, not
your method. Pick the approach you can execute correctly and verify - not
the cleverest one.
:::

## Check yourself

1. Which tasks did you solve in more than one way, and which way was
   faster?
2. Across four mocks, which domain scored lowest, and what is your plan
   for it?
3. Was your last mock above 66% with time left over?
