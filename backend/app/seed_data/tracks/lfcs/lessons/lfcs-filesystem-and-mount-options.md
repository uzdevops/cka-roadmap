## Options change what a filesystem allows

The fourth fstab field, and `mount -o`. Some are performance, some are
security, and a few are the standard answer to an audit finding.

```bash
findmnt                       # every mount with its options
findmnt /mnt/data -o TARGET,SOURCE,FSTYPE,OPTIONS
mount | grep /mnt/data
cat /proc/mounts              # the kernel's view - the authoritative one
```

## The security three

| Option | Effect |
|---|---|
| `noexec` | no binary on this filesystem may be **executed** |
| `nosuid` | SUID/SGID bits are **ignored** here |
| `nodev` | device nodes on this filesystem are **not honoured** |

```
UUID=... /home     ext4  defaults,nodev,nosuid          0 2
UUID=... /var/log  ext4  defaults,nodev,nosuid,noexec   0 2
UUID=... /tmp      ext4  defaults,nodev,nosuid,noexec   0 2
tmpfs    /dev/shm  tmpfs defaults,nodev,nosuid,noexec   0 0
```

`/tmp`, `/var/tmp`, `/dev/shm` and `/home` with `noexec,nosuid,nodev` is
the classic hardening set: a script dropped in `/tmp` cannot be run, and a
SUID binary planted there grants nothing. (Some package managers build in
`/tmp` and will complain - `/var/tmp` or a build directory elsewhere is
the fix.)

## Performance and behaviour

| Option | Effect |
|---|---|
| `noatime` | never update access times - fewer writes, safe for almost everything |
| `relatime` | update atime only if older than mtime (the modern **default**) |
| `nodiratime` | as noatime, directories only |
| `async` / `sync` | buffer writes (default) / write through immediately (slow, safer) |
| `discard` | issue TRIM to SSDs on delete (prefer the weekly `fstrim.timer`) |
| `errors=remount-ro` | ext4: on an error, go read-only rather than continue corrupting |
| `barrier=1` | write barriers on (default; do not disable without a battery-backed controller) |
| `data=ordered\|writeback\|journal` | ext4 journalling mode: safety versus speed |

## Access and mounting behaviour

| Option | Effect |
|---|---|
| `ro` / `rw` | read-only / read-write |
| `auto` / `noauto` | mounted by `mount -a` (and at boot) or not |
| `user` / `nouser` | may a normal user mount it (implies noexec,nosuid,nodev) |
| `owner` | only the device's owner may mount it |
| `nofail` | do not fail the boot if the device is missing |
| `_netdev` | wait for the network before mounting |
| `x-systemd.automount` | mount on first access |
| `x-systemd.device-timeout=5` | how long to wait for the device |
| `defaults` | `rw,suid,dev,exec,auto,nouser,async` |

## Ownership options for filesystems without Unix permissions

vfat, exfat, ntfs and most network shares cannot store Unix ownership, so
it is set at mount time:

```
/dev/sdc1 /mnt/usb vfat uid=1000,gid=1000,umask=022,noexec,nosuid,nodev 0 0
//srv/share /mnt/share cifs credentials=/etc/cifs.cred,uid=1000,gid=1000,_netdev 0 0
```

```bash
sudo mount -o uid=1000,gid=1000,umask=077 /dev/sdc1 /mnt/usb
```

## Changing options without unmounting

```bash
sudo mount -o remount,ro /mnt/data
sudo mount -o remount,rw /mnt/data
sudo mount -o remount,noexec /tmp
sudo mount -o remount,rw /                    # the emergency-mode first command
findmnt /tmp -o OPTIONS                        # confirm
```

A `remount` does not read fstab for the **device**, only for defaults - so
always verify with `findmnt` afterwards, and update fstab too or the change
disappears at the next boot.

## Quotas, briefly

```bash
sudo apt install quota
# fstab:  UUID=... /home ext4 defaults,usrquota,grpquota 0 2
sudo mount -o remount /home
sudo quotacheck -cugm /home
sudo quotaon -v /home
sudo edquota -u alice                # soft/hard limits for blocks and inodes
sudo setquota -u alice 500000 600000 0 0 /home
sudo repquota -a                     # report
quota -u alice
```

XFS uses `uquota`/`gquota` and `xfs_quota` instead. Quotas are how you
stop one user filling `/home` for everyone.

## Checking what is in effect

```bash
findmnt -o TARGET,SOURCE,FSTYPE,OPTIONS
cat /proc/mounts | grep /tmp
mount | grep noexec
findmnt --verify                          # fstab sanity
sudo touch /tmp/x.sh && chmod +x /tmp/x.sh && /tmp/x.sh    # "Permission denied" proves noexec works
```

`/proc/mounts` shows the **kernel's** options, including defaults you did
not write; `/etc/fstab` shows your intent. When they disagree, someone
remounted by hand.

:::exam-tip
"Mount X at Y so that binaries cannot be executed from it" → add `noexec`
to the fstab options, `mount -o remount` (or `mount -a` after unmounting),
and prove it by trying to run something. Know the security three
(`noexec,nosuid,nodev`), `ro`, `nofail`, `_netdev` and `noatime` by heart -
they cover essentially every option task.
:::

## Check yourself

1. What do `noexec`, `nosuid` and `nodev` each prevent, and where are they
   typically applied?
2. How do you make a mounted filesystem read-only without unmounting it,
   and what else must you do to keep it that way?
3. Why do vfat and CIFS mounts need `uid=`/`gid=` options?
