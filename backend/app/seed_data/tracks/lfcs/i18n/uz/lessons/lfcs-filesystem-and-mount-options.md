## Option’lar filesystem nimaga ruxsat berishini o’zgartiradi

fstab’ning to’rtinchi maydoni va `mount -o`. Ba’zilari unumdorlik uchun,
ba’zilari xavfsizlik uchun, bir nechtasi esa audit topilmasiga standart
javob.

```bash
findmnt                       # har bir mount va uning option'lari
findmnt /mnt/data -o TARGET,SOURCE,FSTYPE,OPTIONS
mount | grep /mnt/data
cat /proc/mounts              # kernel'ning ko'rinishi - asosiysi shu
```

## Xavfsizlik uchligi

| Option | Ta’siri |
|---|---|
| `noexec` | bu filesystem’dagi hech qaysi binary **bajarilmaydi** |
| `nosuid` | bu yerda SUID/SGID bit’lar **e’tiborga olinmaydi** |
| `nodev` | bu filesystem’dagi device node’lar **tan olinmaydi** |

```
UUID=... /home     ext4  defaults,nodev,nosuid          0 2
UUID=... /var/log  ext4  defaults,nodev,nosuid,noexec   0 2
UUID=... /tmp      ext4  defaults,nodev,nosuid,noexec   0 2
tmpfs    /dev/shm  tmpfs defaults,nodev,nosuid,noexec   0 0
```

`/tmp`, `/var/tmp`, `/dev/shm` va `/home` uchun `noexec,nosuid,nodev` -
klassik hardening to’plami: `/tmp`’ga tashlangan skript ishga tushmaydi,
u yerga qo’yilgan SUID binary esa hech narsa bermaydi. (Ba’zi paket
menejerlari `/tmp` ichida build qiladi va shikoyat qiladi - yechim
`/var/tmp` yoki boshqa joydagi build directory.)

## Unumdorlik va xatti-harakat

| Option | Ta’siri |
|---|---|
| `noatime` | murojaat vaqtlari hech qachon yangilanmaydi - kamroq yozuv, deyarli hamma narsa uchun xavfsiz |
| `relatime` | atime’ni faqat u mtime’dan eski bo’lsa yangilaydi (zamonaviy **sukut** qiymati) |
| `nodiratime` | noatime kabi, faqat directory’lar uchun |
| `async` / `sync` | yozuvlarni buferlaydi (sukut) / darhol yozib yuboradi (sekin, xavfsizroq) |
| `discard` | o’chirishda SSD’ga TRIM yuboradi (haftalik `fstrim.timer` afzalroq) |
| `errors=remount-ro` | ext4: xatoda buzishda davom etmasdan faqat o’qishga o’tadi |
| `barrier=1` | write barrier’lar yoqiq (sukut; batareyali kontrollersiz o’chirmang) |
| `data=ordered\|writeback\|journal` | ext4 journal rejimi: xavfsizlikka qarshi tezlik |

## Kirish va mount qilish xatti-harakati

| Option | Ta’siri |
|---|---|
| `ro` / `rw` | faqat o’qish / o’qish-yozish |
| `auto` / `noauto` | `mount -a` bilan (va boot’da) mount qilinadi yoki yo’q |
| `user` / `nouser` | oddiy foydalanuvchi uni mount qila oladimi (noexec,nosuid,nodev’ni nazarda tutadi) |
| `owner` | uni faqat qurilma egasi mount qila oladi |
| `nofail` | qurilma yo’q bo’lsa boot’ni buzmaydi |
| `_netdev` | mount qilishdan oldin tarmoqni kutadi |
| `x-systemd.automount` | birinchi murojaatda mount qiladi |
| `x-systemd.device-timeout=5` | qurilmani qancha kutish kerakligi |
| `defaults` | `rw,suid,dev,exec,auto,nouser,async` |

## Unix ruxsatlari yo’q filesystem’lar uchun egalik option’lari

vfat, exfat, ntfs va ko’pchilik tarmoq share’lari Unix egaligini saqlay
olmaydi, shuning uchun u mount paytida beriladi:

```
/dev/sdc1 /mnt/usb vfat uid=1000,gid=1000,umask=022,noexec,nosuid,nodev 0 0
//srv/share /mnt/share cifs credentials=/etc/cifs.cred,uid=1000,gid=1000,_netdev 0 0
```

```bash
sudo mount -o uid=1000,gid=1000,umask=077 /dev/sdc1 /mnt/usb
```

## Unmount qilmasdan option’larni o’zgartirish

```bash
sudo mount -o remount,ro /mnt/data
sudo mount -o remount,rw /mnt/data
sudo mount -o remount,noexec /tmp
sudo mount -o remount,rw /                    # emergency rejimidagi birinchi buyruq
findmnt /tmp -o OPTIONS                        # tasdiqlash
```

`remount` **qurilma** uchun fstab’ni o’qimaydi, faqat sukut qiymatlari
uchun o’qiydi - shuning uchun keyin doim `findmnt` bilan tekshiring va
fstab’ni ham yangilang, aks holda o’zgarish keyingi boot’da yo’qoladi.

## Quota’lar, qisqacha

```bash
sudo apt install quota
# fstab:  UUID=... /home ext4 defaults,usrquota,grpquota 0 2
sudo mount -o remount /home
sudo quotacheck -cugm /home
sudo quotaon -v /home
sudo edquota -u alice                # block va inode'lar uchun soft/hard limitlar
sudo setquota -u alice 500000 600000 0 0 /home
sudo repquota -a                     # hisobot
quota -u alice
```

XFS buning o’rniga `uquota`/`gquota` va `xfs_quota` ishlatadi.
Quota’lar - bitta foydalanuvchi `/home`’ni hamma uchun to’ldirib
qo’yishini to’xtatish usuli.

## Nima kuchda ekanini tekshirish

```bash
findmnt -o TARGET,SOURCE,FSTYPE,OPTIONS
cat /proc/mounts | grep /tmp
mount | grep noexec
findmnt --verify                          # fstab to'g'rimi
sudo touch /tmp/x.sh && chmod +x /tmp/x.sh && /tmp/x.sh    # "Permission denied" noexec ishlayotganini isbotlaydi
```

`/proc/mounts` **kernel’ning** option’larini ko’rsatadi, siz yozmagan
sukut qiymatlari bilan birga; `/etc/fstab` esa sizning niyatingizni
ko’rsatadi. Ular bir-biriga zid bo’lsa, demak kimdir qo’lda remount
qilgan.

:::exam-tip
"X’ni Y’ga shunday mount qilingki, undan binary’lar bajarilmasin" →
fstab option’lariga `noexec` qo’shing, `mount -o remount` (yoki unmount
qilgandan keyin `mount -a`) va biror narsani ishga tushirib ko’rib
isbotlang. Xavfsizlik uchligini (`noexec,nosuid,nodev`), `ro`, `nofail`,
`_netdev` va `noatime`’ni yoddan biling - ular option bo’yicha deyarli
har qanday topshiriqni qoplaydi.
:::

## O’zingizni tekshiring

1. `noexec`, `nosuid` va `nodev` har biri nimaga to’sqinlik qiladi va
   ular odatda qayerda qo’llanadi?
2. Mount qilingan filesystem’ni unmount qilmasdan qanday faqat o’qish
   uchun qilasiz va uni shunday qoldirish uchun yana nima qilish kerak?
3. Nega vfat va CIFS mount’lariga `uid=`/`gid=` option’lari kerak?
