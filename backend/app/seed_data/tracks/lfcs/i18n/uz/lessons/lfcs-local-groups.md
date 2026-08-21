## Asosiy va qo’shimcha

Har bir user’da aynan bitta **asosiy (primary)** guruh bo’ladi
(`/etc/passwd`’dagi GID, u yaratgan fayllar uchun ishlatiladi) va istalgan
sondagi **qo’shimcha (supplementary)** guruh bo’ladi (`/etc/group`’da
ro’yxatlanadi).

```bash
id alice
# uid=1001(alice) gid=1001(alice) groups=1001(alice),27(sudo),1005(developers)
#                   └── asosiy             └── qo'shimcha
groups alice
getent group developers
# developers:x:1005:alice,bob
```

`/etc/group` maydonlari: `name:x:GID:members`. Asosiy guruhning a’zolari
odatda u yerda **ko’rsatilmaydi** - a’zolik `/etc/passwd`’dagi GID’dan
keladi; shuning uchun user’larda u asosiy guruh bo’lsa ham `getent group
developers` bo’sh ko’rinishi mumkin.

Debian ham, RHEL ham sukut bo’yicha **user private group** ishlatadi:
`alice` user’i asosiy guruh sifatida `alice` guruhini oladi, shuning uchun
sukut bo’yicha 002 umask xavfsiz.

## Guruh yaratish va o’chirish

```bash
sudo groupadd developers
sudo groupadd -g 5000 developers        # aniq GID
sudo groupadd -r appgroup               # system guruh (past GID)
sudo groupmod -n devs developers        # nomini o'zgartirish
sudo groupmod -g 5001 devs              # GID'ni o'zgartirish (fayllarda ESKI gid qoladi - find -gid bilan tuzating)
sudo groupdel devs                      # kimningdir ASOSIY guruhi bo'lsa rad etadi
```

## A’zolikni boshqarish

```bash
sudo usermod -aG developers alice       # qo'shish (-a shart)
sudo gpasswd -a alice developers        # qo'shish - niyat aniqroq
sudo gpasswd -d alice developers        # olib tashlash
sudo gpasswd -M alice,bob,carol devs    # a'zolar ro'yxatini aynan o'rnatish
sudo gpasswd -A alice devs              # alice'ni guruh administratori qilish
sudo usermod -g developers alice        # ASOSIY guruhni o'zgartirish
```

A’zolikdagi o’zgarish **mavjud sessiyalarga** ta’sir qilmaydi: user’ning
process’lari login paytida olgan guruh to’plamini saqlab qoladi.

```bash
groups                                  # mening shell'imda nima bor
id alice                                # fayllar nima deydi - bular farq qilishi mumkin!
newgrp developers                       # yangi guruh faol bo'lgan subshell'ni ishga tushirish
# yoki: chiqib, qaytadan kiring
```

Bu - "o’zimni docker guruhiga qo’shdim, lekin baribir permission denied
olyapman" degan savolning javobi.

## Fayllar va guruhlar

```bash
chgrp developers /srv/project
chgrp -R developers /srv/project
chmod 2775 /srv/project                 # SGID: yangi fayllar guruhni meros oladi (2-hafta)
find /srv -group olddevs -exec chgrp devs {} +
find / -xdev -nogroup 2>/dev/null       # guruhi endi mavjud bo'lmagan fayllar
```

Umumiy directory uchun to’liq namuna:

```bash
sudo groupadd project-x
sudo usermod -aG project-x alice
sudo usermod -aG project-x bob
sudo mkdir -p /srv/project-x
sudo chgrp project-x /srv/project-x
sudo chmod 2770 /srv/project-x          # egasi va guruh uchun rwx, boshqalarga hech narsa, SGID
ls -ld /srv/project-x                    # drwxrws--- root project-x
```

## Ma’noga ega guruhlar

| Guruh | Nima beradi |
|---|---|
| `sudo` (Debian) / `wheel` (RHEL) | `sudo` ishlatish huquqi (sudoers qoidasi orqali) |
| `adm` | ko’pchilik log fayllarini o’qish |
| `docker` | docker daemon’i ustidan to’liq nazorat - **root’ga teng** |
| `libvirt`, `kvm` | virtual mashinalarni boshqarish |
| `dialout`, `plugdev`, `audio`, `video` | serial portlar, olinadigan qurilmalar, hardware |
| `shadow` | `/etc/shadow`’ni o’qish |

User’ni `docker`, `libvirt` yoki `sudo` guruhiga qo’shish - qulaylik
haqidagi emas, imtiyoz haqidagi qaror.

## Guruh parollari, qisqacha

`/etc/gshadow` guruh parolini saqlashi mumkin - shunda a’zo bo’lmagan user
guruhga `newgrp` bilan kira oladi. Bu kamdan-kam ishlatiladi va deyarli
har doim user’ni guruhga qo’shish yaxshiroq javob bo’ladi.

```bash
sudo gpasswd developers        # guruh parolini o'rnatish
sudo gpasswd -r developers     # uni olib tashlash
```

## Qilganingizni tekshirish

```bash
id alice; groups alice
getent group developers
grep developers /etc/group
awk -F: '$3>=1000 {print $1, $3}' /etc/group      # system bo'lmagan guruhlar
lslogins -g developers
sudo grpck                                          # izchillik tekshiruvi
```

:::exam-tip
"X guruhini yarating va unga A va B user’larini qo’shing, so’ng /srv/x ni
guruh uchun yozishga ochiq qiling":
`groupadd X; usermod -aG X A; usermod -aG X B; chgrp X /srv/x;
chmod 2770 /srv/x`. `getent group X`, `id A` va `ls -ld
/srv/x` bilan tekshiring. Esda tuting: `groupdel` asosiy guruhni rad
etadi, a’zolik esa kuchga kirishi uchun yangi login talab qiladi.
:::

## O’zingizni tekshiring

1. Asosiy va qo’shimcha guruh o’rtasidagi farq nima va ularning har biri
   qayerda qayd etiladi?
2. User endigina guruhga qo’shildi, lekin baribir "permission denied"
   olyapti. Nega va ikkita yechim qanday?
3. `/srv/team`’ni `team` guruhi uchun umumiy directory qiladigan va yangi
   fayllar guruh egaligi `team` bo’lib qoladigan buyruqlarni yozing.
