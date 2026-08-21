## LFCS mock imtihon 1

Ikki soat. O’n beshta topshiriq, og’irliklar qavs ichida, jami 100. Zaxira
disk (`/dev/sdb`, ≥5 GB) ulangan Ubuntu LTS VM. Avval snapshot. Faqat `man`.

---

**1.** (5) `jdoe` nomli user yarating: home direktoriyasi `/home/jdoe`,
shell `/bin/bash`, to’liq ismi "John Doe" va hisobning amal qilish muddati
`2027-01-31`’da tugaydi.

**2.** (5) `analysts` nomli guruh yarating va `jdoe`’ni unga a’zo qiling,
uning mavjud guruhlaridan birortasini olib tashlamasdan.

**3.** (6) `/srv/analytics` direktoriyasini yarating: egasi `analysts`
guruhi bo’lsin, guruh unga yoza olsin, boshqalar kira olmasin va uning
ichida yaratilgan har bir fayl guruh egaligi `analysts` bo’lsin.

**4.** (7) `/var/log` ostidagi 1 MB’dan katta va oxirgi 7 kunda
o’zgartirilgan har bir faylni toping va ro’yxatni `/root/biglogs.txt`’ga
yozing.

**5.** (6) Ikkalasi ham `/etc/hosts`’ga qaraydigan `/root/hosts.hard` hard
link’ini va `/root/hosts.soft` symbolic link’ini yarating.
`/root/links.txt`’da hard link’ning inode’ini va soft link’ning target’ini ko’rsating.

**6.** (8) `/dev/sdb`’da 1 GiB partition yarating, uni `data01` label’i
bilan ext4 formatlang va `noexec` opsiyasi bilan `/mnt/data01`’ga
**doimiy** qilib mount qiling.

**7.** (7) `/swapextra`’da 512 MiB swap **fayli** yarating, uni yoqing va
doimiy qiling.

**8.** (8) `heartbeat` nomli systemd service yarating: u
`/usr/local/bin/heartbeat.sh`’ni ishga tushirsin (uni o’zingiz yozing: har
safar ishlaganda sanani `/var/log/heartbeat.log`’ga qo’shsin), `nobody`
useri nomidan ishlasin, nosozlikda qayta ishga tushsin. Uni enable qiling
va ishga tushiring.

**9.** (6) `/usr/local/bin/heartbeat.sh`’ni `root` useri uchun cron orqali
har 10 daqiqada ishga tushishga rejalashtiring, chiqishni
`/var/log/heartbeat-cron.log`’ga yozib boring.

**10.** (7) Tizimni IPv4 paketlarini uzatadigan qilib **doimiy** ravishda
sozlang va amaldagi qiymatni `/root/forward.txt`’da ko’rsating.

**11.** (7) `nginx`’ni o’rnating, uning boot paytida ishga tushishiga
ishonch hosil qiling va 80-portda tinglayotganini tasdiqlang. Tegishli
`ss` chiqishini `/root/nginx-port.txt`’ga yozing.

**12.** (8) Firewall orqali kiruvchi SSH va HTTP’ga ruxsat bering, qolgan
barcha kiruvchi trafikni rad eting va konfiguratsiyani doimiy qiling.
O’zingizni tashqarida qoldirib qo’ymang.

**13.** (8) Tizim vaqt zonasini `Asia/Tashkent`’ga o’rnating va vaqt NTP
service tomonidan sinxronlanayotganini ta’minlang. `timedatectl` chiqishini
`/root/time.txt`’ga yozing.

**14.** (6) `jdoe` useriga `/srv/analytics/report.txt` fayliga (uni
yarating) ACL yordamida o’qish va yozish huquqini bering, uning egasini
yoki guruhini o’zgartirmasdan.

**15.** (6) `/etc/ssh` va `/etc/hosts`’ni o’z ichiga olgan, gzip bilan
siqilgan `/root/etc-backup.tar.gz` tar arxivini yarating va uning
tarkibini ochmasdan tekshiring.

---

Ball qo’ying, keyin ko’rib chiqish testi. To’liq balldan past bo’lgan
narsa: o’sha dars va uning labi, o’sha kuni.

:::exam-tip
Bu o’n beshtadan oltitasi **doimiylikni** talab qiladi (6, 7, 8, 9, 10,
12, 13). Agar ularning barchasini ikki soatdan kamroq vaqtda tugatgan
bo’lsangiz, lekin fstab satrini yoki `systemctl enable`’ni o’tkazib
yuborgan bo’lsangiz, haqiqiy ballingiz his qilganingizdan ancha past.
Doimiylikni aniq tekshiring: `mount -a`, `swapon --show`, `systemctl
is-enabled`, `sysctl <key>`, `ufw status`.
:::

## O’zingizni tekshiring

1. Birinchi o’tishda qaysi topshiriqlarni o’tkazib yubordingiz va ularga
   qaytdingizmi?
2. Bajargan har bir topshiriq uchun yakuniy holatni qaysi yagona buyruq
   isbotladi?
3. Qaysi topshiriq eng ko’p vaqt oldi va bu bilim, `man`’da navigatsiya
   yoki yozish tezligi masalasi edimi?
