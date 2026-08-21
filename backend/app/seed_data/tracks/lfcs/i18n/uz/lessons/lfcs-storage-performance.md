## Muammo diskdami?

"CPU storage’ni kutyapti" deydigan yagona raqamdan boshlang:

```bash
top       # CPU satridagi %wa (I/O wait) ko'rsatkichiga qarang
vmstat 1 5
# procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
#  r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
#  1  3      0 120000  20000 400000    0    0  4200  8600  900 1800  5  3 12 80  0
```

`b` (I/O’da bloklangan jarayonlar) noldan yuqori va `wa` baland bo’lsa,
bo’g’iz - storage. Ayni paytda `si`/`so` noldan farqli bo’lsa, I/O’ni
swapping *keltirib chiqaryapti* - avval xotirani tuzating.

## iostat: qurilma bo’yicha raqamlar

```bash
sudo apt install sysstat
iostat -xz 1                    # kengaytirilgan statistika, bo'sh qurilmalarni tashlab, har soniyada
```

```
Device   r/s    w/s     rkB/s    wkB/s  r_await w_await aqu-sz  %util
sda     12.0   340.0    480.0  27000.0     0.8    45.2   14.2   99.6
```

| Ustun | Ma’nosi |
|---|---|
| `r/s`, `w/s` | soniyasiga o’qish va yozishlar (IOPS) |
| `rkB/s`, `wkB/s` | throughput |
| `r_await`, `w_await` | **ms dagi o’rtacha latency**, navbatda turgan vaqt bilan birga |
| `aqu-sz` | o’rtacha navbat chuqurligi - nechta so’rov kutyapti |
| `%util` | qurilmada kamida bitta so’rov ishlanayotgan vaqt ulushi |

Ularni o’qish: SSD’da ~10 ms dan yuqori `await` shubhali; aylanadigan
disklarda yuk ostida ~20 ms normal. `%util` 100 ga yaqin bo’lib, **navbat
uzun** va `await` o’sib borayotgan bo’lsa - bu to’yinish. NVMe va RAID’da
`%util` yolg’iz o’zi aldaydi - bunday qurilmalar ko’p so’rovni parallel
bajaradi, shuning uchun 0.3 ms await bilan 100% util mutlaqo sog’lom.
**Latency va navbat chuqurligi birgalikda** - halol signal.

```bash
iostat -xz 1 5
iostat -d -m 2                 # MB'da
iostat -p sda 1                # partition'lar bilan birga
```

## Buni qaysi jarayon qilyapti

```bash
sudo iotop -o                  # faqat haqiqatan I/O qilayotgan jarayonlar
sudo iotop -oPa                # jamlangan holda, jarayon bo'yicha
sudo pidstat -d 1              # jarayon bo'yicha disk statistikasi (sysstat)
sudo iotop -obtqqq -n 5 >> /var/log/io.log     # logga yozish uchun
```

```
  TID  PRIO  USER   DISK READ  DISK WRITE  COMMAND
 1234  be/4  postgres  0.00 B/s  12.5 M/s  postgres: writer
```

`pidstat -d` skript yozishga qulayi; `iotop` esa root’ni va kernel’ning
task I/O accounting’ini talab qiladi.

## Joy va fayllar qayerda

```bash
df -h; df -i                                     # joy va inode'lar
du -xh /var --max-depth=1 | sort -rh | head
sudo find / -xdev -size +500M -type f -exec ls -lh {} + 2>/dev/null | sort -k5 -rh | head
sudo lsof +L1                                     # o'chirilgan, lekin hali ochiq turgan fayllar
```

## Latency va throughput testlari

```bash
sudo hdparm -tT /dev/sda                # tezkor ketma-ket o'qish (cache'dan va buferlangan)
sudo dd if=/dev/zero of=/mnt/data/testfile bs=1M count=1024 oflag=direct status=progress   # ketma-ket yozish
sudo dd if=/mnt/data/testfile of=/dev/null bs=1M iflag=direct status=progress               # ketma-ket o'qish
sudo rm /mnt/data/testfile
```

```bash
sudo apt install fio
fio --name=randread --filename=/mnt/data/fio.tmp --size=1G --rw=randread \
    --bs=4k --iodepth=32 --direct=1 --runtime=30 --time_based --group_reporting
fio --name=seqwrite --filename=/mnt/data/fio.tmp --size=1G --rw=write \
    --bs=1M --direct=1 --runtime=30 --time_based
```

`--direct=1` page cache’ni chetlab o’tadi - usiz siz RAM’ni o’lchaysiz.
`oflag=direct` siz ishlatilgan `dd` xuddi shu sababdan bema’ni tez
raqamlarni qaytaradi.

## Navbatlar va scheduler’lar

```bash
cat /sys/block/sda/queue/scheduler
# [none] mq-deadline kyber bfq
echo mq-deadline | sudo tee /sys/block/sda/queue/scheduler       # hozir
cat /sys/block/sda/queue/nr_requests
cat /sys/block/sda/queue/rotational        # 1 = aylanadigan disk, 0 = SSD
```

| Scheduler | Nima uchun |
|---|---|
| `none` | NVMe va tez SSD’lar - driver navbatni kernel’dan yaxshiroq tuzadi |
| `mq-deadline` | umumiy maqsad, latency chegaralangan |
| `bfq` | desktop’lar va interaktivlik |
| `kyber` | latency maqsadi bo’lgan tez qurilmalar |

udev qoidasi bilan doimiy qilish:

```
# /etc/udev/rules.d/60-scheduler.rules
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="bfq"
ACTION=="add|change", KERNEL=="nvme[0-9]n[0-9]", ATTR{queue/scheduler}="none"
```

## Arzon yutuqlar

```bash
# mount option'lari
sudo mount -o remount,noatime /mnt/data          # kamroq metadata yozuvi
# SSD trim - `discard` mount option'i o'rniga haftalik timer'ni afzal ko'ring
sudo systemctl enable --now fstrim.timer
sudo fstrim -av
# ko'p yozadigan hostlar uchun writeback tuning'i
sysctl vm.dirty_ratio vm.dirty_background_ratio
sudo sysctl -w vm.dirty_background_ratio=5 -w vm.dirty_ratio=15
# ketma-ket workload'lar uchun readahead
sudo blockdev --getra /dev/sda; sudo blockdev --setra 4096 /dev/sda
```

## Hardware ishdan chiqyaptimi?

Xatolar bilan birga kelgan sekin I/O - bu tuning muammosi emas:

```bash
sudo smartctl -H /dev/sda
sudo smartctl -a /dev/sda | grep -iE "reallocated|pending|uncorrectable|error"
sudo smartctl -t short /dev/sda && sleep 120 && sudo smartctl -l selftest /dev/sda
dmesg -T | grep -iE "i/o error|ata|nvme|reset"
cat /proc/mdstat                                  # degradatsiyaga uchragan RAID massivi tabiatan sekin
```

## Besh daqiqalik tartib

```bash
uptime                                   # yuk, va u yangimi?
vmstat 1 5                               # b va wa ustunlari, si/so
iostat -xz 1 5                           # qaysi qurilma, qanday latency, qanday navbat
sudo iotop -o                            # qaysi jarayon
df -h; df -i                             # shunchaki to'lib ketganmi?
sudo dmesg -T | tail -20                  # xatolar, reset'lar, OOM
```

:::exam-tip
Maqsad - "monitoring", shuning uchun ehtimoliy so’rov: vositani ishga
tushirib, chiqishini saqlash: `iostat -xz 1 5 > /root/io.txt`, `df -h`,
`du -sh`, `iotop -b -n 3`. `iostat` bo’lmasa, `sysstat` ni o’rnating.
`%util`, `await` va `wa` ustuni nimani anglatishini **qaysi** qurilma
band va u to’yinganmi yoki yo’qmi - shuni ayta oladigan darajada biling.
:::

## O’zingizni tekshiring

1. `vmstat` ning qaysi ikkita ustuni "CPU storage’ni kutyapti" deydi?
2. Nega NVMe’da `%util` chalg’itadi va uning o’rniga qaysi raqamlarni
   o’qish kerak?
3. Diskni o’lchayotganda nega `dd` va `fio` direct I/O ishlatishi shart?
