## Linux hypervisor stack’i

Konteynerdan farqli o’laroq, virtual mashinaning o’z kernel’i va virtual
apparati bo’ladi. Linux’da qismlar quyidagicha:

```
  virsh / virt-manager / virt-install     ← the tools you type
            │
        libvirtd                          ← the management daemon and API
            │
          QEMU                            ← emulates the hardware (disks, NICs, console)
            │
          KVM  (kernel module)            ← makes the CPU run guest code at native speed
```

**KVM** kernel’ni hypervisor’ga aylantiradi, **QEMU** virtual qurilmalarni
beradi, **libvirt** esa ularning ustida yagona API va XML ta’rif formatini
beradi. `virsh` - libvirt’ning buyruq satri.

## Oldindan talab qilinadiganlar

```bash
egrep -c '(vmx|svm)' /proc/cpuinfo        # >0 = CPU virtualizatsiyani qo'llab-quvvatlaydi (Intel vmx / AMD svm)
lsmod | grep kvm                           # kvm_intel yoki kvm_amd yuklangan
sudo apt install qemu-kvm libvirt-daemon-system virtinst libvirt-clients bridge-utils virt-manager
sudo dnf install qemu-kvm libvirt virt-install virt-manager
sudo systemctl enable --now libvirtd
sudo usermod -aG libvirt,kvm "$USER"       # virsh'ni sudo'siz ishlatish uchun chiqib, qayta kiring
virt-host-validate                          # yuqoridagi hammasini tekshiradi va yetishmayotganini aytadi
```

Agar `/proc/cpuinfo` da `vmx`/`svm` ko’rinmasa, virtualizatsiya BIOS/UEFI’da
o’chirilgan yoki siz allaqachon ichma-ich virtualizatsiyasiz VM ichidasiz.

## virsh: lug’at

```bash
virsh list                        # ishlayotgan domain'lar ("domain" = VM)
virsh list --all                  # to'xtatilganlari bilan birga
virsh dominfo web01               # holat, CPU'lar, xotira, autostart
virsh domifaddr web01             # uning IP manzillari
virsh start web01
virsh shutdown web01              # ACPI shutdown - muloyim
virsh reboot web01
virsh destroy web01               # tokni uzish - muloyim emas, o'chirish ham emas
virsh undefine web01 --remove-all-storage    # ta'rifni (va disklarni) o'chiradi
virsh autostart web01             # host boot bo'lganda ishga tushadi
virsh autostart --disable web01
virsh console web01               # serial konsolga ulanadi (chiqish uchun Ctrl+])
virsh edit web01                  # domain XML'ini tahrirlaydi
virsh dumpxml web01 > web01.xml   # ta'rifni eksport qiladi
virsh define web01.xml            # uni import qiladi
virsh setmem web01 2G --config; virsh setvcpus web01 2 --config
```

`shutdown` guest’dan so’raydi; `destroy` - bu reset tugmasi. Ikkalasi ham
domain’ni ta’riflangan holda qoldiradi - uni faqat `undefine` olib
tashlaydi.

## Storage: pool’lar va volume’lar

```bash
virsh pool-list --all
virsh pool-info default
virsh vol-list default                     # undagi disk image'lari
ls -lh /var/lib/libvirt/images/            # "default" odatda shu yerda turadi
qemu-img create -f qcow2 /var/lib/libvirt/images/web01.qcow2 20G
qemu-img info /var/lib/libvirt/images/web01.qcow2
qemu-img resize /var/lib/libvirt/images/web01.qcow2 +10G     # diskni kattalashtiradi (keyin ichidagi partition'ni kattalashtiring)
qemu-img convert -O qcow2 disk.raw disk.qcow2
```

**qcow2** ishlatilgan sari o’sadi va snapshot’larni qo’llab-quvvatlaydi;
**raw** - oddiy image, biroz tezroq. qcow2 sukut bo’yicha, va buning
sabablari bor.

## Tarmoq

```bash
virsh net-list --all
virsh net-info default
virsh net-dumpxml default          # NAT tarmog'i: 192.168.122.0/24, dnsmasq, DHCP
virsh net-start default; virsh net-autostart default
```

| Rejim | Guest’lar oladi | Qachon |
|---|---|---|
| **NAT** (`default`) | libvirt’ning xususiy tarmog’idagi manzil; tashqariga chiqish ishlaydi, ichkariga kirish uchun forwarding kerak | noutbuklar, lablar |
| **bridge** | **fizik** LAN’dagi manzil, xuddi yana bitta mashina kabi | server’lar |
| **isolated** | tashqariga yo’li yo’q xususiy tarmoq | test muhitlari |
| **macvtap** | to’g’ridan-to’g’ri LAN, lekin host bilan gaplasha olmaydi | maxsus holatlar |

Production VM’lari host’dagi bridge’ga ulanadi (9-hafta uni `nmcli` bilan
quradi).

## Snapshot’lar

```bash
virsh snapshot-create-as web01 before-upgrade "Before the 1.27 upgrade"
virsh snapshot-list web01
virsh snapshot-revert web01 before-upgrade
virsh snapshot-delete web01 before-upgrade
```

Snapshot’lar xavfli o’zgarishdan oldingi qisqa muddatli xavfsizlik uchun -
ular backup emas va mavjud bo’lgan vaqtida unumdorlikka tushadi.

:::tip
Bu track uchun bitta VM - kerak bo’ladigan barcha lab jihozi: storage
darslari zaxira disklarni talab qiladi (`qemu-img create` +
`virsh attach-disk`), firewall darslari o’zingizni qulflab qo’ya oladigan
mashinani talab qiladi, boot darslari esa SSH yo’qolganda yeta oladigan
konsolni talab qiladi (`virsh console`). Har bir shunday haftadan oldin
snapshot oling.
:::

## O’zingizni tekshiring

1. KVM, QEMU va libvirt’ning har biri nima beradi?
2. `virsh shutdown`, `virsh destroy` va `virsh undefine` o’rtasidagi farq
   nima?
3. Qaysi tarmoq rejimi VM’ga fizik LAN’dagi manzilni beradi va qaysi biri
   sukut bo’yicha?
