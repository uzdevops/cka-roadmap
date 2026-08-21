## Kim root bo’la oladi

Har qanday mashinada javob berish kerak bo’lgan uchta savol: root’da parol
bormi, root to’g’ridan-to’g’ri tizimga kira oladimi va kim root bo’la
oladi.

```bash
sudo passwd -S root
# root L 08/19/2026 0 99999 7 -1     ← L = qulflangan (Ubuntu'da sukut holat)
# root P ...                          ← P = ishlaydigan parol o'rnatilgan
sudo grep '^root:' /etc/shadow | cut -d: -f2 | head -c3    # ! yoki * = parol bilan login yo'q
grep PermitRootLogin /etc/ssh/sshd_config
getent group sudo wheel
sudo -l -U alice
```

## Root’ni qulflash va qulfini ochish

```bash
sudo passwd -l root            # parolni qulflash (hash oldiga ! qo'yiladi)
sudo passwd -u root            # qulfni ochish
sudo passwd root               # parol o'rnatish
sudo passwd -d root            # parolni butunlay o'chirish - BO'SH parol, buni qilmang
sudo usermod -s /usr/sbin/nologin root      # root'ga shell'ni taqiqlash (keskin chora; rescue va ba'zi skriptlarni buzadi)
```

Ubuntu root’ni **qulflangan** holda yetkazadi: parol yo’qligi `su -` yo’q,
root sifatida konsolga kirish yo’q va root sifatida SSH parol login’i yo’q
degani. Administratsiya hamma narsani logga yozadigan `sudo` orqali
boradi. RHEL esa o’rnatish paytida root parolini o’rnatadi.

Parolni qulflash SSH **kaliti** bilan root login’ini **to’xtatmaydi** va
`sudo -i`’ni ham to’xtatmaydi. U faqat parol eshigini yopadi.

## SSH orqali to’g’ridan-to’g’ri root login

```bash
sudo vi /etc/ssh/sshd_config
```

```
PermitRootLogin no                  # umuman root login yo'q - odatiy siyosat
# PermitRootLogin prohibit-password # kalitlarga ruxsat, parollarga yo'q (OpenSSH sukut holati)
# PermitRootLogin forced-commands-only
# PermitRootLogin yes               # bundan qoching
```

```bash
sudo sshd -t                        # reload'dan OLDIN sintaksisni tekshirish
sudo systemctl reload sshd
```

Tarmoqdan yetib boriladigan har qanday narsa uchun siyosat - `no`: root -
har bir hujumchi allaqachon biladigan yagona username, shuning uchun
brute-force urinishlarida muammoning yarmi hal bo’lgan bo’ladi. O’zingiz
bo’lib kiring, so’ng `sudo`.

## Konsol va single-user kirish

Fizik (yoki virtual konsol) kirish - butunlay boshqa masala: konsol
yonidagi odam `rescue.target` yoki `init=/bin/bash` bilan yuklanib, hech
qanday parolsiz root bo’la oladi (operating modes darsi). Agar bu muhim
bo’lsa:

```bash
sudo grub2-setpassword                       # RHEL: GRUB tahrirlarini parol bilan himoyalash
# Debian: /etc/grub.d/40_custom ichida superusers/password_pbkdf2 ni o'rnating, so'ng update-grub
```

Ustiga disk shifrlash yoki fizik xavfsizlik. Bularsiz "root paroli
qulflangan" degani klaviatura yonidagi odamdan hech nimani himoya
qilmaydi.

## Root qaysi terminallardan foydalana oladi

```bash
cat /etc/securetty         # mavjud bo'lsa: root kira oladigan YAGONA TTY'lar (bo'sh fayl = hech qaysi)
```

Zamonaviy tizimlar bu faylni ko’pincha tashlab yuborgan; u mavjud bo’lsa,
uni bo’shatish root’ning konsol login’ini butunlay taqiqlaydi - boshqa
kirish yo’li bo’lmasa, bu xavfli.

## su’ni cheklash

```bash
sudo grep -n pam_wheel /etc/pam.d/su
# auth required pam_wheel.so use_uid           ← izohdan chiqaring: faqat wheel/sudo a'zolari `su` qila oladi
sudo groupadd -r wheel 2>/dev/null; sudo usermod -aG wheel alice
```

Busiz root parolini bilib qolgan har qanday user `su -` qila oladi. Bu
bilan esa ular yana guruh a’zosi ham bo’lishi shart.

## Aqlli siyosat

| Sozlama | Qiymat | Nega |
|---|---|---|
| root paroli | qulflangan (yoki uzun va vault’da saqlanadi) | sizib chiqadigan umumiy sir yo’q |
| `PermitRootLogin` | `no` | hujumlar root’ni nomi bilan nishonga oladi |
| admin kirishi | guruh orqali `sudo` | logga yoziladi, har bir odam uchun alohida bekor qilinadi |
| `NOPASSWD` | faqat aniq avtomatlashtirish buyruqlari uchun | o’g’irlangan sessiya indamas root bo’lib qolmasin |
| `su` | `pam_wheel` bilan cheklangan | qatlamli himoya |
| konsol/GRUB | parol yoki fizik xavfsizlik | aks holda yuqoridagilarning hammasini chetlab o’tish mumkin |
| audit | `journalctl _COMM=sudo`, `/var/log/auth.log` | kim, nima qilgan, qachon |

```bash
sudo grep -E "sudo:|su:" /var/log/auth.log | tail
sudo journalctl _COMM=su --since today
last root
sudo lastb | head                    # muvaffaqiyatsiz loginlar - brute force urinishlari
```

## Agar tashqarida qolib ketsangiz

Root paroli yo’qolgan, ishlaydigan sudo user’i yo’q:
`systemd.unit=rescue.target` bilan yuklang (root parolini so’raydi - u
noma’lum bo’lsa foydasiz) yoki `init=/bin/bash` bilan, so’ng

```bash
mount -o remount,rw /
passwd root
# yoki: usermod -aG sudo alice
exec /sbin/init
```

Shu besh qatorli retsept konsolga kirish root’ga kirish bilan teng
ekanining ham sababi.

:::exam-tip
Kutiladigani: "root SSH orqali kira olmasin" → `PermitRootLogin no` +
`sshd -t` + `systemctl reload sshd`, tekshiruv - `ssh root@localhost` rad
etilishi. "root account’ini qulflang" → `passwd -l root`, tekshiruv -
`passwd -S root` `L` ko’rsatishi. O’zingizni tashqarida qoldirmang: root
kirishini o’zgartirishdan **oldin** o’z sudo’ingiz ishlashiga ishonch
hosil qiling.
:::

## O’zingizni tekshiring

1. `passwd -l root` nimani to’xtatadi va nimani to’xtatmaydi?
2. To’g’ridan-to’g’ri root login’ini sshd_config’ning qaysi sozlamasi
   boshqaradi va uning foydali qiymatlari qanday?
3. Nega qo’shimcha choralar ko’rilmasa konsolga kirish root’ga kirish
   bilan teng?
