## "Bu tizim sog’lommi?"

Maqsad ataylab keng qo’yilgan: resurslar yetarliligini (disk, xotira, CPU),
process va service’lar ishlab turganini va diskdagi narsalar
buzilmaganini tekshirish. Sizga topshirilgan har qanday mashinadagi
birinchi besh daqiqa - shu.

## Disk joyi va inode’lar

```bash
df -h                       # har bir fayl tizimi bo'yicha joy
df -h /var                  # bitta yo'lning fayl tizimi
df -i                       # INODE'lar - joy bo'sh bo'lsa ham disk "to'la" bo'lishi mumkin
du -sh /var/log             # bu daraxt qanchalik katta
du -sh /var/* | sort -rh | head
du -xh /var --max-depth=1 | sort -rh    # -x: bitta fayl tizimida qoladi
ncdu /var                   # interaktiv, o'rnatilgan bo'lsa
find / -xdev -type f -size +500M -exec ls -lh {} + 2>/dev/null
lsof +L1                    # o'chirilgan, lekin ochiq turgan va joyni band qilayotgan fayllar
```

Ikki xil "disk to’la" nosozligi ilova logida bir xil ko’rinadi: **joy yo’q**
(`df -h` 100% ko’rsatadi) va **inode yo’q** (`df -i` 100% ko’rsatadi,
odatda bitta directory’da millionlab mayda fayl). Ikkalasini ham
tekshiring.

## Xotira va swap

```bash
free -h
#                total   used   free  shared  buff/cache  available
# Mem:            7.7G   2.1G   1.2G    250M        4.4G        5.1G
# Swap:           2.0G     0B   2.0G
```

**available**’ni o’qing, free’ni emas: `buff/cache` - bu Linux kesh sifatida
ishlatayotgan va so’ralsa darhol qaytarib beradigan xotira. Doimiy
ishlatilayotgan swap (`vmstat`’dagi `si`/`so`) haqiqiy siqilish degani.

```bash
vmstat 1 5                  # r b | swpd free buff cache | si so | bi bo | in cs | us sy id wa
cat /proc/meminfo | head -5
dmesg -T | grep -i "out of memory\|oom-killer"     # kim o'ldirildi va nega
ps aux --sort=-%mem | head -5
```

## CPU va yuklama

```bash
uptime                      # 1/5/15 daqiqalik load average
nproc                       # nechta CPU bor - yuklamani shu son bilan solishtiring
top -b -n1 | head -15
mpstat 1 5                  # har bir CPU bo'yicha, sysstat paketidan
sar -u 1 5                  # sysstat yig'ishi yoqilgan bo'lsa, tarix ham
```

`%us` past bo’lgani holda `%wa` (I/O kutish) yuqori bo’lsa, tiqilinch
CPU’da emas, diskda.

## Service’lar va process’lar

```bash
systemctl --failed                       # eng ko'p ma'lumot beradigan yagona buyruq
systemctl is-active nginx sshd
systemctl list-units --type=service --state=running | head
ps -ef --forest | head -30
pgrep -a nginx
ss -tulpn                                # qaysi portlar ochiq va ularni kim ushlab turibdi
ss -s                                    # soketlar bo'yicha xulosa
curl -sS -o /dev/null -w '%{http_code}\n' http://localhost/health
systemctl status myapp
journalctl -p err -b --no-pager | tail -20
```

## Tezkor sog’liq skripti

```bash
#!/bin/bash
echo "== uptime";        uptime
echo "== failed units";  systemctl --failed --no-legend
echo "== disk";          df -h -x tmpfs -x devtmpfs
echo "== inodes";        df -i -x tmpfs -x devtmpfs | awk 'NR==1 || $5+0 > 80'
echo "== memory";        free -h
echo "== top mem";       ps aux --sort=-%mem | head -4
echo "== recent errors"; journalctl -p err -b --no-pager | tail -10
```

## Fayl tizimining butunligi

```bash
sudo touch /forcefsck                  # eski usul: keyingi boot'da tekshiruvni majburlaydi
sudo tune2fs -l /dev/sda1 | grep -i "mount count\|check"
sudo umount /dev/sdb1                  # mount qilingan fayl tizimida HECH QACHON fsck qilmang
sudo fsck -n /dev/sdb1                 # -n: xabar beradi, hech narsani o'zgartirmaydi
sudo fsck -y /dev/sdb1                 # tuzatishlarga "ha" deb javob beradi
sudo xfs_repair /dev/sdb1              # XFS'ning o'z vositasi bor (va mount holatida tekshirib bo'lmaydi)
sudo smartctl -H /dev/sda              # DISKNING o'zi ishdan chiqyaptimi? (smartmontools)
sudo smartctl -a /dev/sda | grep -i "reallocated\|pending"
sudo badblocks -sv /dev/sdb            # sekin ishlaydigan yuza skani
```

:::warning
`fsck`’ni **mount qilingan** fayl tizimida ishlatish uni buzadi. Avval
unmount qiling yoki rescue rejimidan / live image’dan ishga tushiring. Root
fayl tizimi uchun bu `touch /forcefsck` va reboot, yoki rescue’ga boot
qilish degani.
:::

## Fayllar butunligi

```bash
sha256sum -c SHA256SUMS               # yuklab olinganlarni tekshiradi
rpm -Va                                # har bir RPM paketining har bir o'zgargan fayli
sudo debsums -c                         # Debian'dagi ekvivalenti (debsums'ni o'rnating)
sudo apt install aide && sudo aideinit  # to'liq fayl butunligi bazasi va davriy tekshiruvlar
sudo aide --check
```

## Vaqt bo’yicha ishlab turish

```bash
uptime -s; last reboot | head          # u qayta-qayta yuklanyaptimi?
sar -q                                 # tarixiy yuklama (sysstat)
systemd-analyze                         # boot vaqti
journalctl --since "24 hours ago" -p warning --no-pager | wc -l
```

:::exam-tip
Kichik va aniq so’rovlar kutiladi: "eng kam bo’sh joyi qolgan fayl tizimini
faylga yozing", "ishlamay qolgan barcha service’larni sanang", "qancha
xotira mavjudligini ko’rsating". Buyruqlar - `df -h`, `systemctl --failed`,
`free -h` - topshiriqda aytilgan faylga yo’naltirish bilan. Disk "to’la"
bo’lib, `df -h` boshqacha desa, `df -i`’ni ham esdan chiqarmang.
:::

## O’zingizni tekshiring

1. Fayl tizimi "joy qolmadi" deyishiga ikki xil sabab bor. Qaysi buyruqlar
   ularni ajratadi?
2. `free -h`’da qaysi ustun xotiraning haqiqatan foydalanish mumkin bo’lgan
   miqdorini aytadi va nega `free` emas?
3. `fsck`’dan oldin fayl tizimi nega unmount qilingan bo’lishi kerak va root
   fayl tizimini qanday tekshirasiz?
