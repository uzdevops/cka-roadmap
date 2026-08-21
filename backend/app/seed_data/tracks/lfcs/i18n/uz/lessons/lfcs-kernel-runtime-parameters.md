## Ishlab turgan kernel’ni sozlash

Kernel’ning yuzlab sozlamalarini tizim ishlab turganda `/proc/sys` orqali
o’zgartirish mumkin. `sysctl` - ularga interfeys; parametrning nomi -
uning yo’li, slashlar nuqtaga almashtirilgan holda.

```
/proc/sys/net/ipv4/ip_forward   ⇄   net.ipv4.ip_forward
```

```bash
sysctl -a                                  # har bir parametr va qiymati (yuzlab)
sysctl -a | grep -i forward
sysctl net.ipv4.ip_forward                 # bittasini o'qish
cat /proc/sys/net/ipv4/ip_forward          # xuddi shu qiymat, boshqa yo'l bilan
```

## Hozir o’zgartirish (doimiy emas)

```bash
sudo sysctl -w net.ipv4.ip_forward=1
sudo sysctl net.ipv4.ip_forward=1                  # -w ixtiyoriy
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward    # ekvivalenti
sudo sysctl -w vm.swappiness=10
```

Bular reboot’gacha saqlanadi. (`sudo echo 1 > /proc/...` ishlamaydi -
faylni shell sizning nomingizdan ochadi; `| sudo tee` ishlating.)

## Doimiy o’zgartirish

```bash
sudo vi /etc/sysctl.d/99-custom.conf
```

```
net.ipv4.ip_forward = 1
vm.swappiness = 10
net.core.somaxconn = 1024
fs.file-max = 200000
```

```bash
sudo sysctl -p /etc/sysctl.d/99-custom.conf   # bu faylni hozir qo'llaydi
sudo sysctl --system                           # BARCHA sysctl konfiguratsiya fayllarini tartib bilan qayta o'qiydi
sysctl net.ipv4.ip_forward                     # tekshirish
```

| Joy | Vazifasi |
|---|---|
| `/etc/sysctl.conf` | an’anaviy yagona fayl (hozir ham o’qiladi) |
| `/etc/sysctl.d/*.conf` | **afzal ko’riladi**: drop-in’lar, leksik tartibda o’qiladi - `99-` g’olib |
| `/usr/lib/sysctl.d/`, `/run/sysctl.d/` | vendor va runtime sukut qiymatlari |

Keyingi fayllar oldingilarini bekor qiladi; `99-custom.conf` ichidagi
sozlama vendor’ning `50-default.conf` faylidan ustun. Doimiy fayllar
qo’llanmaguncha yoki reboot bo’lmaguncha hech narsani o’zgartirmaydi - doim
`sysctl --system`’ni ishga tushiring va keyin qiymatni qaytadan o’qing.

## Bilishga arziydigan parametrlar

| Parametr | Nima qiladi |
|---|---|
| `net.ipv4.ip_forward` | interface’lar orasida paketlarni yo’naltiradi - NAT, router’lar va konteynerlar uchun kerak |
| `net.ipv6.conf.all.forwarding` | IPv6 uchun ekvivalenti |
| `net.ipv4.conf.all.rp_filter` | teskari yo’l bo’yicha filtrlash (anti-spoofing) |
| `net.ipv4.icmp_echo_ignore_all` | ping’ga javob berishni to’xtatadi |
| `net.ipv4.tcp_syncookies` | SYN-flood’dan himoya |
| `net.core.somaxconn` | listen backlog - band serverlarda oshiring |
| `net.ipv4.ip_local_port_range` | vaqtinchalik (ephemeral) portlar diapazoni |
| `vm.swappiness` | 0-100: qanchalik tez swap qilinadi (RAM yetarli serverlarda 10) |
| `vm.max_map_count` | har bir process uchun xotira map’lari - Elasticsearch 262144 talab qiladi |
| `vm.overcommit_memory` | xotirani overcommit qilish siyosati (Redis 1’ni so’raydi) |
| `fs.file-max`, `fs.inotify.max_user_watches` | tizim bo’yicha fayl handle’lari; inotify kuzatuvlari (IDE’lar, log yig’uvchilar) |
| `kernel.pid_max`, `kernel.panic`, `kernel.sysrq` | pid maydoni, panic’dan keyin reboot sekundlari, SysRq tugmalari |

```bash
sudo sysctl -w net.ipv4.ip_forward=1                 # klassikasi: host'ni router'ga aylantiradi (10-hafta)
sudo sysctl -w vm.max_map_count=262144
sysctl -a --pattern 'net.ipv4.conf.(all|default).rp_filter'
```

## Kernel modullari, qisqacha

Ba’zi parametrlar faqat modul yuklangandan keyin paydo bo’ladi, modullarning
esa o’z opsiyalari bor:

```bash
lsmod                                 # yuklangan modullar
modinfo nbd                           # tavsifi va parametrlari
sudo modprobe nbd                     # yuklaydi
sudo modprobe -r nbd                  # yuklamasini oladi
echo nbd | sudo tee /etc/modules-load.d/nbd.conf      # boot'da yuklanadi
echo "options nbd nbds_max=8" | sudo tee /etc/modprobe.d/nbd.conf
cat /sys/module/nbd/parameters/nbds_max
```

## Boot vaqtidagi kernel parametrlari

Boshqa narsa, lekin bir xil so’z: boot loader uzatadigan **buyruq qatori**
parametrlari (`quiet`, `nomodeset`, `systemd.unit=rescue.target`,
`transparent_hugepage=never`).

```bash
cat /proc/cmdline                     # bu boot'ga nima berilgan
sudo vi /etc/default/grub             # GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
sudo update-grub                      # Debian/Ubuntu
sudo grub2-mkconfig -o /boot/grub2/grub.cfg    # RHEL
```

Ularga reboot kerak; sysctl qiymatlariga esa kerak emas.

:::exam-tip
Topshiriq deyarli har doim shunday: "IP forwarding’ni **doimiy** yoqing".
Bu ikkala yarmini ham bildiradi - `/etc/sysctl.d/*.conf` ichidagi qator
**va** uni qo’llash (`sysctl --system` yoki `sysctl -p`) - keyin `= 1`
ekanini ko’rsatish uchun `sysctl net.ipv4.ip_forward`. Yolg’iz
`sysctl -w` ballni yo’qotadi, chunki reboot uni bekor qiladi.
:::

## O’zingizni tekshiring

1. `net.ipv4.ip_forward` parametr nomi `/proc` ostidagi yo’l bilan qanday
   bog’liq?
2. Qaysi ikki qadam sysctl o’zgarishini doimiy qiladi va buni qanday
   tekshirasiz?
3. sysctl parametri bilan kernel buyruq qatori parametri o’rtasida qanday
   farq bor?
