## /etc/fstab, maydonma-maydon

```
UUID=9f8e7d6c-5b4a-...  /mnt/data  ext4  defaults,noatime  0  2
LABEL=backup            /backup    xfs   defaults          0  2
/dev/vg0/root           /          ext4  errors=remount-ro 0  1
/swapfile               none       swap  sw                0  0
tmpfs                   /tmp       tmpfs defaults,size=2G  0  0
//srv/share             /mnt/share cifs  credentials=/etc/cifs.cred,_netdev 0 0
```

| # | Maydon | Ma’nosi |
|---|---|---|
| 1 | qurilma | `UUID=`, `LABEL=`, yo’l yoki tarmoq manbasi - production’da **hech qachon `/dev/sdX`** emas |
| 2 | mount nuqtasi | **mavjud bo’lishi** shart; swap uchun `none` |
| 3 | turi | `ext4`, `xfs`, `swap`, `tmpfs`, `nfs`, `cifs`, `auto` |
| 4 | option’lar | vergul bilan ajratilgan, probelsiz (keyingi darsda ko’riladi) |
| 5 | dump | `0` - tarixiy backup bayrog’i |
| 6 | **fsck tartibi** | `0` hech qachon tekshirmaslik, `1` **faqat root**, `2` qolgan hammasi |

## Yozuvni xavfsiz qo’shish

```bash
sudo blkid /dev/sdb1                       # UUID'ni olish
sudo mkdir -p /mnt/data
sudo cp /etc/fstab /etc/fstab.bak          # doim
echo 'UUID=9f8e7d6c-5b4a-... /mnt/data ext4 defaults 0 2' | sudo tee -a /etc/fstab
sudo mount -a                              # fstab'dagi mount qilinmagan hamma narsani mount qiladi
findmnt /mnt/data
df -h /mnt/data
sudo systemctl daemon-reload               # systemd fstab'ni mount unit'larga qayta o'qiydi
```

:::warning
Noto’g’ri fstab yozuvi boot’ni to’xtatib qo’yishi mumkin: systemd
qurilmani 90 soniya kutadi, keyin **emergency mode**’ga tushadi, unga esa
SSH emas, konsol orqali kirish kerak. fstab’ni tahrirlagandan keyin
`sudo mount -a` (xatosiz) yoki `findmnt --verify`’ni ishlatmasdan hech
qachon reboot qilmang. Konsoli yo’q masofadagi mashinada aynan shu
tekshiruv reboot bilan joyiga borish o’rtasidagi butun farq.
:::

```bash
sudo mount -a                     # bu yerdagi har qanday xato boot nosozligi bo'lardi
findmnt --verify                  # fstab'ni tekshiradi: qurilmalar, mount nuqtalari, option'lar
findmnt --verify --verbose
```

Qurilma bo’lmasligi mumkin bo’lsa, `nofail` boot’ning to’xtab qolishiga
yo’l qo’ymaydi:

```
UUID=... /mnt/usb ext4 defaults,nofail,x-systemd.device-timeout=5 0 2
```

## Bu yerda ishlatadigan mount option’lar

```
defaults                 # rw,suid,dev,exec,auto,nouser,async
noauto                   # boot'da mount QILINMASIN (keyin qo'lda mount qilinadi)
nofail                   # qurilma yo'q bo'lsa ham boot bo'laversin
_netdev                  # avval tarmoqni kutish (NFS, CIFS, iSCSI)
ro                       # faqat o'qish uchun
noatime                  # murojaat vaqtlarini yangilamaslik - arzon unumdorlik yutug'i
user                     # oddiy foydalanuvchiga mount qilishga ruxsat
errors=remount-ro        # ext4: xatoda davom etish o'rniga faqat o'qish uchun remount qilish
x-systemd.automount      # boot'da emas, birinchi murojaatda mount qilish
```

## Systemd mount unit’lari

systemd har bir fstab qatori uchun `.mount` unit generatsiya qiladi va
siz ularni to’g’ridan-to’g’ri ham yozishingiz mumkin. Unit nomi mount
nuqtasi yo’liga **mos kelishi shart**: `/mnt/data` → `mnt-data.mount`.

```ini
# /etc/systemd/system/mnt-data.mount
[Unit]
Description=Data volume
[Mount]
What=/dev/disk/by-uuid/9f8e7d6c-5b4a-...
Where=/mnt/data
Type=ext4
Options=defaults,noatime
[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mnt-data.mount
systemctl status mnt-data.mount
systemctl list-units --type=mount
```

**automount** unit birinchi murojaatda mount qiladi - kamdan-kam
ishlatiladigan tarmoq share’lari uchun qulay:

```ini
# /etc/systemd/system/mnt-data.automount
[Unit]
Description=Automount data
[Automount]
Where=/mnt/data
TimeoutIdleSec=300
[Install]
WantedBy=multi-user.target
```

## Qo’lda mount va unmount qilish

```bash
sudo mount /mnt/data                 # qolganini fstab beradi
sudo mount -o remount,ro /mnt/data   # unmount qilmasdan option'larni o'zgartirish
sudo mount -o remount,rw /
sudo umount /mnt/data
sudo umount -l /mnt/data             # lazy: hozir uzadi, bo'shaganda tozalaydi
findmnt; findmnt -t ext4; mount | column -t
```

unmount paytidagi "Target is busy":

```bash
sudo lsof +D /mnt/data | head        # u yerda qaysi process'larning fayllari ochiq
sudo fuser -vm /mnt/data
sudo fuser -km /mnt/data             # ularni o'ldirish (ehtiyot bo'ling)
cd /                                  # aybdor o'z shell'ingiz bo'lishi mumkin
```

## Bind mount va tmpfs

```bash
sudo mount --bind /srv/data /var/www/data
# fstab:  /srv/data  /var/www/data  none  bind  0 0
sudo mount --rbind /srv /mnt/srv                       # rekursiv, ichki mount'larni ham oladi

sudo mount -t tmpfs -o size=1G tmpfs /mnt/scratch      # RAM'da turadi, har boot'da bo'sh
# fstab:  tmpfs /mnt/scratch tmpfs defaults,size=1G,mode=1777 0 0
```

Bind mount bitta directory’ni ikkinchi joyda ham ko’rsatadi - "dastur
`/var/www/data`’ni talab qilyapti, disk esa `/srv/data`’ga mount
qilingan" degan holatning javobi.

:::exam-tip
"/dev/sdb1’ni /mnt/data’ga doimiy mount qiling" = directory yarating,
**UUID bo’yicha** fstab qatorini qo’shing, `mount -a`, `findmnt` yoki
`df -h` bilan tekshiring. Sizni qutqaradigan ikki odat: avval fstab’dan
nusxa oling va topshiriqni muvaffaqiyatli `mount -a`’siz tark etmang.
Topshiriqda "disk bo’lmasa ham boot’ga to’sqinlik qilmasin" deyilgan
bo’lsa, `nofail` qo’shing.
:::

## O’zingizni tekshiring

1. fstab’ning oltita maydoni qaysilar va oxirgisi nimani boshqaradi?
2. Qaysi buyruq yangi fstab yozuvi keyingi boot’ni buzmasligini isbotlaydi?
3. Bind mount nima uchun kerak va u fstab’da qanday yoziladi?
