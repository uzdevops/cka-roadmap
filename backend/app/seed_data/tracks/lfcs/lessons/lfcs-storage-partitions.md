## Looking at the disks first

```bash
lsblk                      # the tree: disks, partitions, sizes, mount points
lsblk -f                   # + filesystem type, LABEL, UUID
sudo fdisk -l              # every disk and its partition table
sudo parted -l
cat /proc/partitions
sudo blkid                 # UUIDs and types of every block device
ls -l /dev/disk/by-uuid/ /dev/disk/by-id/
```

```
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
sda      8:0    0   40G  0 disk
├─sda1   8:1    0    1G  0 part /boot
├─sda2   8:2    0    1G  0 part /boot/efi
└─sda3   8:3    0   38G  0 part
  └─vg0-root 253:0 0 38G 0 lvm  /
sdb      8:16   0    5G  0 disk               ← a spare disk to practise on
```

Device names: `/dev/sda` (SATA/SCSI/USB), `/dev/vda` (virtio, in VMs),
`/dev/nvme0n1` (NVMe - partitions are `nvme0n1p1`), `/dev/sdb1` (first
partition of the second disk).

## GPT or MBR

| | MBR (msdos) | GPT |
|---|---|---|
| max disk | 2 TiB | 8 ZiB |
| partitions | 4 primary, or 3 + extended with logicals | 128 |
| boot | BIOS | UEFI (and BIOS with a bios_grub partition) |
| redundancy | one copy of the table | primary + backup |
| use | legacy only | **everything new** |

```bash
sudo parted /dev/sdb print | head -5      # "Partition Table: gpt"
```

## fdisk: interactive, GPT-aware

```bash
sudo fdisk /dev/sdb
```

| Key | Does |
|---|---|
| `m` | help |
| `p` | print the table |
| `g` | new **GPT** table (`o` for MBR) |
| `n` | new partition (number, first sector, last sector or `+2G`) |
| `d` | delete |
| `t` | change the type (`L` lists: 20 Linux filesystem, 19 swap, 30 Linux LVM, 1 EFI) |
| `w` | **write** and exit |
| `q` | quit **without** saving - the undo |

```
Command (m for help): g
Command (m for help): n
Partition number (1-128, default 1): 1
First sector (2048-10485726, default 2048): <Enter>
Last sector, +/-sectors or +/-size{K,M,G,T,P} (2048-10485726): +2G
Command (m for help): n            ← a second one, +1G, then t → 19 (swap)
Command (m for help): p
Command (m for help): w
```

Nothing is changed until `w`. That makes `q` a free escape from any
mistake.

## parted: scriptable

```bash
sudo parted /dev/sdb --script mklabel gpt
sudo parted /dev/sdb --script mkpart primary ext4 1MiB 2GiB
sudo parted /dev/sdb --script mkpart primary linux-swap 2GiB 3GiB
sudo parted /dev/sdb --script set 1 lvm on
sudo parted /dev/sdb --script print
sudo parted /dev/sdb --script rm 2
sudo parted /dev/sdb resizepart 1 100%          # grow a partition to fill the disk
```

`parted` writes **immediately** - there is no `q` to escape with. Use
`--script` for automation, and `MiB` units so partitions stay aligned.

## Telling the kernel

```bash
sudo partprobe /dev/sdb          # re-read the partition table
sudo partx -u /dev/sdb
sudo udevadm settle
lsblk /dev/sdb                    # the new partitions should appear
```

If the kernel refuses ("device or resource busy"), something on the disk
is mounted or in use - unmount it, or reboot.

## Partition types

The type is a hint, not enforcement, but tools read it:

```bash
sudo fdisk /dev/sdb            # t, then L to list
# 20  Linux filesystem     19  Linux swap
# 30  Linux LVM             1  EFI System
# 29  Linux RAID
sudo parted /dev/sdb set 1 lvm on
sudo parted /dev/sdb set 1 esp on
```

## Growing a partition

```bash
# after enlarging the virtual disk on the host:
sudo qemu-img resize /var/lib/libvirt/images/lab.qcow2 +10G     # (on the VM host)
lsblk                                            # the disk is bigger, the partition is not
sudo growpart /dev/sda 3                         # cloud-guest-utils - the easy way
# or: parted /dev/sda resizepart 3 100%
sudo pvresize /dev/sda3                          # if it holds an LVM PV
sudo lvextend -l +100%FREE -r /dev/vg0/root      # then the LV and its filesystem
df -h /
```

Three layers, three steps: **disk → partition → (PV/LV) → filesystem**.
Missing one is why "I made the disk bigger and nothing changed".

:::warning
Deleting or resizing a partition that holds data destroys it. Check
`lsblk`, `mount` and `blkid` before touching anything, work on a spare
disk while learning (`virsh attach-disk`), and take a snapshot of the VM
first. `wipefs -a /dev/sdb` erases every signature on a disk - fast, and
irreversible.
:::

:::exam-tip
"Create a 2 GiB partition on /dev/sdb and format it" → `fdisk` (`g`, `n`,
`+2G`, `w`) or `parted --script`, then `partprobe`, then `mkfs` (next
lesson), then verify with `lsblk -f`. Do not skip the type when the task
names one (swap, LVM), and always confirm the target device with `lsblk` -
the wrong device is the one unrecoverable mistake here.
:::

## Check yourself

1. Which command shows disks, partitions, filesystems and mount points in
   one tree?
2. In `fdisk`, what makes changes permanent and what discards them?
3. You enlarged a virtual disk but `df -h` is unchanged. Which layers
   still need action?
