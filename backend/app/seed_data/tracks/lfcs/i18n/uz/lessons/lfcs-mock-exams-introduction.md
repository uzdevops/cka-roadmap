## Mock’lar nima uchun kerak

To’rtta mock, har biri jonli mashinada bajariladigan amaliy topshiriqlar
to’plami, har biridan keyin esa shu platformada ko’rib chiqish testi. Ular
Linux’ni o’rgandingizmi - buni tekshirmaydi, buni o’n ikki hafta qildi.
Ular buni **ikki soatda, birovning mashinasida, yagona ma’lumot manbai
`man` bilan** bajara olasizmi - shuni tekshiradi. Bu alohida ko’nikma va
uni mashq qilib bo’ladi.

## Imtihon, raqamlarda

| | |
|---|---|
| Format | amaliy: brauzerdagi terminalda, jonli Ubuntu LTS tizimida topshiriqlar |
| Davomiyligi | **2 soat** |
| O’tish bali | **66%** |
| Ma’lumot manbai | imtihon tizimida **`man`, `info`, `--help`** - brauzer yo’q, qaydlar yo’q |
| Sohalar | Operations Deployment 25%, Networking 25%, Storage 20%, Essential Commands 20%, Users and Groups 10% |
| Qayta topshirish | bitta bepul qayta topshirish kiradi |
| Amal qilish muddati | 3 yil |

Band qilayotganingizda joriy raqamlarni Linux Foundation’ning
handbook’idan tasdiqlang - ular qayta ko’rib chiqiladi.

## Mock’ni qanday o’tkazish kerak

1. **Ikki soat, bir o’tirishda, brauzersiz.** Faqat `man`. Agar qidiruv
   tizimiga qo’l cho’zayotganingizni sezsangiz, bu - topilma: uni yozib
   qo’ying va o’rniga `man -k` dan foydalaning.
2. **Avval VM snapshot’ini oling**
   (`virsh snapshot-create-as lab01 pre-mock`). Bir nechta topshiriq
   partition’larni, firewall’larni va user’larni o’zgartiradi; ortga
   qaytarib qayta bajarishingizga to’g’ri keladi.
3. **Tartib bilan ishlang, bemalol o’tkazib yuboring.** Besh daqiqada
   qimirlamagan narsani belgilab qo’ying va oldinga o’ting.
4. **Har bir topshiriqni tashlab ketishdan oldin tekshiring.**
   `systemctl is-active`, `findmnt`, `getent`, `ss -tulpn`, `curl` -
   baholovchi yakuniy holatni tekshiradi, niyatingizni emas.
5. **Ikki soatda to’xtang**, hatto topshiriq o’rtasida bo’lsangiz ham.
   Maqsad - ikki soat sizga nima berishini bilib olish.

## Baholash

Har bir mock o’z topshiriqlarini og’irliklari bilan sanaydi, jami 100.
Topshiriqqa ball faqat yakuniy holat so’ralganidek **aynan** bo’lganda
qo’ying: to’g’ri nom, to’g’ri yo’l, to’g’ri opsiyalar va topshiriqda
"doimiy" deyilgan bo’lsa **doimiy**. Hozir ishlaydigan, lekin fstab’da
bo’lmagan mount - nol, va odamlar ball yo’qotishning eng keng tarqalgan
yo’li aynan shu.

## Xato javob bilan nima qilish kerak

| Nega xato ketdi | Tuzatish |
|---|---|
| buyruqni bilmagan | o’sha darsni qayta o’qing, labini qayta bajaring |
| bilgan, lekin `man` da yetarlicha tez topolmagan | `man -k` ni mashq qiling va qaysi bo’lim ekanini o’rganing (config fayllar uchun 5, admin buyruqlar uchun 8) |
| bilgan, yozgan, tekshirmagan - va u xato edi | tekshiruvni odatingizga qo’shing: har bir topshiriq tekshirish buyrug’i bilan tugaydi |
| doimiy qilishni unutgan | fstab, `systemctl enable`, `sysctl --system`, `--permanent` - refleksni shakllantiring |
| vaqt yetmagan | uzun topshiriqlarni (LVM, bonding, firewall) mexanik bo’lguncha mashq qiling |
| topshiriqni noto’g’ri o’qigan | ikki marta o’qing, nomlar, yo’llar, o’lchamlar va "doimiy" so’zining tagini chizing |

Ro’yxatni saqlang. To’rtta mock taxminan yigirmata satr beradi va ular -
qolgan kunlar uchun o’qish rejangiz.

## Mock’lar orasida

Ularni ketma-ket olmang. 1-mock, keyin uning bo’shliqlarini yopishga bir
kun; 2-mock, xuddi shunday; 3- va 4-mock oxirgi haftada, eng oxirgisi
imtihondan ikki-uch kun oldin. Bir haftadan keyin mock’ni qayta bajarish
birinchi o’tishdan kamroq foyda beradi, lekin baribir arziydi - topshiriq
shakllari haqiqiy imtihonda takrorlanadi.

## Doimiylik ro’yxati

Biror topshiriqni tugadi deyishdan oldin, unga bulardan qaysi biri kerak
bo’lganini o’zingizdan so’rang:

| O’zgarish | Nima bilan doimiy qilinadi |
|---|---|
| mount | `/etc/fstab` + `mount -a` |
| swap | `/etc/fstab` + `swapon --show` |
| service | `systemctl enable --now` |
| sysctl | `/etc/sysctl.d/*.conf` + `sysctl --system` |
| firewall | `ufw enable` / `--permanent` + `--reload` |
| tarmoq manzili | nmcli profili yoki netplan, `ip addr add` emas |
| user limitlari | `/etc/security/limits.d/` |
| SELinux label/port/boolean | `semanage`, `setsebool -P` |
| cron | crontab, shell tsikli emas |

:::tip
Imtihon terminal muhitida sizga qoralama daftar beradi. Mock’lar davomida
ham xuddi shunday matn faylini ochiq tuting: o’tkazib yuborgan topshiriq
raqamlaringiz va qayta ishlatmoqchi bo’lgan buyruqlaringiz. Bu - sizga
ruxsat etilgan yagona "qaydlar", chunki ularni imtihon davomida o’zingiz
yozasiz.
:::

## O’zingizni tekshiring

1. LFCS’ning davomiyligi, o’tish bali va ma’lumot manbai qanday?
2. Bajarilgan topshiriq baribir nol ball olishining eng keng tarqalgan
   sababi nima?
3. Xato javobning beshta toifasini va har birining tuzatilishini ayting.
