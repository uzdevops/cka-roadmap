## Tarmoq orqali blok qurilma

NFS **fayl tizimini** ulashadi: u serverga tegishli, ko’p klient bir xil
fayllarni ko’radi. NBD (Network Block Device) esa **xom blok qurilmani**
ulashadi: klient `/dev/nbd0`’ni xuddi disk ulangandek ko’radi, uni
partition’laydi, formatlaydi va fayl tizimiga to’liq egalik qiladi.

| | NFS | NBD |
|---|---|---|
| nimani export qiladi | directory daraxtini | xom bloklarni |
| fayl tizimi qayerda | serverda | **klientda** |
| bir vaqtdagi klientlar | ko’p, xavfsiz | **bir vaqtda bittasi** (klaster fayl tizimi ishlatilmasa) |
| fayl lock’lari, ruxsatlar | NFS hal qiladi | oddiy lokal semantika |
| odatiy foydalanish | umumiy home directory’lar, umumiy kontent | bitta mashina uchun disk: VM’lar, disksiz boot, masofadagi storage |

Bitta yozuvchi qoidasi - eslab qolish kerak bo’lgan narsa: bir xil NBD
export’ni ext4 bilan mount qilgan ikkita klient uni buzadi, chunki har
biri o’zini yagona yozuvchi deb bilib metadata’ni cache’laydi. (iSCSI -
xuddi shu g’oyaning enterprise ekvivalenti.)

## Server

```bash
sudo apt install nbd-server        # Debian/Ubuntu
sudo dnf install nbd               # RHEL
```

Uni fayl yoki haqiqiy qurilma bilan ta’minlang:

```bash
sudo mkdir -p /srv/nbd
sudo truncate -s 2G /srv/nbd/export1.img        # sparse 2 GiB backing fayl
# yoki to'g'ridan-to'g'ri partition/LV ishlating: /dev/vg0/nbdvol
```

```bash
sudo vi /etc/nbd-server/config
```

```ini
[generic]
    user = nbd
    group = nbd
    includedir = /etc/nbd-server/conf.d

[export1]
    exportname = /srv/nbd/export1.img
    readonly = false
    flush = true
    fua = true
    listenaddr = 192.168.1.10

[data]
    exportname = /dev/vg0/nbdvol
    readonly = true
```

```bash
sudo systemctl enable --now nbd-server
sudo systemctl status nbd-server
sudo ss -tulpn | grep 10809           # sukut bo'yicha NBD porti
sudo ufw allow from 192.168.1.0/24 to any port 10809 proto tcp
```

## Klient

```bash
sudo apt install nbd-client
sudo modprobe nbd                      # kernel moduli /dev/nbd* ni beradi
lsmod | grep nbd
ls /dev/nbd*
```

```bash
sudo nbd-client 192.168.1.10 10809 /dev/nbd0 -N export1
# Negotiation: ..size = 2048MB
# bs=512, sz=2147483648 bytes
lsblk /dev/nbd0
```

Bundan keyin bu oddiy disk:

```bash
sudo mkfs.ext4 -L nbdvol /dev/nbd0        # faqat BIRINCHI marta
sudo mkdir -p /mnt/nbd
sudo mount /dev/nbd0 /mnt/nbd
df -h /mnt/nbd
echo hello | sudo tee /mnt/nbd/test.txt
```

Uzish - **aynan shu tartibda**:

```bash
sudo umount /mnt/nbd
sudo nbd-client -d /dev/nbd0
lsblk | grep nbd
```

Uzishdan oldin doim umount qiling. Mount qilingan fayl tizimi ostidan
qurilmani tortib olish - diskni sug’urib olish bilan bir xil.

## Klient tomonini doimiy qilish

```bash
sudo vi /etc/nbdtab
```

```
# qurilma host          export    option'lar
nbd0      192.168.1.10  export1   persist
```

```bash
sudo systemctl enable --now nbd-client
# fstab, tarmoq va qurilmani kutish bilan:
# /dev/nbd0  /mnt/nbd  ext4  _netdev,nofail,x-systemd.device-timeout=10  0  0
sudo mount -a
```

Bu yerda `_netdev` va `nofail` ixtiyoriy emas: tarmoq ko’tarilib,
`nbd-client` ulanmaguncha qurilma mavjud bo’lmaydi, uni abadiy kutgan
boot esa emergency rejimda tugaydi.

## Rejimlar va option’lar

```bash
sudo nbd-client 192.168.1.10 10809 /dev/nbd0 -N export1 -persist   # avtomatik qayta ulanadi
sudo nbd-client -N ro-export 192.168.1.10 /dev/nbd1                 # faqat o'qish uchun export
sudo nbd-client -l 192.168.1.10                                     # server taklif qiladigan export'lar RO'YXATI
sudo nbd-client -c /dev/nbd0                                        # bu qurilma ulanganmi?
```

Server tomonidagi `readonly = true` ko’p klientga bir xil export’ni
xavfsiz mount qilish imkonini beradi - bu ko’p klientli yagona xavfsiz
holat.

## Diagnostika

```bash
# server
sudo systemctl status nbd-server; sudo journalctl -u nbd-server -n 30
sudo ss -tulpn | grep 10809
ls -l /srv/nbd/

# klient
lsmod | grep nbd || sudo modprobe nbd
sudo nbd-client -l <server>
dmesg | tail -20                       # kernel NBD ulanish hodisalarini logga yozadi
lsblk; sudo blkid /dev/nbd0
```

| Belgi | Sababi |
|---|---|
| `Error: Read failed` / negotiation ishlamaydi | export nomi (`-N`) noto’g’ri, server ishlamayapti, firewall |
| `/dev/nbd0: No such device` | `modprobe nbd` qilinmagan; `/etc/modules-load.d/`’ga `nbd`’ni qo’shing |
| ikkinchi klient mount qilgandan keyin fayl tizimi buzilgan | bitta yozuvchi qoidasi buzilgan |
| qurilma yo’qoladi, I/O xatolari | `-persist`’siz tarmoq uzilishi |
| boot osilib qoladi | fstab’da `_netdev`/`nofail` yo’q |

:::warning
NBD’da sukut bo’yicha **autentifikatsiya ham, shifrlash ham yo’q**: 10809
portiga yeta oladigan har kim export’ni o’qiy va unga yoza oladi. Uni
firewall bilan ishonchli tarmoq bilan cheklang, ichki manzilga bog’lang
yoki SSH/WireGuard orqali tunnel qiling. Hech qachon internetga
ochmang.
:::

:::exam-tip
Ehtimoliy topshiriq: nbd-server bilan fayl yoki qurilmani export qilish,
uni klientdan `nbd-client host port /dev/nbd0 -N name` bilan ulash,
formatlash va mount qilish. Klientda `modprobe nbd`’ni, uzish tartibini
(umount, keyin `nbd-client -d`) va fayl tizimi **klientga** tegishli
ekanini eslang - demak `mkfs` o’sha yerda ishlaydi, serverda emas.
:::

## O’zingizni tekshiring

1. NFS va NBD nimani export qilishidagi asosiy farq nima, va har birida
   fayl tizimi qayerda joylashadi?
2. Nega yoziladigan NBD export’ni bir vaqtda faqat bitta klient mount
   qilishi kerak?
3. Mount qilingan NBD qurilmasini xavfsiz uzish uchun qaysi ikkita
   buyruq, qaysi tartibda kerak?
