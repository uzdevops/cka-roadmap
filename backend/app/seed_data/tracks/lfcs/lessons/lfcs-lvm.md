## Three layers

LVM inserts an abstraction between disks and filesystems, so that storage
can be resized, moved and combined without repartitioning.

```
 /dev/sdb1  /dev/sdc1        ← PV  physical volumes (partitions or whole disks)
        └────┬────┘
          vg0              ← VG  volume group: one pool of extents
        ┌───┴────┬───────┐
     lv_data  lv_logs  lv_home    ← LV  logical volumes: what you format and mount
```

| Term | Is |
|---|---|
| **PV** | a block device given to LVM |
| **VG** | a pool made of PVs, divided into **PE** (physical extents, 4 MiB by default) |
| **LV** | a slice of the pool, used like a partition |

Why it is worth the extra layer: an LV can be **grown while mounted**,
extended across a new disk, snapshotted, and moved to different hardware
without downtime.

## Building the stack

```bash
sudo apt install lvm2
sudo pvcreate /dev/sdb1 /dev/sdc1
sudo vgcreate vg0 /dev/sdb1 /dev/sdc1
sudo lvcreate -L 2G -n lv_data vg0
sudo mkfs.ext4 /dev/vg0/lv_data
sudo mkdir -p /mnt/data && sudo mount /dev/vg0/lv_data /mnt/data
```

Sizes:

```bash
sudo lvcreate -L 500M  -n lv_logs vg0        # absolute
sudo lvcreate -l 100   -n lv_x    vg0        # 100 extents
sudo lvcreate -l 50%FREE -n lv_y  vg0        # half of what is free
sudo lvcreate -l 100%FREE -n lv_z vg0        # everything left
```

The device appears as both `/dev/vg0/lv_data` and `/dev/mapper/vg0-lv_data`
- use either in fstab (they are stable names, unlike `/dev/sdX`).

## Inspecting

```bash
pvs; vgs; lvs                      # the quick tables
sudo pvdisplay; sudo vgdisplay; sudo lvdisplay      # verbose
sudo vgdisplay vg0 | grep -E "Free|PE Size|Total PE"
lsblk
sudo pvs -o+pv_used
sudo lvs -o+lv_size,seg_size,devices
```

## Growing - the everyday operation

```bash
sudo vgs                                       # is there free space in the VG?
sudo lvextend -L +5G /dev/vg0/lv_data          # add 5 GiB
sudo lvextend -L 20G /dev/vg0/lv_data          # grow TO 20 GiB
sudo lvextend -l +100%FREE /dev/vg0/lv_data    # take all remaining space
sudo resize2fs /dev/vg0/lv_data                # ext4: grow the filesystem, online
sudo xfs_growfs /mnt/data                      # xfs: grow the filesystem, must be mounted
```

Or both steps in one, which is what you should type:

```bash
sudo lvextend -r -L +5G /dev/vg0/lv_data       # -r resizes the filesystem too, ext4 or xfs
df -h /mnt/data
```

No free space in the VG? Add a disk:

```bash
sudo pvcreate /dev/sdd1
sudo vgextend vg0 /dev/sdd1
sudo vgs
sudo lvextend -r -l +100%FREE /dev/vg0/lv_data
```

## Shrinking - ext4 only, and offline

```bash
sudo umount /mnt/data
sudo e2fsck -f /dev/vg0/lv_data          # required before a shrink
sudo resize2fs /dev/vg0/lv_data 5G       # filesystem FIRST
sudo lvreduce -L 5G /dev/vg0/lv_data     # then the LV
sudo mount /dev/vg0/lv_data /mnt/data
# or, both at once:
sudo lvreduce -r -L 5G /dev/vg0/lv_data
```

:::warning
Growing: LV first, then filesystem. **Shrinking: filesystem first, then
LV.** Reducing the LV below the filesystem's size destroys data, and
`lvreduce` will warn but still do it if you confirm. XFS **cannot be
shrunk at all** - back up, recreate smaller, restore.
:::

## Removing

```bash
sudo umount /mnt/data
sudo lvremove /dev/vg0/lv_data
sudo vgreduce vg0 /dev/sdc1          # take a PV out of the VG (move data off it first)
sudo pvmove /dev/sdc1                # migrate extents off a disk, ONLINE - how you retire a failing disk
sudo pvremove /dev/sdc1
sudo vgremove vg0
```

`pvmove` is LVM's best trick: with the filesystem mounted and in use, move
every extent off one disk onto the others, then pull it out.

## Snapshots

```bash
sudo lvcreate -L 1G -s -n data_snap /dev/vg0/lv_data      # a copy-on-write snapshot
sudo mount -o ro /dev/vg0/data_snap /mnt/snap             # back it up from here, consistently
sudo lvs                                                   # watch the Data% column
sudo lvconvert --merge /dev/vg0/data_snap                  # ROLL BACK to the snapshot
sudo lvremove /dev/vg0/data_snap
```

A snapshot stores only changed blocks. If it **fills up** it is dropped and
becomes invalid, so size it for the expected churn and remove it when the
backup is done. Snapshots are not backups - they live on the same disks.

## Persisting

```bash
sudo blkid /dev/vg0/lv_data
echo '/dev/vg0/lv_data /mnt/data ext4 defaults 0 2' | sudo tee -a /etc/fstab
sudo mount -a && findmnt /mnt/data
```

LVM device names are stable, so `/dev/vg0/lv_data` is acceptable in fstab -
UUID works too.

## Diagnosing

```bash
sudo vgs -o+vg_free; sudo lvs -o+lv_size
sudo pvck /dev/sdb1
sudo vgscan; sudo vgchange -ay              # activate volume groups (after moving disks in)
sudo lvchange -ay /dev/vg0/lv_data
sudo vgcfgrestore -l vg0                     # metadata backups in /etc/lvm/archive - recovery from a bad change
sudo dmsetup ls
```

| Symptom | Cause |
|---|---|
| `Insufficient free space` on lvextend | the VG is full - `vgextend` with a new PV |
| LV grown, `df` unchanged | the filesystem was not resized - `resize2fs`/`xfs_growfs`, or use `-r` |
| LVs missing after moving disks | `vgscan` + `vgchange -ay` |
| `Device /dev/sdb1 excluded by a filter` | already has a signature - `wipefs -a`, or check `/etc/lvm/lvm.conf` filters |
| snapshot invalid | it filled up |

:::exam-tip
The classic task: "extend logical volume X by N GB including its
filesystem". One command: `lvextend -r -L +NG /dev/vgX/lvX`, verified with
`lvs` and `df -h`. If the VG has no free space, the full sequence is
`pvcreate` → `vgextend` → `lvextend -r`. Know the shrink order too - it is
the question that separates people who memorised a command from people who
understand the layers.
:::

## Check yourself

1. What are PV, VG and LV, and which one do you format?
2. Give the order of operations for growing, and for shrinking, an ext4
   filesystem on an LV.
3. Which command moves data off a failing disk while everything stays
   mounted?
