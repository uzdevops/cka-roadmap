## Uch qatlam

LVM disklar bilan fayl tizimlari orasiga abstraksiya qo’yadi, shu sababli
storage’ni qayta partition’lamasdan o’lchamini o’zgartirish, ko’chirish va
birlashtirish mumkin bo’ladi.

```
 /dev/sdb1  /dev/sdc1        ← PV  physical volume'lar (partition'lar yoki butun disklar)
        └────┬────┘
          vg0              ← VG  volume group: extent'larning yagona havzasi
        ┌───┴────┬───────┐
     lv_data  lv_logs  lv_home    ← LV  logical volume'lar: siz formatlab mount qiladiganingiz
```

| Termin | Nima |
|---|---|
| **PV** | LVM’ga berilgan blok qurilma |
| **VG** | PV’lardan tuzilgan, **PE**’larga (physical extent, sukut bo’yicha 4 MiB) bo’lingan hovuz |
| **LV** | hovuzning bir bo’lagi, partition kabi ishlatiladi |

Nega bu qo’shimcha qatlam arziydi: LV’ni **mount qilingan holida
o’stirish**, yangi disk hisobiga kengaytirish, snapshot olish va downtime
bo’lmasdan boshqa hardware’ga ko’chirish mumkin.

## Stack’ni qurish

```bash
sudo apt install lvm2
sudo pvcreate /dev/sdb1 /dev/sdc1
sudo vgcreate vg0 /dev/sdb1 /dev/sdc1
sudo lvcreate -L 2G -n lv_data vg0
sudo mkfs.ext4 /dev/vg0/lv_data
sudo mkdir -p /mnt/data && sudo mount /dev/vg0/lv_data /mnt/data
```

O’lchamlar:

```bash
sudo lvcreate -L 500M  -n lv_logs vg0        # absolyut
sudo lvcreate -l 100   -n lv_x    vg0        # 100 ta extent
sudo lvcreate -l 50%FREE -n lv_y  vg0        # bo'sh joyning yarmi
sudo lvcreate -l 100%FREE -n lv_z vg0        # qolgan hammasi
```

Qurilma ham `/dev/vg0/lv_data`, ham `/dev/mapper/vg0-lv_data` sifatida
paydo bo’ladi - fstab’da istalganini ishlating (ular `/dev/sdX` dan
farqli o’laroq barqaror nomlar).

## Ko’rib chiqish

```bash
pvs; vgs; lvs                      # tezkor jadvallar
sudo pvdisplay; sudo vgdisplay; sudo lvdisplay      # batafsil
sudo vgdisplay vg0 | grep -E "Free|PE Size|Total PE"
lsblk
sudo pvs -o+pv_used
sudo lvs -o+lv_size,seg_size,devices
```

## O’stirish - kundalik amaliyot

```bash
sudo vgs                                       # VG'da bo'sh joy bormi?
sudo lvextend -L +5G /dev/vg0/lv_data          # 5 GiB qo'shish
sudo lvextend -L 20G /dev/vg0/lv_data          # 20 GiB GACHA o'stirish
sudo lvextend -l +100%FREE /dev/vg0/lv_data    # qolgan barcha joyni olish
sudo resize2fs /dev/vg0/lv_data                # ext4: fayl tizimini online o'stirish
sudo xfs_growfs /mnt/data                      # xfs: fayl tizimini o'stirish, mount qilingan bo'lishi shart
```

Yoki ikkala qadam birdaniga - siz aynan shuni yozishingiz kerak:

```bash
sudo lvextend -r -L +5G /dev/vg0/lv_data       # -r fayl tizimining ham o'lchamini o'zgartiradi, ext4 yoki xfs
df -h /mnt/data
```

VG’da bo’sh joy yo’qmi? Disk qo’shing:

```bash
sudo pvcreate /dev/sdd1
sudo vgextend vg0 /dev/sdd1
sudo vgs
sudo lvextend -r -l +100%FREE /dev/vg0/lv_data
```

## Qisqartirish - faqat ext4, va offline

```bash
sudo umount /mnt/data
sudo e2fsck -f /dev/vg0/lv_data          # qisqartirishdan oldin shart
sudo resize2fs /dev/vg0/lv_data 5G       # AVVAL fayl tizimi
sudo lvreduce -L 5G /dev/vg0/lv_data     # keyin LV
sudo mount /dev/vg0/lv_data /mnt/data
# yoki, ikkalasi birdaniga:
sudo lvreduce -r -L 5G /dev/vg0/lv_data
```

:::warning
O’stirish: avval LV, keyin fayl tizimi. **Qisqartirish: avval fayl
tizimi, keyin LV.** LV’ni fayl tizimining o’lchamidan pastga tushirish
ma’lumotni yo’q qiladi, `lvreduce` ogohlantiradi, lekin tasdiqlasangiz
baribir bajaradi. XFS’ni esa **umuman qisqartirib bo’lmaydi** - backup
qiling, kichikroq qilib qayta yarating, tiklang.
:::

## O’chirish

```bash
sudo umount /mnt/data
sudo lvremove /dev/vg0/lv_data
sudo vgreduce vg0 /dev/sdc1          # PV'ni VG'dan chiqarish (avval undan ma'lumotni ko'chiring)
sudo pvmove /dev/sdc1                # extent'larni diskdan ko'chirish, ONLINE - ishdan chiqayotgan diskni shunday nafaqaga chiqarasiz
sudo pvremove /dev/sdc1
sudo vgremove vg0
```

`pvmove` - LVM’ning eng zo’r hiylasi: fayl tizimi mount qilingan va
ishlatilayotgan holda har bir extent’ni bitta diskdan boshqalariga
ko’chiring, keyin uni sug’urib oling.

## Snapshot’lar

```bash
sudo lvcreate -L 1G -s -n data_snap /dev/vg0/lv_data      # copy-on-write snapshot
sudo mount -o ro /dev/vg0/data_snap /mnt/snap             # backup'ni izchil holatda shu yerdan oling
sudo lvs                                                   # Data% ustunini kuzating
sudo lvconvert --merge /dev/vg0/data_snap                  # snapshot'ga QAYTARISH
sudo lvremove /dev/vg0/data_snap
```

Snapshot faqat o’zgargan bloklarni saqlaydi. Agar u **to’lib ketsa**,
tashlab yuboriladi va yaroqsiz bo’ladi, shuning uchun uni kutilayotgan
o’zgarishlar hajmiga qarab o’lchang va backup tugagach o’chiring.
Snapshot’lar backup emas - ular o’sha disklarda yashaydi.

## Doimiy qilish

```bash
sudo blkid /dev/vg0/lv_data
echo '/dev/vg0/lv_data /mnt/data ext4 defaults 0 2' | sudo tee -a /etc/fstab
sudo mount -a && findmnt /mnt/data
```

LVM qurilma nomlari barqaror, shuning uchun fstab’da `/dev/vg0/lv_data`
maqbul - UUID ham ishlaydi.

## Diagnostika

```bash
sudo vgs -o+vg_free; sudo lvs -o+lv_size
sudo pvck /dev/sdb1
sudo vgscan; sudo vgchange -ay              # volume group'larni faollashtirish (disklarni ko'chirib kelgandan keyin)
sudo lvchange -ay /dev/vg0/lv_data
sudo vgcfgrestore -l vg0                     # /etc/lvm/archive dagi metadata backup'lari - noto'g'ri o'zgarishdan tiklanish
sudo dmsetup ls
```

| Belgi | Sababi |
|---|---|
| lvextend’da `Insufficient free space` | VG to’la - yangi PV bilan `vgextend` |
| LV o’sdi, `df` o’zgarmadi | fayl tizimi resize qilinmagan - `resize2fs`/`xfs_growfs`, yoki `-r` ishlating |
| disklarni ko’chirgandan keyin LV’lar yo’qolgan | `vgscan` + `vgchange -ay` |
| `Device /dev/sdb1 excluded by a filter` | unda allaqachon signature bor - `wipefs -a`, yoki `/etc/lvm/lvm.conf` filtrlarini tekshiring |
| snapshot yaroqsiz | u to’lib ketgan |

:::exam-tip
Klassik topshiriq: "X logical volume’ni fayl tizimi bilan birga N GB’ga
kengaytiring". Bitta buyruq: `lvextend -r -L +NG /dev/vgX/lvX`, `lvs` va
`df -h` bilan tekshiriladi. Agar VG’da bo’sh joy bo’lmasa, to’liq ketma-
ketlik: `pvcreate` → `vgextend` → `lvextend -r`. Qisqartirish tartibini
ham biling - bu buyruqni yodlaganlarni qatlamlarni tushunganlardan
ajratadigan savol.
:::

## O’zingizni tekshiring

1. PV, VG va LV nima, va ularning qaysi birini formatlaysiz?
2. LV’dagi ext4 fayl tizimini o’stirish va qisqartirish uchun amallar
   tartibini ayting.
3. Hamma narsa mount qilingan holida ishdan chiqayotgan diskdan
   ma’lumotni qaysi buyruq ko’chiradi?
