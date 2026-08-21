## Rejimni o’qish

```bash
ls -l /etc/passwd /etc/shadow /usr/bin/vim
# -rw-r--r-- 1 root root   2941 ... /etc/passwd
# -rw-r----- 1 root shadow 1347 ... /etc/shadow
# -rwxr-xr-x 1 root root 3.1M  ... /usr/bin/vim
```

```
 - rw- r-- r--
 │ │   │   └── other  (qolgan hamma)
 │ │   └────── group  (fayl guruhi a'zolari)
 │ └────────── user   (egasi)
 └──────────── turi: - fayl, d directory, l link, c/b qurilma, p pipe, s socket
```

Har bir uchlik - **r**ead, **w**rite, e**x**ecute. Qaysi uchlik sizga
tegishli ekani bir marta, shu tartibda hal qilinadi: siz **egasimisiz**?
unda user bitlari, boshqa hech narsa emas. Aks holda, **guruhdamisiz**?
unda group bitlari. Aks holda, other bitlari. (Ya’ni egasi `---`, guruh
`rwx` bo’lgan faylni egasi o’qiy olmaydi - birinchi moslik yutadi.) root
r/w’ni e’tiborga olmaydi va bajarish uchun biror joyda bitta `x` bo’lishi
kifoya.

| Bit | Faylda | Directory’da |
|---|---|---|
| `r` | mazmunini o’qish | ichidagi nomlarni **ro’yxatlash** (`ls`) |
| `w` | mazmunini o’zgartirish | ichida yozuvlarni **yaratish, o’chirish, nomini o’zgartirish** (faylni o’chirish - bu faylga emas, *directory*’ga yozish) |
| `x` | uni dastur sifatida ishga tushirish | ichiga **kirish** (`cd`) va ichidagilarga nomi bo’yicha yetib borish |

`r` bor, `x` yo’q directory: nomlarni ko’rasiz, lekin hech narsani
ocholmaysiz. `x` bor, `r` yo’q: nomini oldindan bilsangiz faylni ocha
olasiz, lekin ro’yxatlay olmaysiz. Ikkalasi ham umumiy directory’lar
uchun muhim.

## chmod: simvolik

```bash
chmod u+x script.sh               # egasiga execute qo'shish
chmod g-w file                    # guruhdan write ni olib tashlash
chmod o=r file                    # other ni aynan r ga qo'yish
chmod a+r file                    # uchchalasi ham (a = ugo)
chmod ug+rw,o-rwx file            # bir vaqtda bir nechtasi
chmod -R g+rX dir/                # rekursiv; katta X: execute faqat directory'larga va allaqachon bajariladigan fayllarga
chmod u=rwx,g=rx,o= dir/
```

`+` qo’shadi, `-` olib tashlaydi, `=` aynan o’rnatadi. `X` - har bir
ma’lumot faylini bajariladigan qilmasdan daraxt bo’ylab yurish mumkin
bo’ladigan xavfsiz usul.

## chmod: octal

| Qiymat | Bit’lar |
|---|---|
| 4 | r |
| 2 | w |
| 1 | x |

Har bir uchlik ichida qo’shing: `rwx`=7, `rw-`=6, `r-x`=5, `r--`=4.

```bash
chmod 644 file        # rw-r--r--   odatiy fayl
chmod 600 ~/.ssh/id_ed25519       # rw-------   maxfiy kalit
chmod 755 script.sh   # rwxr-xr-x   bajariladigan fayl / odatiy directory
chmod 750 dir/        # rwxr-x---
chmod 700 ~/.ssh      # rwx------
chmod 664 shared.txt  # rw-rw-r--
```

To’rtta raqam (`2775`, `4755`, `1777`) maxsus bitlarni oldinga qo’yadi -
keyingi dars.

## chown va chgrp

```bash
chown alice file                  # egasi
chown alice:devs file             # egasi va guruh
chown :devs file                  # faqat guruh  (chgrp devs file bilan bir xil)
chgrp devs file
chown -R alice:devs /srv/project  # rekursiv
chown --reference=a b             # a ning egasi/guruhini b ga ko'chiradi
```

Faylning egasini faqat **root** o’zgartira oladi; egasi esa guruhni
**o’zi a’zo bo’lgan** istalgan guruhga o’zgartira oladi.

## umask: sukut bo’yicha qiymatlar

Yangi fayllar `666 & ~umask`, yangi directory’lar `777 & ~umask` bilan
yaratiladi. Odatdagi `022` umask `644` va `755` beradi; `027` - `640` va
`750`; `077` - `600` va `700`.

```bash
umask                 # 0022
umask 027             # shu shell, hozir
# doimiy qilish uchun: ~/.bashrc yoki /etc/profile.d/umask.sh, yoki /etc/login.defs UMASK
touch f; mkdir d; ls -ld f d
```

## Qilganingizni tekshirish

```bash
ls -l file; stat -c '%A %a %U:%G %n' file       # simvolik va octal bir vaqtda
namei -l /srv/project/data/file.txt             # yo'ldagi har bir directory ruxsati - "nega ular yetib bora olmayapti" vositasi
id; groups alice                                # qaysi uchlik kimga tegishli
sudo -u alice cat /srv/project/data/file.txt    # user nomidan sinab ko'rish
```

:::warning
Directory’dan `x`’ni olib tashlash uning ostidagi hamma narsaga hammaning
yo’lini yopadi, fayllar qanchalik ochiq bo’lmasin - `namei -l` yo’ldagi
eng zaif bo’g’inni ko’rsatadi. `chmod -R 777` esa hech qachon javob emas;
umumiy directory aynan shu yo’l bilan har kim har kimning fayllarini
o’chiradigan joyga aylanadi (haqiqiy yechim - keyingi darsdagi sticky
bit).
:::

:::exam-tip
Topshiriqlar shunday yoziladi: "`/srv/data`’ni `devs` guruhi uchun o’qish
va yozishga ochiq, boshqalar uchun yopiq qiling":
`chgrp -R devs /srv/data; chmod -R 770 /srv/data` (yoki yangi fayllarda
guruhni saqlash uchun `2770` - keyingi dars). `ls -ld` bilan va ichkarida
`ls -l` bilan tekshiring. "Faylni faqat egasi o’qiy olsin": `chmod 600`.
:::

## O’zingizni tekshiring

1. Fayl `-rw-r-----  root shadow` ko’rinishida. Uni kim o’qiy oladi?
2. Directory’dagi `w` nimaga ruxsat beradi va nega foydalanuvchi o’zi
   yoza olmaydigan faylni o’chira oladi?
3. `umask 027` yangi fayllar va directory’larga qanday ruxsatlar beradi?
