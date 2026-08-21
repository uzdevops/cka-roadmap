## Is the disk the problem?

Start with the one number that says "the CPU is waiting for storage":

```bash
top       # look at the %wa (I/O wait) figure in the CPU line
vmstat 1 5
# procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
#  r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
#  1  3      0 120000  20000 400000    0    0  4200  8600  900 1800  5  3 12 80  0
```

`b` (processes blocked on I/O) above zero and `wa` high means storage is
the bottleneck. `si`/`so` non-zero at the same time means swapping is
*causing* the I/O - fix memory first.

## iostat: per-device numbers

```bash
sudo apt install sysstat
iostat -xz 1                    # extended stats, skip idle devices, every second
```

```
Device   r/s    w/s     rkB/s    wkB/s  r_await w_await aqu-sz  %util
sda     12.0   340.0    480.0  27000.0     0.8    45.2   14.2   99.6
```

| Column | Means |
|---|---|
| `r/s`, `w/s` | reads and writes per second (IOPS) |
| `rkB/s`, `wkB/s` | throughput |
| `r_await`, `w_await` | **average latency in ms**, including queue time |
| `aqu-sz` | average queue depth - how many requests are waiting |
| `%util` | share of time the device had at least one request in flight |

Reading them: on an SSD, `await` above ~10 ms is suspicious; on spinning
disks, ~20 ms is normal under load. `%util` near 100 with a **long queue**
and rising `await` is saturation. On NVMe and RAID, `%util` alone lies -
those devices serve many requests in parallel, so 100% util with 0.3 ms
await is perfectly healthy. **Latency plus queue depth** is the honest
signal.

```bash
iostat -xz 1 5
iostat -d -m 2                 # in MB
iostat -p sda 1                # including partitions
```

## Which process is doing it

```bash
sudo iotop -o                  # only processes actually doing I/O
sudo iotop -oPa                # accumulated, per process
sudo pidstat -d 1              # per-process disk stats (sysstat)
sudo iotop -obtqqq -n 5 >> /var/log/io.log     # for logging
```

```
  TID  PRIO  USER   DISK READ  DISK WRITE  COMMAND
 1234  be/4  postgres  0.00 B/s  12.5 M/s  postgres: writer
```

`pidstat -d` is the scriptable one; `iotop` needs root and the kernel's
task I/O accounting.

## Where the space and the files are

```bash
df -h; df -i                                     # space and inodes
du -xh /var --max-depth=1 | sort -rh | head
sudo find / -xdev -size +500M -type f -exec ls -lh {} + 2>/dev/null | sort -k5 -rh | head
sudo lsof +L1                                     # deleted files still held open
```

## Latency and throughput tests

```bash
sudo hdparm -tT /dev/sda                # quick sequential read (cached and buffered)
sudo dd if=/dev/zero of=/mnt/data/testfile bs=1M count=1024 oflag=direct status=progress   # sequential write
sudo dd if=/mnt/data/testfile of=/dev/null bs=1M iflag=direct status=progress               # sequential read
sudo rm /mnt/data/testfile
```

```bash
sudo apt install fio
fio --name=randread --filename=/mnt/data/fio.tmp --size=1G --rw=randread \
    --bs=4k --iodepth=32 --direct=1 --runtime=30 --time_based --group_reporting
fio --name=seqwrite --filename=/mnt/data/fio.tmp --size=1G --rw=write \
    --bs=1M --direct=1 --runtime=30 --time_based
```

`--direct=1` bypasses the page cache - without it you are measuring RAM.
`dd` without `oflag=direct` returns absurdly fast numbers for the same
reason.

## Queues and schedulers

```bash
cat /sys/block/sda/queue/scheduler
# [none] mq-deadline kyber bfq
echo mq-deadline | sudo tee /sys/block/sda/queue/scheduler       # now
cat /sys/block/sda/queue/nr_requests
cat /sys/block/sda/queue/rotational        # 1 = spinning disk, 0 = SSD
```

| Scheduler | For |
|---|---|
| `none` | NVMe and fast SSDs - the driver queues better than the kernel can |
| `mq-deadline` | general purpose, latency-bounded |
| `bfq` | desktops and interactivity |
| `kyber` | fast devices with latency targets |

Persist with a udev rule:

```
# /etc/udev/rules.d/60-scheduler.rules
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="bfq"
ACTION=="add|change", KERNEL=="nvme[0-9]n[0-9]", ATTR{queue/scheduler}="none"
```

## Cheap wins

```bash
# mount options
sudo mount -o remount,noatime /mnt/data          # fewer metadata writes
# SSD trim - prefer the weekly timer over the `discard` mount option
sudo systemctl enable --now fstrim.timer
sudo fstrim -av
# writeback tuning for write-heavy hosts
sysctl vm.dirty_ratio vm.dirty_background_ratio
sudo sysctl -w vm.dirty_background_ratio=5 -w vm.dirty_ratio=15
# readahead for sequential workloads
sudo blockdev --getra /dev/sda; sudo blockdev --setra 4096 /dev/sda
```

## Is the hardware dying?

Slow I/O with errors is not a tuning problem:

```bash
sudo smartctl -H /dev/sda
sudo smartctl -a /dev/sda | grep -iE "reallocated|pending|uncorrectable|error"
sudo smartctl -t short /dev/sda && sleep 120 && sudo smartctl -l selftest /dev/sda
dmesg -T | grep -iE "i/o error|ata|nvme|reset"
cat /proc/mdstat                                  # a degraded RAID array is slow by design
```

## A five-minute routine

```bash
uptime                                   # load, and is it new?
vmstat 1 5                               # b and wa columns, si/so
iostat -xz 1 5                           # which device, what latency, what queue
sudo iotop -o                            # which process
df -h; df -i                             # is it simply full?
sudo dmesg -T | tail -20                  # errors, resets, OOM
```

:::exam-tip
The objective is "monitor", so the likely asks are to run a tool and save
its output: `iostat -xz 1 5 > /root/io.txt`, `df -h`, `du -sh`,
`iotop -b -n 3`. Install `sysstat` if `iostat` is missing. Know what
`%util`, `await` and the `wa` column mean well enough to say **which**
device is busy and whether it is saturated.
:::

## Check yourself

1. Which two columns of `vmstat` say "the CPU is waiting for storage"?
2. Why is `%util` misleading on NVMe, and which numbers should you read
   instead?
3. Why must `dd` and `fio` use direct I/O when measuring a disk?
