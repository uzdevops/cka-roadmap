## Swap nima uchun kerak

Swap - bu kernel RAM’da saqlamaslikka qaror qilgan xotira page’larini
turg’azib turadigan disk maydoni. Bu "qo’shimcha RAM" emas - u ancha
sekin - lekin kernel’ga kam ishlatiladigan page’larni chiqarib yuborish
imkonini beradi, qisqa cho’qqilarni yutadi va hibernation uchun shart.
Swap’i **yo’q** va RAM’i to’lgan mashina OOM killer bilan process’larni
o’ldira boshlaydi.

```bash
free -h
swapon --show
# NAME      TYPE      SIZE USED PRIO
# /swapfile file        2G   0B   -2
cat /proc/swaps
```

## Swap partition

```bash
sudo fdisk /dev/sdb              # n, +2G, t → 19 (Linux swap), w
sudo partprobe /dev/sdb
sudo mkswap /dev/sdb2
# Setting up swapspace version 1, size = 2 GiB
# no label, UUID=1a2b3c4d-...
sudo swapon /dev/sdb2            # hozir yoqish
swapon --show
free -h
```

Uni UUID orqali doimiy qiling:

```bash
sudo blkid /dev/sdb2
echo 'UUID=1a2b3c4d-... none swap sw 0 0' | sudo tee -a /etc/fstab
sudo swapoff /dev/sdb2 && sudo swapon -a      # fstab qatorini reboot qilmasdan sinash
```

## Swap fayl

Bo’sh partition’i yo’q mashinada osonroq va o’lchamini o’zgartirsa bo’ladi.

```bash
sudo swapoff /swapfile 2>/dev/null
sudo fallocate -l 2G /swapfile                # yoki: dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile                      # SHART - mkswap hamma o'qiy oladigan faylni rad etadi
sudo mkswap /swapfile
sudo swapon /swapfile
swapon --show
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

`chmod 600` ixtiyoriy emas: swap process xotirasini saqlaydi, o’qib
bo’ladigan swap fayl esa - undagi hamma narsaning o’qib bo’ladigan
nusxasi.

(Btrfs’da `fallocate` yetarli emas - fayl `btrfs filesystem mkswapfile`
bilan yoki bo’sh faylga `chattr +C` qo’yib yaratilishi kerak.)

## O’chirish yoki o’lchamini o’zgartirish

```bash
sudo swapoff /swapfile            # page'larini RAM'ga qaytaradi - bo'sh RAM kerak, vaqt olishi mumkin
sudo rm /swapfile
sudo sed -i '/swapfile/d' /etc/fstab

# o'lchamni o'zgartirish = o'chirib, qaytadan yaratish
sudo swapoff /swapfile && sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile \
  && sudo mkswap /swapfile && sudo swapon /swapfile
```

## Qancha va qanchalik ishtiyoq bilan

| RAM | Odatdagi tavsiya |
|---|---|
| ≤ 2 GB | 2× RAM |
| 2-8 GB | = RAM |
| 8-64 GB | 4-8 GB (ko’proq - faqat hibernation bo’lsa) |
| > 64 GB | 4 GB yoki umuman yo’q, hibernation bo’lmasa |
| hibernation | **≥ RAM** |

Ma’lumotlar bazalari va kechikishga sezgir servis’lar ko’pincha juda oz
swap bilan yoki umuman swap’siz ishlaydi va buning o’rniga to’g’ri
o’lcham tanlashga tayanadi; umumiy maqsadli server’lar esa hech swap’siz
emas, ozgina swap bilan yaxshiroq ishlaydi.

```bash
sysctl vm.swappiness                    # sukut bo'yicha 60
sudo sysctl -w vm.swappiness=10         # swap qilishdan ko'ra cache'ni tashlashni afzal ko'radi - server'lar uchun odatiy
echo 'vm.swappiness = 10' | sudo tee /etc/sysctl.d/99-swap.conf
sudo sysctl --system
```

`vm.swappiness` - "qancha swap ishlatish kerak" degani emas; u kernel
page cache’ni chiqarib yuborish o’rniga anonim page’larni qanchalik
osonlik bilan swap qilishini bildiradi. 10 - server uchun oqilona qiymat,
60 - desktop uchun, 1 - butunlay o’chirmasdan qo’yiladigan eng kichigi.

## Prioritet va bir nechta swap

```bash
sudo swapon -p 10 /dev/sdb2         # yuqori prioritet birinchi ishlatiladi
# fstab:  UUID=... none swap sw,pri=10 0 0
swapon --show
```

Alohida disk’lardagi teng prioritet’lar parallel ishlatiladi - swap’dan
qochib bo’lmaydigan holatda kichik unumdorlik hiylasi.

## Raqamlarni o’qish

```bash
free -h
vmstat 1 5                 # si / so ustunlari: sekundiga IN va OUT swap qilingan page'lar
# doim noldan farqli si/so = haqiqiy xotira tanqisligi; ishlatilgan, lekin tinch swap normal
sudo smem -rs swap | head  # process bo'yicha swap sarfi, agar smem o'rnatilgan bo'lsa
for f in /proc/*/status; do awk '/^Name|^VmSwap/{printf "%s ", $2} END{print ""}' "$f"; done | sort -k2 -n | tail
dmesg -T | grep -i "out of memory"
```

**Ishlatilgan swap muammo emas; swap thrashing muammo.** 500 MB swap
ishlatayotgan va I/O’si yo’q server shunchaki tinch page’larni chetga
qo’ygan. `si`/`so` doim noldan farqli bo’lgani esa thrashing qilyapti va
javob ko’proq swap emas, ko’proq RAM yoki kamroq workload.

## zram, qisqacha

**RAM ichida** siqilgan swap - disk’dan tez, aslida CPU’ni xotiraga
almashtirish. Ba’zi distributiv’larda va RAM’i kam mashinalarda sukut
bo’yicha yoqilgan:

```bash
sudo apt install zram-tools
zramctl
```

:::exam-tip
"2 GB swap fayl yarating va uni boot’da yoqing": `fallocate` →
`chmod 600` → `mkswap` → `swapon` → fstab qatori → `swapon --show` va
`free -h` bilan tekshiring. Yo’qotiladigan ikki ball - `chmod 600` va
fstab yozuvi. Doimiy deb aytishdan oldin fstab qatorini
`swapoff -a && swapon -a` bilan sinab ko’ring.
:::

## O’zingizni tekshiring

1. Nega swap fayl `chmod 600` bo’lishi kerak va busiz nima bo’ladi?
2. `vm.swappiness` aslida nimani boshqaradi?
3. Sog’lom swap sarfini xotira muammosidan qanday ajratasiz?
