## What swap is for

Swap is disk space the kernel uses to hold memory pages it has decided not
to keep in RAM. It is not "extra RAM" - it is far slower - but it lets the
kernel evict rarely-used pages, absorbs short spikes, and is required for
hibernation. A machine with **no** swap and full RAM starts killing
processes with the OOM killer.

```bash
free -h
swapon --show
# NAME      TYPE      SIZE USED PRIO
# /swapfile file        2G   0B   -2
cat /proc/swaps
```

## A swap partition

```bash
sudo fdisk /dev/sdb              # n, +2G, t → 19 (Linux swap), w
sudo partprobe /dev/sdb
sudo mkswap /dev/sdb2
# Setting up swapspace version 1, size = 2 GiB
# no label, UUID=1a2b3c4d-...
sudo swapon /dev/sdb2            # activate now
swapon --show
free -h
```

Persist it by UUID:

```bash
sudo blkid /dev/sdb2
echo 'UUID=1a2b3c4d-... none swap sw 0 0' | sudo tee -a /etc/fstab
sudo swapoff /dev/sdb2 && sudo swapon -a      # test the fstab line without rebooting
```

## A swap file

Easier on a machine with no spare partition, and resizable.

```bash
sudo swapoff /swapfile 2>/dev/null
sudo fallocate -l 2G /swapfile                # or: dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile                      # REQUIRED - mkswap refuses a world-readable file
sudo mkswap /swapfile
sudo swapon /swapfile
swapon --show
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

`chmod 600` is not optional: swap holds process memory, and a readable
swap file is a readable copy of everything in it.

(On Btrfs, `fallocate` is not enough - the file must be created with
`btrfs filesystem mkswapfile` or with `chattr +C` on an empty file.)

## Removing or resizing

```bash
sudo swapoff /swapfile            # moves its pages back into RAM - needs free RAM, can take a while
sudo rm /swapfile
sudo sed -i '/swapfile/d' /etc/fstab

# resize = remove and recreate
sudo swapoff /swapfile && sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile \
  && sudo mkswap /swapfile && sudo swapon /swapfile
```

## How much, and how eagerly

| RAM | Common guidance |
|---|---|
| ≤ 2 GB | 2× RAM |
| 2-8 GB | = RAM |
| 8-64 GB | 4-8 GB (more only if hibernating) |
| > 64 GB | 4 GB, or none, unless hibernation |
| hibernation | **≥ RAM** |

Databases and latency-sensitive services often run with little or no swap
and rely on correct sizing instead; general-purpose servers do better with
some swap than with none.

```bash
sysctl vm.swappiness                    # 60 by default
sudo sysctl -w vm.swappiness=10         # prefer dropping cache over swapping - typical for servers
echo 'vm.swappiness = 10' | sudo tee /etc/sysctl.d/99-swap.conf
sudo sysctl --system
```

`vm.swappiness` is not "how much swap to use"; it is how readily the
kernel swaps anonymous pages rather than evicting page cache. 10 is a
sensible server value, 60 a desktop one, 1 the minimum-without-disabling.

## Priorities and several swaps

```bash
sudo swapon -p 10 /dev/sdb2         # higher priority is used first
# fstab:  UUID=... none swap sw,pri=10 0 0
swapon --show
```

Equal priorities on separate disks are used in parallel - a small
performance trick when swap is unavoidable.

## Reading the numbers

```bash
free -h
vmstat 1 5                 # si / so columns: pages swapped IN and OUT per second
# constant non-zero si/so = real memory pressure; a used-but-idle swap is fine
sudo smem -rs swap | head  # per-process swap usage, if smem is installed
for f in /proc/*/status; do awk '/^Name|^VmSwap/{printf "%s ", $2} END{print ""}' "$f"; done | sort -k2 -n | tail
dmesg -T | grep -i "out of memory"
```

**Swap used is not a problem; swap thrashing is.** A server with 500 MB of
swap in use and no I/O has simply parked idle pages. One with `si`/`so`
constantly non-zero is thrashing, and the answer is more RAM or less
workload, not more swap.

## zram, briefly

Compressed swap **in RAM** - faster than disk, effectively trading CPU for
memory. Default on some distributions and on low-RAM machines:

```bash
sudo apt install zram-tools
zramctl
```

:::exam-tip
"Create a 2 GB swap file and enable it at boot": `fallocate` → `chmod 600`
→ `mkswap` → `swapon` → fstab line → verify with `swapon --show` and
`free -h`. The two marks lost are the `chmod 600` and the fstab entry.
Test the fstab line with `swapoff -a && swapon -a` before you claim it is
persistent.
:::

## Check yourself

1. Why must a swap file be `chmod 600`, and what happens without it?
2. What does `vm.swappiness` actually control?
3. How do you tell healthy swap usage from a memory problem?
