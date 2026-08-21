## Avval disk’larga qarab olish

```bash
lsblk                      # daraxt: disk'lar, partition'lar, o'lchamlar, mount nuqtalari
lsblk -f                   # + filesystem turi, LABEL, UUID
sudo fdisk -l              # har bir disk va uning partition jadvali
sudo parted -l
cat /proc/partitions
sudo blkid                 # har bir block qurilmaning UUID va turi
ls -l /dev/disk/by-uuid/ /dev/disk/by-id/
```

```
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
sda      8:0    0   40G  0 disk
├─sda1   8:1    0    1G  0 part /boot
├─sda2   8:2    0    1G  0 part /boot/efi
└─sda3   8:3    0   38G  0 part
  └─vg0-root 253:0 0 38G 0 lvm  /
sdb      8:16   0    5G  0 disk               ← mashq qilish uchun bo'sh disk
```

Qurilma nomlari: `/dev/sda` (SATA/SCSI/USB), `/dev/vda` (virtio, VM’larda),
`/dev/nvme0n1` (NVMe - partition’lari `nvme0n1p1` ko’rinishida),
`/dev/sdb1` (ikkinchi disk’ning birinchi partition’i).

## GPT yoki MBR

| | MBR (msdos) | GPT |
|---|---|---|
| maks. disk | 2 TiB | 8 ZiB |
| partition’lar | 4 primary, yoki 3 + extended ichida logical’lar | 128 |
| boot | BIOS | UEFI (va bios_grub partition’i bilan BIOS) |
| ortiqchalik | jadvalning bitta nusxasi | primary + backup |
| qayerda | faqat legacy | **hamma yangi narsa** |

```bash
sudo parted /dev/sdb print | head -5      # "Partition Table: gpt"
```

## fdisk: interaktiv, GPT’ni tushunadi

```bash
sudo fdisk /dev/sdb
```

| Tugma | Nima qiladi |
|---|---|
| `m` | yordam |
| `p` | jadvalni chiqaradi |
| `g` | yangi **GPT** jadval (MBR uchun `o`) |
| `n` | yangi partition (raqami, birinchi sektor, oxirgi sektor yoki `+2G`) |
| `d` | o’chirish |
| `t` | turini o’zgartirish (`L` ro’yxatlaydi: 20 Linux filesystem, 19 swap, 30 Linux LVM, 1 EFI) |
| `w` | **yozish** va chiqish |
| `q` | saqla**masdan** chiqish - undo |

```
Command (m for help): g
Command (m for help): n
Partition number (1-128, default 1): 1
First sector (2048-10485726, default 2048): <Enter>
Last sector, +/-sectors or +/-size{K,M,G,T,P} (2048-10485726): +2G
Command (m for help): n            ← ikkinchisi, +1G, keyin t → 19 (swap)
Command (m for help): p
Command (m for help): w
```

`w` bosilmaguncha hech narsa o’zgarmaydi. Shu sababli `q` istalgan
xatodan tekin qutulish yo’li.

## parted: skript yoziladigan

```bash
sudo parted /dev/sdb --script mklabel gpt
sudo parted /dev/sdb --script mkpart primary ext4 1MiB 2GiB
sudo parted /dev/sdb --script mkpart primary linux-swap 2GiB 3GiB
sudo parted /dev/sdb --script set 1 lvm on
sudo parted /dev/sdb --script print
sudo parted /dev/sdb --script rm 2
sudo parted /dev/sdb resizepart 1 100%          # partition'ni disk to'lguncha kattalashtirish
```

`parted` **darhol** yozadi - `q` bilan qochish imkoni yo’q.
Avtomatlashtirish uchun `--script`, partition’lar tekislangan bo’lib
qolishi uchun esa `MiB` birliklaridan foydalaning.

## Kernel’ga xabar berish

```bash
sudo partprobe /dev/sdb          # partition jadvalini qayta o'qish
sudo partx -u /dev/sdb
sudo udevadm settle
lsblk /dev/sdb                    # yangi partition'lar paydo bo'lishi kerak
```

Agar kernel rad etsa ("device or resource busy"), disk’dagi biror narsa
mount qilingan yoki ishlatilyapti - uni unmount qiling yoki reboot qiling.

## Partition turlari

Turi majburlash emas, ishora, lekin vositalar uni o’qiydi:

```bash
sudo fdisk /dev/sdb            # t, keyin ro'yxat uchun L
# 20  Linux filesystem     19  Linux swap
# 30  Linux LVM             1  EFI System
# 29  Linux RAID
sudo parted /dev/sdb set 1 lvm on
sudo parted /dev/sdb set 1 esp on
```

## Partition’ni kattalashtirish

```bash
# host'da virtual disk kattalashtirilgandan keyin:
sudo qemu-img resize /var/lib/libvirt/images/lab.qcow2 +10G     # (VM host'ida)
lsblk                                            # disk kattalashdi, partition esa yo'q
sudo growpart /dev/sda 3                         # cloud-guest-utils - oson yo'l
# yoki: parted /dev/sda resizepart 3 100%
sudo pvresize /dev/sda3                          # agar ichida LVM PV bo'lsa
sudo lvextend -l +100%FREE -r /dev/vg0/root      # keyin LV va uning filesystem'i
df -h /
```

Uch qatlam, uch qadam: **disk → partition → (PV/LV) → filesystem**.
Bittasini o’tkazib yuborish - "disk’ni kattalashtirdim, hech narsa
o’zgarmadi" degan gapning sababi.

:::warning
Ma’lumot turgan partition’ni o’chirish yoki o’lchamini o’zgartirish uni
yo’q qiladi. Biror narsaga tegishdan oldin `lsblk`, `mount` va `blkid`
bilan tekshiring, o’rganayotganda zaxira disk’da ishlang
(`virsh attach-disk`) va avval VM’ning snapshot’ini oling.
`wipefs -a /dev/sdb` disk’dagi har bir signature’ni o’chiradi - tez va
qaytarib bo’lmaydigan tarzda.
:::

:::exam-tip
"/dev/sdb’da 2 GiB partition yarating va uni formatlang" → `fdisk` (`g`,
`n`, `+2G`, `w`) yoki `parted --script`, keyin `partprobe`, keyin `mkfs`
(keyingi dars), so’ng `lsblk -f` bilan tekshiring. Topshiriqda tur
aytilgan bo’lsa (swap, LVM) uni tashlab ketmang va nishon qurilmani doim
`lsblk` bilan tasdiqlang - bu yerda noto’g’ri qurilma yagona tuzatib
bo’lmaydigan xato.
:::

## O’zingizni tekshiring

1. Qaysi buyruq disk’lar, partition’lar, filesystem’lar va mount
   nuqtalarini bitta daraxtda ko’rsatadi?
2. `fdisk` ichida o’zgarishlarni nima doimiy qiladi va nima ularni bekor
   qiladi?
3. Virtual disk’ni kattalashtirdingiz, lekin `df -h` o’zgarmadi. Qaysi
   qatlamlarda hali ish qilinishi kerak?
