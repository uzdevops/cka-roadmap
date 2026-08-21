## /etc/fstab, field by field

```
UUID=9f8e7d6c-5b4a-...  /mnt/data  ext4  defaults,noatime  0  2
LABEL=backup            /backup    xfs   defaults          0  2
/dev/vg0/root           /          ext4  errors=remount-ro 0  1
/swapfile               none       swap  sw                0  0
tmpfs                   /tmp       tmpfs defaults,size=2G  0  0
//srv/share             /mnt/share cifs  credentials=/etc/cifs.cred,_netdev 0 0
```

| # | Field | Means |
|---|---|---|
| 1 | device | `UUID=`, `LABEL=`, a path, or a network source - **never `/dev/sdX`** in production |
| 2 | mount point | must **exist**; `none` for swap |
| 3 | type | `ext4`, `xfs`, `swap`, `tmpfs`, `nfs`, `cifs`, `auto` |
| 4 | options | comma-separated, no spaces (next lesson covers them) |
| 5 | dump | `0` - historical backup flag |
| 6 | **fsck order** | `0` never check, `1` **root only**, `2` everything else |

## Adding an entry safely

```bash
sudo blkid /dev/sdb1                       # get the UUID
sudo mkdir -p /mnt/data
sudo cp /etc/fstab /etc/fstab.bak          # always
echo 'UUID=9f8e7d6c-5b4a-... /mnt/data ext4 defaults 0 2' | sudo tee -a /etc/fstab
sudo mount -a                              # mount everything in fstab that is not mounted
findmnt /mnt/data
df -h /mnt/data
sudo systemctl daemon-reload               # systemd re-reads fstab into mount units
```

:::warning
An invalid fstab entry can stop the boot: systemd waits 90 seconds for the
device, then drops to **emergency mode**, which needs console access - not
SSH. Never reboot after editing fstab without running `sudo mount -a` (no
errors) or `findmnt --verify` first. On a remote machine with no console,
that check is the whole difference between a reboot and a site visit.
:::

```bash
sudo mount -a                     # any error here would be a boot failure
findmnt --verify                  # validates fstab: devices, mount points, options
findmnt --verify --verbose
```

If a device may be absent, `nofail` prevents the boot from blocking:

```
UUID=... /mnt/usb ext4 defaults,nofail,x-systemd.device-timeout=5 0 2
```

## Mount options you will use here

```
defaults                 # rw,suid,dev,exec,auto,nouser,async
noauto                   # do NOT mount at boot (mount it by hand later)
nofail                   # boot even if the device is missing
_netdev                  # wait for the network first (NFS, CIFS, iSCSI)
ro                       # read-only
noatime                  # do not update access times - a cheap performance win
user                     # allow a normal user to mount it
errors=remount-ro        # ext4: on error, remount read-only rather than continue
x-systemd.automount      # mount on first access instead of at boot
```

## Systemd mount units

systemd generates a `.mount` unit for every fstab line, and you can also
write them directly. The unit's name **must** match the mount point path:
`/mnt/data` → `mnt-data.mount`.

```ini
# /etc/systemd/system/mnt-data.mount
[Unit]
Description=Data volume
[Mount]
What=/dev/disk/by-uuid/9f8e7d6c-5b4a-...
Where=/mnt/data
Type=ext4
Options=defaults,noatime
[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mnt-data.mount
systemctl status mnt-data.mount
systemctl list-units --type=mount
```

An **automount** unit mounts on first access - good for rarely-used
network shares:

```ini
# /etc/systemd/system/mnt-data.automount
[Unit]
Description=Automount data
[Automount]
Where=/mnt/data
TimeoutIdleSec=300
[Install]
WantedBy=multi-user.target
```

## Mounting and unmounting by hand

```bash
sudo mount /mnt/data                 # fstab supplies the rest
sudo mount -o remount,ro /mnt/data   # change options without unmounting
sudo mount -o remount,rw /
sudo umount /mnt/data
sudo umount -l /mnt/data             # lazy: detach now, clean up when free
findmnt; findmnt -t ext4; mount | column -t
```

"Target is busy" on unmount:

```bash
sudo lsof +D /mnt/data | head        # which processes have files open there
sudo fuser -vm /mnt/data
sudo fuser -km /mnt/data             # kill them (careful)
cd /                                  # your own shell may be the culprit
```

## Bind mounts and tmpfs

```bash
sudo mount --bind /srv/data /var/www/data
# fstab:  /srv/data  /var/www/data  none  bind  0 0
sudo mount --rbind /srv /mnt/srv                       # recursive, includes submounts

sudo mount -t tmpfs -o size=1G tmpfs /mnt/scratch      # RAM-backed, empty at every boot
# fstab:  tmpfs /mnt/scratch tmpfs defaults,size=1G,mode=1777 0 0
```

A bind mount makes one directory visible in a second place - the answer to
"the application insists on `/var/www/data` but the disk is mounted at
`/srv/data`".

:::exam-tip
"Mount /dev/sdb1 at /mnt/data persistently" = create the directory, add an
fstab line **by UUID**, `mount -a`, verify with `findmnt` or `df -h`. Two
habits that save you: back up fstab first, and never leave the task
without a successful `mount -a`. If the task says "must not prevent
booting if the disk is absent", add `nofail`.
:::

## Check yourself

1. What are the six fstab fields, and what does the last one control?
2. Which command proves a new fstab entry will not break the next boot?
3. What is a bind mount for, and how is it written in fstab?
