## virt-install: ta’riflab, ishga tushiradigan bitta buyruq

`virt-install` domain XML’ini yaratadi, diskni ajratadi, tarmoqni ulaydi va
mashinani ishga tushiradi.

```bash
sudo virt-install \
  --name web01 \
  --memory 2048 \
  --vcpus 2 \
  --disk path=/var/lib/libvirt/images/web01.qcow2,size=20,format=qcow2 \
  --os-variant ubuntu24.04 \
  --network network=default \
  --graphics none \
  --console pty,target_type=serial \
  --location http://archive.ubuntu.com/ubuntu/dists/noble/main/installer-amd64/ \
  --extra-args 'console=ttyS0,115200n8'
```

| Opsiya | Ma’nosi |
|---|---|
| `--name` | domain nomi |
| `--memory` | RAM, MiB’da |
| `--vcpus` | virtual CPU’lar |
| `--disk path=...,size=N` | disk image’i (bo’lmasa yaratiladi), hajmi GiB’da |
| `--os-variant` | libvirt’ga guest’ga qaysi qurilma/sukut qiymatlar mos kelishini aytadi (`osinfo-query os` ularni ro’yxatlaydi) |
| `--network network=default` | NAT tarmog’i; yoki `bridge=br0` |
| `--graphics none` + `--console` | headless: o’rnatish va login serial konsol orqali |
| `--location` | tarmoqdagi o’rnatuvchi daraxti (matnli o’rnatish) |
| `--cdrom /path.iso` | uning o’rniga ISO’dan boot qiladi (keyingi dars) |
| `--import` | o’rnatmaydi: mavjud disk image’ini boot qiladi |
| `--noautoconsole` | konsolni darhol ulamaydi |

`--os-variant` ni to’g’ri berishga arziydi: u virtio drayverlari va sukut
qiymatlarni hal qiladi, noto’g’ri qiymat esa unumdorlikka tushadi.

## Tez yo’l: cloud image

ISO’dan o’rnatish yigirma daqiqa savollarga javob berishni oladi. Cloud
image’lar - oldindan o’rnatilgan disklar bo’lib, ular birinchi boot’da
**cloud-init** seed’idan o’zini o’zi sozlaydi - ishlaydigan VM’ni bir
daqiqacha ichida olish yo’li.

```bash
cd /var/lib/libvirt/images
sudo wget https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img
sudo qemu-img convert -O qcow2 noble-server-cloudimg-amd64.img web01.qcow2
sudo qemu-img resize web01.qcow2 20G
```

```bash
cat > user-data <<'EOF'
#cloud-config
hostname: web01
users:
  - name: ahmad
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    ssh_authorized_keys:
      - ssh-ed25519 AAAA... your key here
package_update: true
packages: [nginx]
EOF
echo -e "instance-id: web01\nlocal-hostname: web01" > meta-data
sudo cloud-localds /var/lib/libvirt/images/web01-seed.iso user-data meta-data
```

```bash
sudo virt-install --name web01 --memory 2048 --vcpus 2 \
  --disk /var/lib/libvirt/images/web01.qcow2,device=disk,bus=virtio \
  --disk /var/lib/libvirt/images/web01-seed.iso,device=cdrom \
  --os-variant ubuntu24.04 --network network=default \
  --graphics none --console pty,target_type=serial --import --noautoconsole
```

`--import` o’rnatishni butunlay o’tkazib yuboradi: diskda tizim allaqachon
bor, cloud-init esa birinchi boot’da sizning `user-data` faylingizni
qo’llaydi.

## Mashinaga yetib borish

```bash
virsh list
virsh console web01                 # serial konsol; uzilish uchun Ctrl+]
virsh domifaddr web01               # uning DHCP manzili
ssh ahmad@192.168.122.45
sudo virsh net-dhcp-leases default  # NAT tarmog'idagi har bir lease
```

Agar `virsh console` hech narsa ko’rsatmasa, demak guest serial portga
yozmayapti: kernel buyruq satrida `console=ttyS0` bilan boot qiling (cloud
image’lar buni allaqachon qiladi) yoki `virt-manager`/VNC’dan foydalaning.

## Kundalik amallar

```bash
virsh start web01; virsh shutdown web01; virsh reboot web01
virsh autostart web01
virsh dominfo web01; virsh domstats web01
virsh setmem web01 4G --config      # qayta ishga tushgandan keyin kuchga kiradi
virsh setvcpus web01 4 --config --maximum
virsh attach-disk web01 /var/lib/libvirt/images/data.qcow2 vdb --persistent --subdriver qcow2
virsh detach-disk web01 vdb --persistent
virsh snapshot-create-as web01 clean "Fresh install"
virsh dumpxml web01 | grep -A3 "<disk"
```

O’sha `attach-disk` satri - storage haftalari talab qiladigan zaxira
disklarni o’zingizga berish usuli:

```bash
sudo qemu-img create -f qcow2 /var/lib/libvirt/images/lab-disk1.qcow2 5G
sudo virsh attach-disk web01 /var/lib/libvirt/images/lab-disk1.qcow2 vdb --persistent --subdriver qcow2
# guest ichida: lsblk /dev/vdb ni ko'rsatadi
```

## Klonlash

```bash
virsh shutdown web01
sudo virt-clone --original web01 --name web02 --auto-clone
sudo virt-sysprep -d web02          # hostname, SSH host kalitlari, machine-id, loglarni tozalaydi
virsh start web02
```

`virt-sysprep` muhim: asl nusxaning machine-id va SSH host kalitlarini
saqlab qolgan klon DHCP’ni ham, ilgari ulangan har bir SSH klientini ham
chalkashtiradi.

:::exam-tip
LFCS sizdan VM yaratib, boot qilishni so’raydi, libvirt’ni mukammal
bilishni emas. `virt-install` ni `--name --memory --vcpus --disk --os-variant
--network` bilan biling, `virsh start/shutdown/list --all/autostart/console`
ni biling va `--import` mavjud image’ni boot qilishini, `--cdrom`/`--location`
esa yangisini o’rnatishini biling.
:::

## O’zingizni tekshiring

1. `virt-install` da `--import`, `--cdrom` va `--location` ning har biri
   nima qiladi?
2. VM’ning IP manzilini host’dan qanday qilib ikki xil yo’l bilan
   topasiz?
3. Nega VM’ni klonlagandan keyin `virt-sysprep` ishga tushiriladi?
