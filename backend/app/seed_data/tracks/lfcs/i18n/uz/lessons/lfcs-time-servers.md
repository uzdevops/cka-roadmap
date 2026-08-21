## Nega soat muhim

Noto’g’ri soat timestamp’dan ko’ra ko’proq narsani buzadi: TLS
sertifikatlari "not yet valid" deb rad etiladi, Kerberos va AD login’lari
besh daqiqalik skew’dan tashqarida ishlamaydi, host’lar bo’ylab loglarni
solishtirish taxminga aylanadi, cron noto’g’ri vaqtda ishga tushadi,
ma’lumotlar bazasi replikatsiyasi va backup’lar chalkash tartibga ega
bo’ladi. Vaqtni sinxronlash - kosmetika emas.

## timedatectl: umumiy ko’rinish

```bash
timedatectl
#                Local time: Fri 2026-08-21 14:03:11 +05
#            Universal time: Fri 2026-08-21 09:03:11 UTC
#                  RTC time: Fri 2026-08-21 09:03:11
#                 Time zone: Asia/Tashkent (+05, +0500)
# System clock synchronized: yes
#               NTP service: active
#           RTC in local TZ: no
```

O’qish kerak bo’lgan to’rt narsa: **time zone**, soat
**sinxronlanganmi**, **NTP service** ishlayaptimi va RTC mahalliy vaqtda
**emasligi** (faqat Linux ishlaydigan har qanday mashinada u UTC bo’lishi
kerak).

```bash
timedatectl list-timezones | grep -i tashkent
sudo timedatectl set-timezone Asia/Tashkent
sudo timedatectl set-ntp true                 # sinxronlash service'ini yoqish
sudo timedatectl set-time "2026-08-21 14:00:00"    # qo'lda - faqat NTP o'chirilgandagina ishlaydi
sudo timedatectl set-local-rtc 0                    # apparat soatini UTC'da saqlash
date; date -u; date -R; date +%s
```

Time zone - bu zoneinfo fayliga symlink:

```bash
ls -l /etc/localtime          # → /usr/share/zoneinfo/Asia/Tashkent
cat /etc/timezone             # Debian
TZ=UTC date                   # boshqa zone'dagi bitta buyruq
```

## chrony: tavsiya etilgan NTP client

```bash
sudo apt install chrony        # Debian/Ubuntu
sudo dnf install chrony        # RHEL
sudo systemctl enable --now chronyd     # (Debian'da chrony)
```

```bash
sudo vi /etc/chrony/chrony.conf         # RHEL'da /etc/chrony.conf
```

```
pool 2.pool.ntp.org iburst              # serverlar pool'i; iburst = ishga tushganda tez sinxronlash
server ntp1.example.com iburst prefer   # aniq bir server, afzal ko'riladigan
driftfile /var/lib/chrony/chrony.drift
makestep 1.0 3                          # birinchi 3 yangilanishda katta step tuzatishlariga ruxsat
rtcsync                                 # apparat soatini ham hamqadam saqlash
# allow 192.168.1.0/24                  # shu tarmoqqa vaqtni TARQATISH (bu host'ni NTP serverga aylantiradi)
# local stratum 10                      # o'zimiz sinxronlanmagan bo'lsak ham tarqatish
```

```bash
sudo systemctl restart chronyd
chronyc sources -v
# MS Name/IP address    Stratum Poll Reach LastRx Last sample
# ^* ntp1.example.com         2    6   377     21   +14us[  +18us] +/-   12ms
chronyc sourcestats
chronyc tracking                 # bizning offset, drift va stratum
chronyc -a makestep              # darhol step tuzatishini majburlash
chronyc ntpdata
```

`chronyc sources` chiqishida boshidagi belgilar butun hikoyani aytadi:
`^*` - tanlangan sinxronlash manbasi, `^+` - maqbul muqobil, `^-` -
birlashtirish algoritmi chetlatgan, `^?` - yetib bo’lmaydigan.
`Reach 377` (sakkizlik sanoqda, sakkizala bit) oxirgi sakkizta
so’rovning hammasiga javob kelganini bildiradi.

## systemd-timesyncd: minimal client

chrony o’rnatilmagan bo’lsa, Ubuntu’da sukut bo’yicha shu ishlatiladi. Bu -
SNTP client: soatni sinxronlay oladi, lekin vaqtni tarqata olmaydi va uni
shunchalik aniq boshqara olmaydi.

```bash
systemctl status systemd-timesyncd
timedatectl show-timesync --all
sudo vi /etc/systemd/timesyncd.conf     # [Time] NTP=ntp1.example.com  FallbackNTP=...
sudo systemctl restart systemd-timesyncd
timedatectl timesync-status
```

Bir vaqtda faqat bitta time daemon: chrony o’rnatilganda odatda timesyncd
mask qilinadi, ikkalasini birga ishlatish esa ularni bir-biriga
urishtiradi.

```bash
systemctl is-active chronyd systemd-timesyncd ntpd     # aynan bittasi faol bo'lishi kerak
```

## LAN’ga vaqt tarqatish

```
# serverda, chrony.conf ichida
allow 192.168.1.0/24
local stratum 10
```

```bash
sudo systemctl restart chronyd
sudo firewall-cmd --permanent --add-service=ntp && sudo firewall-cmd --reload   # UDP 123
sudo ufw allow 123/udp
chronyc clients                       # kim bizdan so'rayapti
# client'larda:  server 192.168.1.10 iburst
```

## Apparat soati

```bash
sudo hwclock --show                  # RTC
sudo hwclock --systohc               # tizim → apparat (to'g'ri vaqtni RTC'ga yozish)
sudo hwclock --hctosys               # apparat → tizim
```

Mashina Windows bilan dual-boot bo’lmasa, RTC’ni **UTC**’da saqlang
(`set-local-rtc 0`). VM odatda host’ning soatini meros qilib oladi,
shuning uchun guest’dagi vaqt siljishi ko’pincha host muammosi bo’ladi.

## Diagnostika

```bash
timedatectl                                   # bosh sarlavha - "System clock synchronized: no"
chronyc tracking | grep -E "System time|Stratum|Leap"
chronyc sources
journalctl -u chronyd --since today
sudo ss -ulpn | grep 123
ping -c1 pool.ntp.org
sudo chronyd -Q 'pool pool.ntp.org iburst'    # bir martalik: qanday offset olar edik?
```

| Alomat | Sababi |
|---|---|
| `System clock synchronized: no` | NTP service ishlamayapti, yoki yetib boradigan manba yo’q |
| hamma manbalar `^?` | UDP 123 tashqariga bloklangan, yoki pool nomini DNS yecha olmayapti |
| katta offset hech tuzalmaydi | step juda katta - `makestep`, yoki `chronyc -a makestep` |
| soat sakrab turadi | bir vaqtda ikkita time daemon ishlayapti |
| sertifikatlar "not yet valid" deyapti | soat orqada - avval vaqtni tuzating, keyin TLS’ni qayta sinang |
| vaqt to’g’ri, loglar noto’g’ri zone’da | gap soatda emas, time zone’da - `timedatectl set-timezone` |

:::exam-tip
Ikkita topshiriq: "time zone’ni X qiling" → `timedatectl set-timezone X`,
`timedatectl` bilan tekshiriladi; "tizimni Y serveri bilan vaqtni
sinxronlashga sozlang" → chrony.conf’ga `server Y iburst` qo’shing,
chronyd’ni restart qiling, `^*` ko’rsatayotgan `chronyc sources` va
sinxronlanganini ko’rsatayotgan `timedatectl` bilan tekshiring. NTP
ishlashi kerak bo’lgan joyda soatni qo’lda o’rnatmang.
:::

## O’zingizni tekshiring

1. Serverning soati noto’g’ri bo’lganda buziladigan uchta narsani ayting.
2. Qaysi buyruq soat sinxronlanganini ko’rsatadi va qaysi biri manbalarni
   hamda ularning holatini ko’rsatadi?
3. Nega faqat bitta time daemon faol bo’lishi kerak va buni qanday
   tekshirasiz?
