## ISO’dan o’rnatish

Uzun yo’l, va aynan u cloud image siz uchun nima qilishini o’rgatadi:
o’rnatish media’sini ulang, undan boot qiling, o’rnatuvchiga javob bering.

```bash
cd /var/lib/libvirt/images
sudo wget https://releases.ubuntu.com/24.04/ubuntu-24.04-live-server-amd64.iso
sha256sum ubuntu-24.04-live-server-amd64.iso        # mirror'dagi SHA256SUMS bilan solishtiring
```

```bash
sudo virt-install \
  --name lab01 \
  --memory 2048 --vcpus 2 \
  --disk path=/var/lib/libvirt/images/lab01.qcow2,size=20,format=qcow2,bus=virtio \
  --cdrom /var/lib/libvirt/images/ubuntu-24.04-live-server-amd64.iso \
  --os-variant ubuntu24.04 \
  --network network=default \
  --graphics vnc,listen=0.0.0.0
```

`--graphics vnc` bilan o’rnatuvchining ekrani VNC orqali ochiq bo’ladi:

```bash
virsh vncdisplay lab01           # :0  → port 5900
virt-viewer lab01                # desktop'ingiz bo'lsa
# masofadan: ssh -L 5900:127.0.0.1:5900 host   keyin VNC klientini localhost:5900 ga qarating
```

Serial konsol orqali faqat matnli o’rnatish uchun `--location`’ni
`--extra-args 'console=ttyS0,115200n8'` bilan (oldingi dars) va
`virsh console lab01`’ni ishlating.

## O’rnatuvchi bo’ylab yurish

Savollar har bir distributivda bir xil va ularning har biri shu track’dagi
biror mavzuga to’g’ri keladi:

| O’rnatuvchi qadami | Nimani hal qilasiz | Qayerda ko’riladi |
|---|---|---|
| til, klaviatura, vaqt zonasi | locale; vaqt zonasi loglar uchun muhim | 10-hafta (vaqt) |
| tarmoq | DHCP yoki statik, hostname | 9-hafta |
| disk taqsimoti | butun disk, LVM, qo’lda partition’lar, swap hajmi | 11-12-haftalar |
| fayl tizimi | ext4 yoki xfs; alohida `/var`, `/home`mi? | 11-hafta |
| user hisobi | birinchi user va u sudo oladimi | 8-hafta |
| SSH server | uni o’rnatish va kalitlarni import qilish kerakmi | 10-hafta |
| paket tanlash / snap’lar | server’da minimal saqlang | 6-hafta |

Lab mashinasi uchun oqilona javoblar: butun diskda LVM (storage darslarida
kengaytiradigan narsa bo’lishi uchun), 2 GB swap, sudo’li bitta user,
o’rnatilgan OpenSSH, boshqa hech narsa.

Oxirida o’rnatuvchi reboot qilishni so’raydi. ISO’ni olib tashlang, aks
holda u yana o’rnatuvchini boot qiladi:

```bash
virsh destroy lab01                        # "please remove the installation medium" da osilib qolsa
virsh change-media lab01 sda --eject --config
virsh start lab01
virsh console lab01
```

## Yangi mashina ichidagi dastlabki qadamlar

```bash
sudo apt update && sudo apt upgrade -y
sudo hostnamectl set-hostname lab01
ip a; ip r                                  # manzil oldimi?
sudo systemctl enable --now ssh
ssh-copy-id ahmad@192.168.122.50            # host'dan, konsoldan foydalanishni to'xtatish uchun
timedatectl set-timezone Asia/Tashkent
sudo virsh snapshot-create-as lab01 clean "Fresh install"     # HOST'dan - sizning rollback nuqtangiz
```

O’sha snapshot - mashqning butun ma’nosi: shu yerdan boshlab bu track’ning
har bir darsida mashinani buzishingiz va soniyalarda qaytib kelishingiz
mumkin.

## Nazoratsiz o’rnatishlar, bir paragrafda

O’rnatuvchiga qo’lda javob berish miqyoslashmaydi. Har bir distributivda
sizning o’rningizga javob beradigan fayl bor - Ubuntu’ning
**autoinstall/cloud-init**’i (`user-data`), Debian’ning **preseed**’i,
RHEL’ning **kickstart**’i:

```bash
sudo virt-install --name lab02 ... \
  --location /var/lib/libvirt/images/ubuntu-24.04-live-server-amd64.iso \
  --extra-args 'autoinstall ds=nocloud-net;s=http://10.0.0.1/autoinstall/ console=ttyS0'
# RHEL: --extra-args "inst.ks=http://10.0.0.1/ks.cfg console=ttyS0"
```

O’sha o’rnatuvchi, o’sha savollar - fayldan javob berilgan. Yuzta bir xil
mashina shunday quriladi va LFCS sizdan faqat bittasini o’rnatishni
so’rasa ham, buning borligini bilishga arziydi.

:::exam-tip
Bu maqsad - amaliy maqsad: ISO’ni ulang, boot qiling, o’rnating, media’ni
olib tashlang, o’rnatilgan tizimni boot qiling. Imtihon sizga o’rnatishni
yuklashdan ko’ra ishlab turgan mashinani berishi ancha ehtimolliroq - lekin
o’rnatuvchining disk taqsimoti va tarmoq savollari aynan storage va tarmoq
maqsadlari, shuning uchun qo’lda o’rnatish yaxshi takrorlash bo’ladi.
:::

## O’zingizni tekshiring

1. Qaysi ikkita `virt-install` opsiyasi o’rnatish media’sini ulaydi va
   ular bir-biridan nimasi bilan farq qiladi?
2. Host’da desktop bo’lmasa, o’rnatuvchining ekraniga qanday yetasiz?
3. O’rnatish tugagandan keyin host nuqtai nazaridan birinchi navbatda
   nima qilish kerak?
