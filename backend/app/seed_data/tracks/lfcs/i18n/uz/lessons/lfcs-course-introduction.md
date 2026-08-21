## LFCS nima

Linux Foundation Certified System Administrator - amaliy imtihon: jonli
Linux tizimida terminal oldida ikki soat, topshiriqlar esa "hisobi ma’lum
sanada tugaydigan user yarating", "bu filesystem boot paytida mount
bo’lsin", "8080 portni 80 ga yo’naltiring", "har dushanba ishlaydigan cron
job sozlang" ko’rinishida. Variantlardan tanlash yo’q. Siz buni mashinada
bajardingiz yoki bajarmadingiz.

Bu - shu platformadagi Kubernetes yo’nalishlari nazarda tutadigan Linux
qismi. `ssh node01; journalctl -u kubelet` bilan tugaydigan har bir CKA
nosozlik topshirig’i - LFCS ko’nikmasi; istalgan bulutdagi har bir storage
yoki networking savoli ham shunday.

## Bu yo’nalish nima qiladi

O’n uch hafta, olti bosqich, yetmish to’qqiz dars, har biri rasmiy
maqsadlar ro’yxatidagi bitta satrga bog’langan:

| Bosqich | Haftalar | Soha |
|---|---|---|
| Essential commands | 1-4 | konsollar, hujjatlar, fayllar, linklar, ruxsatlar, qidiruv, matn, regex, arxivlar, redirection, SSL, Git |
| Operations deployment | 5-7 | boot va target’lar, skriptlash, systemd service’lari, jarayonlar, loglar, rejalashtirish, paketlar, kernel parametrlari, SELinux, konteynerlar, VM’lar |
| Users and groups | 8 | hisoblar, guruhlar, muhit, limitlar, sudo, root, LDAP |
| Networking | 9-10 | IPv4/IPv6, service’lar, bridge va bond’lar, firewall’lar, NAT, reverse proxy’lar, vaqt, SSH |
| Storage | 11-12 | partition’lar, swap, fayl tizimlari, fstab, mount opsiyalari, NFS, NBD, LVM, unumdorlik, ACL’lar |
| Exam prep | 13 | vaqt bilan o’lchanadigan to’rtta mock va xulosa |

Har bir dars: tushuncha bir-ikki ekranda, siz yozadigan buyruqlar, jadval
tushunarliroq bo’lgan joyda jadval, odamlar kuyadigan joyda ogohlantirish va
yoddan javob beriladigan uchta savol. Har bir hafta haqiqiy mashinadagi lab
va qisqa test bilan tugaydi.

## Buni qanday o’rganish kerak

- **Har bir buyruqni yozing.** `chmod 2775`’ni o’qish - uni yozib,
  `ls -l`’da `s` paydo bo’lganini ko’rish bilan bir xil emas. Kerakli yagona jihoz -
  VM (7-haftaga qarang) yoki buzsangiz bo’ladigan istalgan Linux mashinasi.
- **man sahifasini dars aytishidan oldin oching.** Imtihon sizga `man`’dan
  boshqa hech narsa bermaydi; unga qo’l cho’zish odati bayroqlarni yodlashdan
  qimmatroq.
- **Cheat sheet’ni** (shu haftaning 4-darsi) ochiq tuting va unga qo’shib
  boring.
- **Lab’ni testdan oldin bajaring**, keyin emas - test lab’ni tekshiradi.

:::tip
Agar sizda CKA bo’lsa, 1-3 haftalar tanish tuyuladi va tez o’tasiz; yangi
material 5, 7, 10 va 12-haftalarda (systemd unit’lari, SELinux, NAT, LVM).
Noldan boshlayotgan bo’lsangiz, tartib bilan boring - keyingi haftalar
birinchi uchtasining redirection va ruxsatlarini nazarda tutadi.
:::

## O’zingizni tekshiring

1. LFCS qanday turdagi imtihon va bu o’rganish uslubingiz uchun nimani
   anglatadi?
2. Beshta sohani va ularni qamrab oladigan hafta raqamlarini ayting.
3. Bu yo’nalish uchun qanday yagona jihoz kerak?
