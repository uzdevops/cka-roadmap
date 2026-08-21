## LFCS mock imtihon 4

Ikki soat. O’n beshta topshiriq, jami 100. Haqiqiysidan oldingi oxirgisi:
barcha sohalar, ishoralarsiz va ataylab to’liq aniqlanmagan uchta
topshiriq - "to’g’ri" nima ekanini o’zingiz hal qilishingiz kerak. Avval
snapshot.

---

**1.** (7) `/root/records.csv` fayli (uni `name,dept,salary` ko’rinishidagi
o’nta satr bilan yarating) umumlashtirilishi kerak: `/root/bydept.txt`’ga
har bir bo’limni yozuvlari soni bilan, son bo’yicha eng kattadan
boshlab saralangan holda yozing.

**2.** (6) `/var/log/auth.log`’dan (yoki jurnaldan) oxirgi 24 soatda
muvaffaqiyatsiz autentifikatsiyani qayd etgan har bir satrni
`/root/failed.txt`’ga chiqarib oling va sonini
`/root/failed-count.txt`’ning birinchi satriga qo’ying.

**3.** (7) Mavjud yoki yangi volume group’da 2 GiB hajmli `lvbackup`
logical volume yarating, uni ext4 formatlang, `nodev,nosuid` bilan
`/backup`’ga doimiy qilib mount qiling va opsiyalar kuchda ekanini
tasdiqlang.

**4.** (7) `lvbackup`’ning 500 MiB hajmli `lvbackup_snap` nomli
snapshot’ini oling, uni `/mnt/snap`’ga faqat o’qish uchun mount qiling,
tarkibini `/root/snap.txt`’ga ro’yxatlang, keyin snapshot’ni o’chiring.

**5.** (7) `/usr/local/bin/backup.sh` yozing: u `/etc`’dan
`/backup/etc-YYYY-MM-DD.tar.gz` yaratsin va 7 kundan eski arxivlarni
o’chirsin. Uni systemd timer bilan (cron emas) har kuni 01:00 ga
rejalashtiring va ishlashini isbotlash uchun bir marta qo’lda ishga
tushiring.

**6.** (7) `dev1` va `dev2` userlarini, `devteam` guruhini va
`/srv/devteam` direktoriyasini yarating: ikkalasi ham fayl yarata olsin,
har biri faqat **o’z** fayllarini o’chira olsin va ichida yaratilgan
fayllar `devteam`’ga tegishli bo’lsin.

**7.** (6) `dev1` uchun parol muddatini sozlang: maksimum 60 kun, minimum
7, ogohlantirish 10 va keyingi login’da parolni majburiy o’zgartirish.
`chage -l dev1` chiqishini `/root/ageing.txt`’da ko’rsating.

**8.** (7) SSH serverni 22-portga **qo’shimcha ravishda** 2222-portda ham
tinglaydigan qilib sozlang, firewall (va enforcing rejimida bo’lsa,
SELinux) bunga ruxsat berishini ta’minlang. Yangi portga ulanib
tekshiring.

**9.** (7) Bu hostning ikkinchi interfeysini statik manzil bilan sozlang
va host o’zidan `lab.local` nomi orqali topiladigan bo’lsin. Nom
yechimini `/root/resolve.txt`’da ko’rsating.

**10.** (7) Bir service boot paytida, tarmoq to’liq ishga tushgandan
**keyin**, imtiyozsiz user nomidan, 10 soniyalik qayta ishga tushish
kechikishi va 256 MB xotira cheklovi bilan ishlashi kerak. Uni yarating
(istalgan uzoq ishlaydigan buyruq) va uchta tegishli xossa uchun
`systemctl show` chiqishini `/root/unit.txt`’da ko’rsating.

**11.** (6) Ayni damda eng ko’p xotira ishlatayotgan jarayonni va eng ko’p
disk I/O qilayotgan jarayonni aniqlang va ikkalasini PID’lari bilan
`/root/hogs.txt`’ga yozib qo’ying.

**12.** (6) Kernel parametrlarini doimiy qilib o’rnating:
`vm.swappiness=10` va `net.ipv4.tcp_syncookies=1`. Qo’llagandan keyin
ikkalasi ham kuchda ekanini reboot qilmasdan isbotlang.

**13.** (6) `auditors` guruhiga (uni yarating) `/var/log` ostidagi har bir
faylga faqat o’qish huquqini bering - hozir va keyinroq yaratiladigan
fayllar uchun ham - mavjud egalar yoki guruhlarni o’zgartirmasdan.

**14.** (7) `/srv`’ni `/root/srv-backup.tar.zst`’ga (yoki zstd bo’lmasa
`.tar.gz`’ga) ACL’lar va kengaytirilgan atributlarni saqlagan holda
arxivlang, keyin arxivni ro’yxatlab va bitta nomli faylni `/tmp`’ga
chiqarib tekshiring.

**15.** (7) Tizimda boot paytida `/opt/extra`’ga mount bo’lishi kerak
bo’lgan, lekin bo’lmayotgan mount qilinmagan fayl tizimi bor (buni
o’zingiz tashkil qiling: fstab’ga noto’g’ri satr qo’shing - yaroqsiz
UUID). `mount -a` nega ishlamayotganini aniqlang, tuzating va dastlabki
xatoni `/root/fstab-error.txt`’ga yozing.

---

## To’rtta mock’dan keyin

Ballarni qo’shing. Oxirgi ikkitasida **vaqt ortib qolgan holda** 66% dan
ancha yuqori bo’lsa - tayyorsiz. Faqat har bir daqiqani ishlatib o’tgan
bo’lsangiz, uzun topshiriqlar (LVM, networking, systemd unit’lari)
mexanik bo’lguncha mashq talab qiladi. To’rttasida ham qulagan soha -
qolgan kunlar uchun reja.

Keyin maqsadlar ro’yxatini oxirgi marta o’qing va har bir satr uchun nima
yozishingizni ovoz chiqarib ayting. Javob berolmagan narsangiz - eng
oxirida o’rganiladigan narsa.

:::exam-tip
6-, 10- va 13-topshiriqning bittadan ortiq to’g’ri javobi bor (SGID +
sticky yoki ACL’lar; `Wants=` bilan `After=network-online.target`; sukut
bo’yicha ACL’lar yoki guruh o’zgarishlari). Haqiqiy imtihon ham xuddi
shunday: u **yakuniy holatni** tekshiradi, usulingizni emas. Eng aqllisini
emas, o’zingiz to’g’ri bajarib tekshira oladigan yondashuvni tanlang.
:::

## O’zingizni tekshiring

1. Qaysi topshiriqlarni bir necha usulda yechdingiz va qaysi usul tezroq
   edi?
2. To’rtta mock bo’ylab qaysi soha eng past ball oldi va u bo’yicha
   rejangiz qanday?
3. Oxirgi mock’ingiz vaqt ortib qolgan holda 66% dan yuqori bo’ldimi?
