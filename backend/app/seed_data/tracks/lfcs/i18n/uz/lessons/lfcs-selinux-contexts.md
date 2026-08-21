## Hamma narsada label’lar

SELinux (Security-Enhanced Linux) odatdagi egalik/ruxsat modeli ustiga
**mandatory access control** qo’shadi: har bir process va har bir fayl
**label** olib yuradi, policy esa qaysi process label’lari qaysi fayl
label’lariga tegishi mumkinligini hal qiladi. Hatto root ham unga
bo’ysunadi.

RHEL oilasida u sukut bo’yicha yoqilgan; Ubuntu’da ekvivalenti AppArmor,
lekin LFCS maqsadlari SELinux’ni nomlaydi, shuning uchun u shu yerda
o’rgatiladi.

```bash
getenforce                # Enforcing | Permissive | Disabled
sestatus                  # to'liqroq hisobot: rejim, policy, u yuklanganmi
id -Z                     # SIZNING context'ingiz
ls -Z /var/www/html       # fayl context'lari
ps -eZ | head             # process context'lari
```

## Context’ni o’qish

```
system_u:object_r:httpd_sys_content_t:s0
    │        │            │            └── level (MLS/MCS; targeted policy'da s0)
    │        │            └── TYPE  ← deyarli har doim ahamiyatli bo'lgan qism
    │        └── role (fayllar uchun object_r, process'lar uchun system_r)
    └── user (SELinux user'i, Unix user'i emas)
```

Kundalik SELinux ishining deyarli hammasi **tip** haqida. Kelishuv:
process tiplari `_t` bilan tugaydi va **domen** deb ataladi (`httpd_t`,
`sshd_t`); fayl tiplari ham `_t` bilan tugaydi (`httpd_sys_content_t`,
`ssh_home_t`). Policy, masalan, "`httpd_t` dagi process
`httpd_sys_content_t` deb belgilangan fayllarni o’qishi mumkin" deydi - va
boshqa hech narsani emas.

```bash
ls -Z /var/www/html/index.html
# -rw-r--r--. root root unconfined_u:object_r:httpd_sys_content_t:s0 index.html
ps -eZ | grep httpd
# system_u:system_r:httpd_t:s0     1234 ?  00:00:00 httpd
ls -Z /etc/ssh/sshd_config
ls -dZ /home/ahmad
```

Oddiy `ls -l` da ruxsatlardan keyin turgan `.` "bu faylda SELinux context’i
bor" degani (`+` esa unda ACL borligini bildiradi).

## Label qayerdan keladi

- Fayllar o’zi yaratilgan katalogning label’ini **meros qilib oladi** -
  shuning uchun `/var/www` ichiga *ko’chirilgan* (`mv`) fayl eski label’ini
  saqlaydi, *nusxalangan* (`cp`) fayl esa yangisini oladi.
- Policy’da har bir yo’l uchun sukut bo’yicha label’lar bazasi bor
  (`semanage fcontext -l`); undan `restorecon` va qayta belgilash paytida
  foydalaniladi.

```bash
semanage fcontext -l | grep '/var/www'
# /var/www(/.*)?    all files    system_u:object_r:httpd_sys_content_t:s0
matchpathcon /var/www/html/index.html      # label QANDAY bo'lishi kerakligi
restorecon -v /var/www/html/index.html     # qanday bo'lishi kerak bo'lsa, shunday qiladi
restorecon -Rv /var/www                     # rekursiv
```

## Tanib olish kerak bo’lgan alomat

Unix ruxsatlari to’g’ri bo’lsa ham "Permission denied" oladigan service -
va faylning label’i noto’g’ri ko’rinsa - bu SELinux.

```bash
sudo ausearch -m avc -ts recent            # AVC denial'lari (bloklashning audit yozuvi)
sudo ausearch -m avc -ts today | audit2why # tushunarli tilda, taklif qilingan yechim bilan
sudo tail /var/log/audit/audit.log | grep denied
sudo journalctl -t setroubleshoot          # setroubleshoot o'rnatilgan bo'lsa: sodda tildagi maslahat
```

```
type=AVC msg=audit(...): avc: denied { read } for pid=1234 comm="httpd"
  name="index.html" dev="dm-0" ino=12345
  scontext=system_u:system_r:httpd_t:s0
  tcontext=unconfined_u:object_r:user_home_t:s0 tclass=file
```

Buni shunday o’qing: `httpd_t` dagi process `user_home_t` deb belgilangan
faylni `read` qilmoqchi bo’ldi, policy esa yo’q dedi. Yechim - faylga
to’g’ri label berish, SELinux’ni o’chirib qo’yish emas.

## Rejimlar

```bash
getenforce
sudo setenforce 0          # Permissive: denial'larni logga yozadi, hammasiga ruxsat beradi - VAQTINCHALIK, diagnostika uchun
sudo setenforce 1          # Enforcing
cat /etc/selinux/config    # SELINUX=enforcing|permissive|disabled  ← doimiy, reboot kerak
```

Permissive - bu **diagnostika** holati: agar muammo permissive rejimda
yo’qolsa, demak bu SELinux, va `ausearch` endi rad etilishi mumkin bo’lgan
hamma narsani ro’yxatlaydi. Keyin qayta belgilang va enforcing’ga qayting.
Tuzatish keyingi darsda.

:::warning
`/etc/selinux/config` dagi `SELINUX=disabled` label qo’yishni butunlay
to’xtatadi; uni qaytadan yoqqaningizda fayl tizimi to’liq qayta belgilashni
talab qiladi (`sudo touch /.autorelabel && reboot`), bu katta diskda uzoq
vaqt oladi. Agar bo’shashtirish shart bo’lsa, `disabled` o’rniga
`permissive` ni tanlang.
:::

:::exam-tip
Bu maqsad uchun odatda faqat **ro’yxatlash va aniqlash** so’raladi: yo’lga
`ls -Z`, process uchun `ps -Z`, o’zingiz uchun `id -Z` va rejim uchun
`getenforce`/`sestatus` - ko’pincha chiqishni faylga yozish bilan. Uchinchi
maydon tip ekanini va aynan o’sha muhimligini biling.
:::

## O’zingizni tekshiring

1. SELinux context’ining to’rtta maydoni qaysilar va kundalik ish
   qaysinisiga tegishli?
2. Nega `/var/www` ichiga `mv` qilish ko’pincha web server’ni buzadi,
   `cp` esa buzmaydi?
3. `ausearch -m avc` dagi denial sizga scontext va tcontext nuqtai
   nazaridan nimani aytadi?
