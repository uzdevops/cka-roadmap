## Filesystem tanlash

| Filesystem | Izoh |
|---|---|
| **ext4** | xavfsiz sukut tanlovi: yetuk, kichraytirsa bo’ladi, `resize2fs` uni online kattalashtiradi |
| **xfs** | RHEL’ning sukut tanlovi: katta fayllar va parallel I/O bilan a’lo; **faqat kattalashadi, hech qachon kichraymaydi** |
| **btrfs** | snapshot’lar, subvolume’lar, checksum’lar, ichida RAID; harakatlanuvchi qismlari ko’p |
| **vfat/exfat** | olinadigan qurilmalar va EFI system partition’lari; Unix ruxsatlari yo’q |
| **swap** | filesystem emas - `mkswap` (o’tgan dars) |

Imtihon va ko’pchilik server’lar uchun: boshqacha aytilmagan bo’lsa ext4,
RHEL qoidalari amal qiladigan joyda xfs.

## Uni yaratish

```bash
sudo mkfs.ext4 /dev/sdb1
sudo mkfs.ext4 -L data /dev/sdb1              # LABEL bilan
sudo mkfs.ext4 -m 1 -L data /dev/sdb1         # sukutdagi 5% o'rniga root uchun 1% ajratish
sudo mkfs.xfs -L data /dev/sdb1
sudo mkfs.xfs -f /dev/sdb1                    # -f: mavjud filesystem ustiga yozish
sudo mkfs.vfat -F32 -n USB /dev/sdc1
sudo mkfs -t ext4 /dev/sdb1                   # umumiy shakli
```

```bash
lsblk -f
# NAME FSTYPE LABEL UUID                                 MOUNTPOINTS
# sdb1 ext4   data  9f8e7d6c-5b4a-...
sudo blkid /dev/sdb1
```

`mkfs` u yerda nima bo’lsa, hammasini **yo’q qiladi**. Avval `lsblk`,
`blkid` va `mount` bilan tekshiring; undo yo’q.

## Label va UUID’lar

**UUID**’ni `mkfs` generatsiya qiladi va u yagona; **label** esa siz
tanlaydigan nom. Qurilma nomlari o’zgarganda (reboot yoki yangi disk’dan
keyin `/dev/sdb` `/dev/sdc`’ga aylanishi) ikkalasi ham o’zgarmaydi -
shuning uchun fstab hech qachon `/dev/sdX` ishlatmasligi kerak.

```bash
sudo blkid                                    # hammasi
sudo e2label /dev/sdb1 data                   # ext2/3/4: label'ni o'qish yoki qo'yish
sudo tune2fs -L data /dev/sdb1                # xuddi shu
sudo xfs_admin -L data /dev/sdb1              # xfs (unmount qilingan bo'lishi shart)
sudo xfs_admin -u /dev/sdb1                   # xfs: UUID'ni ko'rsatish
sudo tune2fs -U random /dev/sdb1              # ext4: yangi tasodifiy UUID (disk klonlangandan keyin)
ls -l /dev/disk/by-uuid/ /dev/disk/by-label/
```

## Bir martalik mount qilish

```bash
sudo mkdir -p /mnt/data
sudo mount /dev/sdb1 /mnt/data
sudo mount -o noexec,nosuid /dev/sdb1 /mnt/data
sudo mount UUID=9f8e7d6c-... /mnt/data
sudo mount -t ext4 /dev/sdb1 /mnt/data
df -h /mnt/data; findmnt /mnt/data
sudo umount /mnt/data                          # yoki: umount /dev/sdb1
```

Doimiy mount qilish - bu `/etc/fstab`, keyingi dars.

## ext4’ni sozlash va ko’rish

```bash
sudo tune2fs -l /dev/sdb1 | head -30          # har bir parametr: block o'lchami, inode soni, mount soni, feature'lar
sudo tune2fs -m 1 /dev/sdb1                   # zaxiraga olingan block'lar foizi
sudo tune2fs -c 30 -i 30d /dev/sdb1           # har 30 mount / 30 kunda majburiy tekshiruv
sudo tune2fs -O ^has_journal /dev/sdb1        # feature'ni olib tashlash (kamdan-kam kerak)
sudo dumpe2fs -h /dev/sdb1
sudo xfs_info /mnt/data                        # xfs'dagi ekvivalenti (MOUNT QILINGAN filesystem'da)
```

**inode soni** `mkfs` paytida qotib qoladi: mayda fayllarga to’la
filesystem joyi bo’la turib inode’larni tugatib qo’yishi mumkin
(`df -i`). Bunday workload’lar uchun `mkfs.ext4 -i
8192` yoki `-N <count>` zichroq nisbat qo’yadi - va uni keyin
o’zgartirib bo’lmaydi.

## Kattalashtirish va kichraytirish

```bash
# ext4 - kattalashtirish, online (mount qilingan) yoki offline
sudo resize2fs /dev/vg0/data                   # qurilma o'lchamigacha
sudo resize2fs /dev/vg0/data 20G
# ext4 - KICHRAYTIRISH: avval UNMOUNT qilinishi va tekshirilishi shart
sudo umount /mnt/data
sudo e2fsck -f /dev/vg0/data
sudo resize2fs /dev/vg0/data 5G
# keyin LV/partition'ni ham mos ravishda kichraytiring

# xfs - faqat kattalashtirish va faqat MOUNT QILINGAN holatda
sudo xfs_growfs /mnt/data
sudo xfs_growfs -D 5242880 /mnt/data
```

Kattalashtirish va kichraytirishda tartib teskari: **kattalashtirishda**
avval qurilma, keyin filesystem; **kichraytirishda** avval filesystem,
keyin qurilma. Teskarisini qilish ma’lumotni yo’qotadi. (`lvextend -r` /
`lvreduce -r` ikkala qadamni sizning o’rningizga bajaradi - LVM darsi.)

## Tekshirish va tuzatish

```bash
sudo umount /dev/sdb1                # mount qilingan filesystem HECH QACHON tekshirilmaydi
sudo fsck /dev/sdb1
sudo fsck -n /dev/sdb1               # faqat hisobot
sudo fsck -y /dev/sdb1               # hamma savolga ha deb javob berish
sudo e2fsck -f -y /dev/sdb1          # toza ko'rinsa ham majburan
sudo xfs_repair /dev/sdb1            # xfs; quruq yurish uchun -n
sudo xfs_repair -L /dev/sdb1         # shikastlangan log'ni nollash - ENG OXIRGI CHORA, so'nggi yozuvlarni yo'qotadi
```

Root filesystem uchun: `sudo touch /forcefsck && sudo reboot` yoki rescue
rejimiga boot qiling.

## Nusxalash va klonlash

```bash
sudo dd if=/dev/sdb1 of=/dev/sdc1 bs=4M status=progress    # block nusxasi - nishon shu o'lchamda yoki kattaroq
sudo e2image -ra -p /dev/sdb1 /dev/sdc1                     # ext'ni tushunadigan klon, faqat band block'larni ko'chiradi
sudo tune2fs -U random /dev/sdc1                            # klonga YANGI uuid bering, aks holda fstab chalkashadi
sudo rsync -aHAX /mnt/src/ /mnt/dst/                        # fayl darajasida, filesystem'ga bog'liq emas, ACL va xattr'larni saqlaydi
```

:::warning
Bitta tizimda ikkita bir xil UUID mount’ni oldindan aytib bo’lmaydigan
qiladi: `mount
UUID=...` istalgan qurilmani tanlashi mumkin. Har qanday `dd` klonidan
keyin ikkalasi bitta kernel’ga ko’rinmasdan oldin nusxaning UUID’sini
o’zgartiring.
:::

:::exam-tip
"/dev/sdb1’ni X label bilan ext4 qilib formatlang va /mnt/Y’ga mount
qiling" → `mkfs.ext4 -L X /dev/sdb1`, `mkdir -p /mnt/Y`, `mount`, keyin
doimiylik uchun fstab qatori (keyingi dars), `lsblk -f` va `df -h` bilan
tekshirilgan holda. Topshiriqda xfs aytilgan bo’lsa, uni kichraytirib
bo’lmasligini va mount qilingan holda `xfs_growfs` bilan
kattalashtirilishini eslang.
:::

## O’zingizni tekshiring

1. Nega fstab `/dev/sdb1` emas, UUID yoki label’ga murojaat qilishi
   kerak?
2. Qaysi filesystem’ni kichraytirib bo’lmaydi va ikkita asosiysining har
   birini qaysi buyruq kattalashtiradi?
3. LV’dagi filesystem’ni kattalashtirishda va kichraytirishda amallarning
   to’g’ri tartibi qanday?
