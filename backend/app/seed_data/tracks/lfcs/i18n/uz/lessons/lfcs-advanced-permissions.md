## rwx yetarli bo’lmaganda

Standart ruxsatlar aynan uchta subyektni tavsiflaydi: bitta ega, bitta
guruh, qolgan hamma. "alice yoza olsin, devs guruhi o’qiy olsin, bob
o’qiy olsin, boshqa hech kim yo’q" uchun to’rtinchisi kerak - **ACL’lar**
aynan shuni beradi.

```bash
ls -l report.txt
# -rw-rw-r--+ 1 ahmad devs 1234 Aug 21 10:00 report.txt
#           ↑ + belgisi bu faylda ACL borligini bildiradi
```

Talablar: fayl tizimi `acl` bilan mount qilingan bo’lishi kerak
(zamonaviy distributivlarda ext4 va xfs uni sukut bo’yicha yoqadi).

```bash
sudo apt install acl
findmnt -o TARGET,OPTIONS /home
sudo mount -o remount,acl /home        # faqat u yo'q bo'lsa
```

## ACL’larni o’qish va o’rnatish

```bash
getfacl report.txt
# file: report.txt
# owner: ahmad
# group: devs
user::rw-
user:bob:r--                 ← nomlangan foydalanuvchi
group::rw-
group:qa:r--                 ← nomlangan guruh
mask::rw-                    ← barcha nomlangan yozuvlar va guruh uchun YUQORI CHEGARA
other::r--
```

```bash
setfacl -m u:bob:rw report.txt            # modify: bob'ga o'qish+yozish berish
setfacl -m g:qa:r report.txt              # guruh
setfacl -m u:bob:rwx,g:qa:rx dir/         # bir vaqtda bir nechtasi
setfacl -R -m g:devs:rwx /srv/project     # rekursiv
setfacl -x u:bob report.txt               # bob'ning yozuvini olib tashlash
setfacl -b report.txt                     # HAMMA ACL'larni olib tashlash
setfacl -m m:r report.txt                 # mask'ni aniq o'rnatish
getfacl a.txt | setfacl --set-file=- b.txt        # ACL'ni bir fayldan boshqasiga ko'chirish
```

## Mask, va nega ruxsatlar "ishlamaydi"

`mask` - har bir **nomlangan** foydalanuvchi, har bir nomlangan guruh va
egalik qiluvchi guruh uchun yuqori chegara. `r--` mask ostidagi `rwx`
yozuv faqat `r` beradi. ACL’i bor faylda `chmod g+w file` guruh yozuvini
emas, **mask**’ni o’zgartiradi - shuning uchun ACL’lar chmod’dan keyin
goho ishlashdan to’xtagandek ko’rinadi.

```bash
getfacl report.txt | grep -E "mask|effective"
# group:qa:rwx                 #effective:r--     ← mask uni cheklayapti
setfacl -m m:rwx report.txt    # mask'ni ko'tarish
```

`getfacl` chiqishidagi `#effective:`’ni "bu yozuv aslida nima beradi" deb
o’qing.

## Default ACL’lar: meros

Directory’dagi **default** ACL uning ichida yaratilgan hamma narsaga
meros bo’ladi - bu SGID’ning ACL’dagi ekvivalenti.

```bash
setfacl -d -m u:bob:rwx /srv/project          # -d = default
setfacl -d -m g:devs:rwx /srv/project
setfacl -d -m o::--- /srv/project
getfacl /srv/project
# default:user:bob:rwx
# default:group:devs:rwx
touch /srv/project/newfile
getfacl /srv/project/newfile                   # bob va devs allaqachon o'sha yerda
setfacl -k /srv/project                        # default ACL'ni olib tashlash
```

Qo’shimcha mehmoni bor umumiy loyiha directory’si uchun to’liq retsept:

```bash
sudo mkdir -p /srv/project
sudo chgrp devs /srv/project
sudo chmod 2770 /srv/project                        # SGID: guruh egaligi meros bo'ladi
sudo setfacl -m u:bob:rwx /srv/project              # devs'da bo'lmagan bob
sudo setfacl -d -m u:bob:rwx /srv/project           # ...va keyin yaratilgan hamma narsaga
sudo setfacl -d -m g:devs:rwx /srv/project
getfacl /srv/project
```

## ACL’larni backup qilish va tiklash

```bash
getfacl -R /srv/project > acl-backup.txt
setfacl --restore=acl-backup.txt
cp -a src dst                     # -a ACL'larni saqlaydi
rsync -aHAX src/ dst/             # -A ACL'lar, -X kengaytirilgan atributlar
tar --acls --xattrs -czf backup.tar.gz /srv/project
```

Oddiy `cp` va oddiy `tar` ACL’larni **tashlab yuboradi** - tiklangan
directory’da kirish huquqlari to’satdan boshqacha bo’lib qolishining
sababi shu.

## Fayl atributlari: chattr

Fayl tizimining o’zi majburlaydigan boshqa mexanizm; yozishdan oldin uni
hatto root ham olib tashlashi kerak:

```bash
lsattr file.txt
sudo chattr +i /etc/resolv.conf        # IMMUTABLE: o'zgartirib, o'chirib, nomini almashtirib yoki link qilib bo'lmaydi - hatto root ham
sudo chattr -i /etc/resolv.conf
sudo chattr +a /var/log/audit.log      # APPEND-ONLY: yozuvlar faqat oxiriga qo'shilishi mumkin
sudo chattr +A file                    # atime'ni yangilamaslik
sudo chattr -R +i /etc/critical/
lsattr -d /etc/critical/
```

```bash
sudo lsattr /etc/resolv.conf
# ----i---------e------- /etc/resolv.conf
```

`+i` - "nimadir bu faylni doim qayta yozyapti" muammosining javobi
(masalan, `resolv.conf`’ni qayta yozadigan DHCP klienti) - va root
sifatida boshni qotiradigan "Operation not permitted" ning sababi. Root
faylni o’chira olmasa, birinchi tekshiriladigan narsa - `lsattr`.

## Kengaytirilgan atributlar

ACL’lar, SELinux kontekstlari va capability’lar - hammasi **xattr**
sifatida saqlanadi:

```bash
getfattr -d -m - file                       # hamma xattr'lar
getfattr -n security.selinux file
sudo setfattr -n user.comment -v "reviewed" file
sudo setcap cap_net_bind_service=+ep /usr/local/bin/myserver   # root bo'lmasdan 80-portga bind qilish
getcap /usr/local/bin/myserver
sudo setcap -r /usr/local/bin/myserver
```

`setcap` - SUID binary’ga zamonaviy muqobil: to’liq root o’rniga bitta
capability berish.

## Kirish muammolarini diagnostika qilish

```bash
namei -l /srv/project/data/file.txt        # yo'lning HAR BIR qismidagi ruxsatlar
getfacl file; ls -l file; lsattr file
id bob; groups bob
sudo -u bob cat /srv/project/data/file.txt        # foydalanuvchi nomidan sinash
sudo -u bob test -w /srv/project && echo writable
ls -Z file                                         # SELinux, agar enforcing bo'lsa (7-hafta)
```

Tekshirish tartibi: yo’l bo’ylab o’tish (`namei -l`), keyin
egasi/guruhi/rejimi, keyin ACL va uning mask’i, keyin atributlar
(`lsattr`), keyin SELinux/AppArmor.

:::exam-tip
"X foydalanuvchisiga F faylga, guruhini o’zgartirmasdan, o’qish-yozish
huquqini bering" → `setfacl -m u:X:rw F`, `getfacl F` bilan
tekshiriladi. "...va keyinchalik D directory’sida yaratilgan hamma
narsaga ham" → `setfacl -d -m u:X:rwx D`. Ruxsatlar to’g’ri ko’rinsa-yu,
kirish rad etilsa, **mask**’ni (`#effective:`) va `lsattr`’ni tekshiring.
:::

## O’zingizni tekshiring

1. `ls -l` rejimining oxiridagi `+` nimani anglatadi?
2. ACL mask nima, va nega `chmod g+w` ACL’ni buzishi mumkin?
3. Root faylni o’chira olmayapti va "Operation not permitted" olyapti.
   Siz nimani tekshirasiz?
