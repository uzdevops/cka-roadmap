## Yonma-yon ikkita log tizimi

Zamonaviy Linux binary **journal** (systemd-journald) va, odatda, rsyslog
yozadigan oddiy matnli fayllarni `/var/log`’da saqlaydi. Ikkalasi ham bir
xil hodisalarni saqlaydi; journal’da struktura va filtrlar bor, fayllarni
esa grep qilish mumkin va ular nusxalanganda ham omon qoladi.

```bash
journalctl                       # hammasi, eng eskisidan boshlab (bu pager: chiqish uchun q)
journalctl -e                    # oxiriga sakrash
journalctl -f                    # kuzatish, tail -f kabi
journalctl -n 50                 # oxirgi 50 satr
journalctl -r                    # eng yangisi birinchi
```

## Journal’ni filtrlash

```bash
journalctl -u nginx                       # bitta unit
journalctl -u nginx -u sshd               # bir nechta
journalctl -u nginx -f                    # bitta unit'ni kuzatish
journalctl -b                             # shu boot
journalctl -b -1                          # oldingi boot
journalctl --list-boots
journalctl -k                             # kernel xabarlari (dmesg kabi)
journalctl -p err                         # prioritet: err va undan yomoni
journalctl -p warning..err
journalctl --since "2026-08-19 09:00" --until "2026-08-19 10:00"
journalctl --since "1 hour ago"
journalctl --since yesterday --until today
journalctl _PID=1234
journalctl _UID=1000
journalctl /usr/sbin/sshd                 # bajariladigan fayl bo'yicha
journalctl -u myapp -o json-pretty | head -40      # har bir strukturali maydon
journalctl -o cat                         # yalang'och xabarlar, timestamp'siz - pipe qilishga qulay
journalctl -xe                            # oxiri, izohlar bilan - standart "hozir nima buzildi"
journalctl -u myapp --grep "timeout"
```

Prioritetlar, kichik raqam = yomonroq: `0 emerg`, `1 alert`, `2 crit`,
`3 err`, `4 warning`, `5 notice`, `6 info`, `7 debug`.

## Journal saqlanishi: volatile yoki persistent

```bash
journalctl --disk-usage
ls /var/log/journal/           # mavjud → persistent;  faqat /run/log/journal → faqat RAM, reboot'da yo'qoladi
sudo mkdir -p /var/log/journal && sudo systemd-tmpfiles --create --prefix /var/log/journal
sudo systemctl restart systemd-journald
```

```ini
# /etc/systemd/journald.conf
[Journal]
Storage=persistent
SystemMaxUse=500M
MaxRetentionSec=1month
```

```bash
sudo journalctl --vacuum-size=200M
sudo journalctl --vacuum-time=7d
sudo journalctl --verify
```

Agar `journalctl -b -1` "Specifying boot ID has no effect, no persistent
journal was found" desa, journal RAM’da - bu sozlamani keyingi crash’dan
**oldin** o’zgartirish kerak, keyin emas.

## /var/log: matnli fayllar

| Fayl | Nima saqlaydi |
|---|---|
| `/var/log/syslog` (Debian) / `/var/log/messages` (RHEL) | umumiy tizim xabarlari |
| `/var/log/auth.log` (Debian) / `/var/log/secure` (RHEL) | autentifikatsiya, sudo, sshd |
| `/var/log/kern.log` | kernel |
| `/var/log/boot.log` | boot xabarlari |
| `/var/log/dmesg` | boot paytidagi kernel ring buffer |
| `/var/log/cron` / journal | cron job’lari |
| `/var/log/apt/`, `/var/log/dnf.log` | paket operatsiyalari |
| `/var/log/nginx/`, `/var/log/mysql/` | har bir service uchun alohida direktoriyalar |
| `/var/log/wtmp`, `/var/log/btmp`, `/var/log/lastlog` | binary: `last`, `lastb`, `lastlog`’dan foydalaning |

```bash
sudo tail -f /var/log/syslog
sudo grep -i "failed password" /var/log/auth.log | tail
sudo less /var/log/nginx/error.log
last | head; sudo lastb | head; lastlog | grep -v "Never"
```

## rsyslog: qaysi xabar qayerga ketadi

```bash
cat /etc/rsyslog.conf; ls /etc/rsyslog.d/
```

```
auth,authpriv.*                 /var/log/auth.log
*.*;auth,authpriv.none          -/var/log/syslog
kern.*                          -/var/log/kern.log
*.emerg                         :omusrmsg:*
local7.*                        @@logserver.example.com:514      # @@ TCP, @ UDP - markazlashgan logging
```

`facility.priority  destination`. Tahrirlagandan keyin:
`sudo systemctl restart rsyslog`. `logger` bilan sinang:

```bash
logger "test message"                       # syslog'ga user.notice sifatida ketadi
logger -p local7.err -t myapp "disk full"   # facility, prioritet, tag
journalctl -t myapp
```

## logrotate: /var/log diskni to’ldirmasligi uchun

```bash
cat /etc/logrotate.conf; ls /etc/logrotate.d/
```

```
/var/log/myapp/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 myapp adm
    sharedscripts
    postrotate
        systemctl reload myapp > /dev/null 2>&1 || true
    endscript
}
```

```bash
sudo logrotate -d /etc/logrotate.d/myapp     # debug: nima BO'LISHI mumkinligi
sudo logrotate -f /etc/logrotate.d/myapp     # hozir rotatsiyani majburlash
cat /var/lib/logrotate/status                 # har bir fayl oxirgi marta qachon rotatsiya qilingan
```

`create` muhim: rotatsiya qilingan fayl service’ga kerak bo’lgan ruxsatlar
va egalikni saqlab qolishi kerak, aks holda service o’zi ocholmaydigan
faylga yozadi. `copytruncate` - faylni ochiq ushlab turadigan va reload’da
uni qayta ochmaydigan dasturlar uchun mo’ljallangan opsiya.

## Disk loglar bilan to’lganda

```bash
df -h /var
du -sh /var/log/* | sort -rh | head
sudo journalctl --vacuum-size=200M
sudo find /var/log -name "*.gz" -mtime +30 -delete
lsof +L1 | head        # jarayon hali ochiq ushlab turgan o'chirilgan fayllar - joyni bo'shatish uchun uni restart qiling
```

Oxirgisi - tuzoq: jarayon hali ochiq ushlab turgan logni o’chirish,
jarayon uni qayta ochmaguncha, joy bo’shatmaydi. `df` to’la ko’rsatadi,
`du` esa fayl yo’q deydi.

:::exam-tip
Ikkala dunyoni ham biling: systemd uchun `journalctl -u X`, `-b`,
`-p err`, `--since`, matn uchun esa grep bilan
`/var/log/auth.log`/`syslog`. "Barcha muvaffaqiyatsiz login urinishlarini
toping" → `grep "Failed password" /var/log/auth.log` yoki `journalctl -u
sshd -p err`. "Journal’ni persistent qiling" → `Storage=persistent` +
restart. "/var/log/myapp uchun rotatsiyani sozlang" →
`/etc/logrotate.d/` ichidagi fayl va `logrotate -d` bilan sinash.
:::

## O’zingizni tekshiring

1. Qaysi journalctl opsiyalari quyidagilarni ko’rsatadi: bitta unit,
   oldingi boot, faqat xatolar, oxirgi bir soat?
2. Journal reboot’dan omon qolishini qanday ta’minlaysiz va hozir
   shundayligini qanday bilasiz?
3. Katta log faylni o’chirish nega `df`’ni o’zgarishsiz qoldirishi
   mumkin?
