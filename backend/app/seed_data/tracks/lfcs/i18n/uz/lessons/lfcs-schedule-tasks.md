## Uchta rejalashtiruvchi

| Vosita | Nima uchun |
|---|---|
| **cron** | belgilangan vaqtlarda takrorlanadigan job’lar - klassikasi |
| **at** | kelajakda bir marta bajariladigan job |
| **systemd timers** | systemd’ning loglari, bog’liqliklari va kalendar sintaksisi bilan takrorlanadigan job’lar |

## crontab sintaksisi

```
 ┌─ daqiqa (0-59)
 │ ┌─ soat (0-23)
 │ │ ┌─ oyning kuni (1-31)
 │ │ │ ┌─ oy (1-12 yoki jan-dec)
 │ │ │ │ ┌─ hafta kuni (0-7, 0 va 7 = yakshanba, yoki sun-sat)
 │ │ │ │ │
 * * * * *  ishga tushadigan buyruq
```

| Yozuv | Qachon ishlaydi |
|---|---|
| `0 3 * * *` | har kuni 03:00’da |
| `*/15 * * * *` | har 15 daqiqada |
| `0 */4 * * *` | har 4 soatda |
| `30 2 * * 1` | dushanbalari 02:30’da |
| `0 0 1 * *` | har oyning birinchi kuni |
| `0 9-17 * * 1-5` | soat sayin, 09:00-17:00, ish kunlari |
| `15 2 1,15 * *` | oyning 1- va 15-kunlari 02:15’da |
| `@reboot` | har bir boot’da bir marta |
| `@daily` `@weekly` `@monthly` `@hourly` `@yearly` | qisqartmalar |

**Oyning kuni va hafta kuni birga berilsa, bu OR bo’ladi**: `0 0 13 * 5`
13-kuni *va* har juma ishlaydi, faqat 13-kunga to’g’ri kelgan jumada emas.

## Har bir user uchun crontab

```bash
crontab -e                 # O'ZINGIZNING crontab'ingizni tahrirlaydi ($EDITOR bilan)
crontab -l                 # ro'yxat
crontab -r                 # butunlay o'chiradi (tasdiq so'ramaydi - ehtiyot bo'ling)
crontab -l > backup.cron   # -r'dan oldin backup qiling
crontab backup.cron        # fayldan o'rnatadi
sudo crontab -u alice -e   # boshqa user'niki
sudo crontab -u alice -l
```

`/var/spool/cron/crontabs/<user>` (Debian) yoki `/var/spool/cron/<user>`
(RHEL) ichida saqlanadi - faqat `crontab -e` orqali tahrirlang, u
sintaksisni tekshiradi.

## Tizim crontab’lari

```bash
cat /etc/crontab           # qo'shimcha USER ustuni bor
ls /etc/cron.d/            # drop-in fayllar, /etc/crontab bilan bir xil format
ls /etc/cron.{hourly,daily,weekly,monthly}/     # skriptlar, run-parts ishga tushiradi - vaqt maydonlari umuman yo'q
```

```
# /etc/cron.d/backup     ← user ustuniga e'tibor bering
30 2 * * *  root  /usr/local/bin/backup.sh
```

`/etc/cron.daily/` ichidagi skript **bajariladigan** bo’lishi, root’ga
tegishli bo’lishi va - Debian’da - **fayl nomida nuqtasiz** bo’lishi kerak
(`run-parts` sozlanmagan bo’lsa `backup.sh`’ni o’tkazib yuboradi; uni
`backup` deb nomlang).

## Muhit tuzog’i

cron minimal muhitda ishlaydi: `PATH=/usr/bin:/bin`, `~/.bashrc` o’qilmaydi,
`HOME` o’rnatilgan, `SHELL=/bin/sh`. Terminalingizda ishlaydigan, cron’da
esa hech narsa qilmaydigan skript deyarli har doim shu sabab.

```
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAILTO=admin@example.com

0 3 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1
```

Qoidalar: buyruqlar va fayllar uchun **absolyut yo’llar**; chiqishni
yo’naltiring (aks holda cron uni pochta qilib yuboradi yoki u yo’qoladi);
cron’ning yalang’och muhitini takrorlash uchun `env -i /bin/bash --noprofile
--norc /path/script.sh` bilan sinab ko’ring.

```bash
%           # crontab ichida % yangi qator degani - uni ekranlang: date +\%F
0 3 * * * echo "run at $(date +\%F)" >> /var/log/x.log
```

## U ishlaganini tekshirish

```bash
grep CRON /var/log/syslog | tail             # Debian
journalctl -u cron -f                        # RHEL'da -u crond
journalctl _COMM=cron --since today
sudo systemctl status cron
ls -l /var/spool/cron/crontabs/
```

Kirish nazorati: `/etc/cron.allow` (agar u mavjud bo’lsa, cron’dan faqat shu
user’lar foydalana oladi) va `/etc/cron.deny`.

## anacron: doim yoqiq turmaydigan mashinalar uchun

```bash
cat /etc/anacrontab
# davr  kechikish  job-identifikatori  buyruq
# 1       5      cron.daily      run-parts --report /etc/cron.daily
```

Mashina o’chiq turgan paytda vaqti o’tib ketgan job’larni cron o’tkazib
yuboradi; **anacron** esa ularni kechikib bo’lsa ham ishga tushiradi.
Noutbuklar va desktop’larga u kerak; doim yoqiq serverlarga odatda kerak
emas.

## at: bir marta, keyinroq

```bash
at 22:00                       # keyin buyruqlarni yozing, tugatish uchun Ctrl-D
at now + 1 hour
at 09:00 tomorrow
at 14:30 2026-09-01
echo "/usr/local/bin/report.sh" | at 06:00 tomorrow
atq                            # navbat
atrm 3                         # 3-job'ni o'chiradi
at -c 3                        # 3-job nima ishga tushirishini ko'rsatadi (saqlangan muhiti bilan)
sudo systemctl enable --now atd
```

`at` sizning **joriy muhitingizni** saqlaydi, shuning uchun bir martalik
ishlarda u cron’ga qaraganda qulayroq. Kirishni `/etc/at.allow`,
`/etc/at.deny` boshqaradi.

## systemd timer’lari

```ini
# /etc/systemd/system/backup.service
[Unit]
Description=Nightly backup
[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh
```

```ini
# /etc/systemd/system/backup.timer
[Unit]
Description=Run backup nightly
[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true          # oxirgi ishga tushish o'tkazib yuborilgan bo'lsa, boot'da ishlaydi (anacron kabi)
RandomizedDelaySec=300
[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now backup.timer
systemctl list-timers --all               # NEXT, LEFT, LAST, PASSED, UNIT
systemctl status backup.timer
journalctl -u backup.service              # chiqish journal'da, pochtada emas
systemd-analyze calendar "Mon *-*-* 02:30:00"     # jadval ifodasini tekshiradi
```

`OnCalendar=` shakllari: `hourly`, `daily`, `weekly`, `Mon..Fri 09:00`,
`*-*-01 04:00:00`, `*:0/15` (har 15 daqiqada). Timer’lar sizga cron
bermaydigan bog’liqliklar, resurs limitlari va journal’ga log yozishni
beradi - systemd mashinasida jiddiyroq har qanday ish uchun ulardan
foydalaning.

:::exam-tip
Ko’proq so’raladigani - cron: "alice user’i nomidan har kuni 05:30’da
/usr/local/bin/x.sh ishga tushsin". Yechim:
`sudo crontab -u alice -e`, qator `30 5 * * *
/usr/local/bin/x.sh`. `crontab -u alice -l` bilan tekshiring. Maydonlar
tartibiga (avval daqiqa!) e’tibor bering va absolyut yo’llardan
foydalaning. "Har 10 daqiqada" uchun bu `*/10 * * * *`.
:::

## O’zingizni tekshiring

1. Har dushanba va payshanba 02:15 uchun crontab qatorini yozing.
2. Shell’ingizda ishlaydigan skript nega ko’pincha cron ostida ishlamaydi
   va ikkita yechim qanday?
3. systemd timer’ida `Persistent=true` nima qiladi va u qaysi cron
   vositasining o’rnini bosadi?
