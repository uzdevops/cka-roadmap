## Konfiguratsiyaning uchta qatlami

```
 ip / ifconfig     → yadro, hozir, QAYTA YUKLASHDA YO'QOLADI
 NetworkManager (nmcli) / netplan / systemd-networkd → doimiy konfiguratsiya fayllari
 DHCP             → server tarqatadigan konfiguratsiya
```

Ko’rish va sinash uchun `ip`dan foydalaning; o’zgarish saqlanib qolishi
uchun doimiy vositadan foydalaning. Qaysi doimiy vosita: Ubuntu server
**netplan**dan foydalanadi (u esa NetworkManager yoki systemd-networkd’ni
boshqaradi); desktop’lar va RHEL to’g’ridan-to’g’ri **NetworkManager**dan
foydalanadi.

## Ko’rish

```bash
ip a; ip addr show eth0
ip link show                       # holat UP/DOWN, MAC, MTU
ip -br a                           # qisqacha, har interfeysga bitta qator
ip -4 a; ip -6 a
ip r; ip -6 r; ip r get 8.8.8.8
ip neigh                           # ARP jadvali
nmcli device status
nmcli connection show
hostnamectl
resolvectl status
```

## Hozir o’zgartirish (doimiy emas)

```bash
sudo ip link set eth0 up
sudo ip link set eth0 down
sudo ip addr add 192.168.1.50/24 dev eth0
sudo ip addr del 192.168.1.50/24 dev eth0
sudo ip route add default via 192.168.1.1
sudo ip route add 10.0.0.0/8 via 192.168.1.254 dev eth0
sudo ip route del default
sudo ip link set eth0 mtu 9000
sudo ip -6 addr add 2001:db8::10/64 dev eth0
```

Yuqoridagi hamma narsa reboot’dan yoki NetworkManager qayta ishga
tushirilgandan keyin yo’qoladi. Shuning uchun `ip` gipotezani sinash uchun
ideal ("gap gateway’damikan?") va konfiguratsiya uchun noto’g’ri.

## nmcli bilan doimiy

```bash
nmcli con show                                   # connection profillari
nmcli con show "Wired connection 1"              # har bir xossa
nmcli dev status

# statik IPv4
sudo nmcli con mod eth0 \
  ipv4.method manual \
  ipv4.addresses 192.168.1.50/24 \
  ipv4.gateway 192.168.1.1 \
  ipv4.dns "1.1.1.1 8.8.8.8" \
  ipv4.dns-search example.com
sudo nmcli con up eth0                            # qo'llash

# yana DHCP'ga qaytish
sudo nmcli con mod eth0 ipv4.method auto ipv4.addresses "" ipv4.gateway ""
sudo nmcli con up eth0

# yangi profil
sudo nmcli con add type ethernet con-name lab ifname eth1 \
  ip4 10.0.0.5/24 gw4 10.0.0.1
sudo nmcli con mod lab ipv6.method manual ipv6.addresses 2001:db8::5/64 ipv6.gateway 2001:db8::1
sudo nmcli con up lab
sudo nmcli con delete lab
sudo nmcli con mod eth0 connection.autoconnect yes
```

Profillar - `/etc/NetworkManager/system-connections/*.nmconnection`
ichidagi fayllar (rejimi 600 - ular Wi-Fi kalitlarini saqlashi mumkin).

## netplan bilan doimiy (Ubuntu)

```bash
ls /etc/netplan/
sudo vi /etc/netplan/01-netcfg.yaml
```

```yaml
network:
  version: 2
  renderer: networkd            # yoki NetworkManager
  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - 192.168.1.50/24
        - 2001:db8::10/64
      routes:
        - to: default
          via: 192.168.1.1
        - to: 10.0.0.0/8
          via: 192.168.1.254
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8]
        search: [example.com]
    eth1:
      dhcp4: true
```

```bash
sudo chmod 600 /etc/netplan/01-netcfg.yaml
sudo netplan generate                 # backend konfiguratsiyasini yaratish
sudo netplan try                      # 120 soniyada avtomatik rollback bilan qo'llash  ← masofadan shuni ishlating
sudo netplan apply                    # darhol qo'llash
ip a; ip r
```

:::warning
YAML: ikki probelli otstup, **tab yo’q**, va fayl tartibga sezgir.
`netplan try` - o’zgarishni SSH orqali qo’llashning xavfsiz yo’li: o’zingizni
qulflab qo’ysangiz, u ikki daqiqadan keyin o’zi qaytaradi. `netplan apply`
esa qaytarmaydi.
:::

## Hostname va hosts

```bash
hostnamectl                                   # static, pretty, transient hostname'lar
sudo hostnamectl set-hostname web01.example.com
hostname; hostname -f                          # qisqa; to'liq malakali
cat /etc/hostname
sudo vi /etc/hosts
```

```
127.0.0.1       localhost
127.0.1.1       web01.example.com web01
192.168.1.60    db01.example.com db01
::1             localhost ip6-localhost ip6-loopback
```

`/etc/hosts` dagi yozuv DNS’ni yengadi (`nsswitch.conf` bo’yicha) - qat’iy
moslik uchun qulay va "aynan shu mashinada noto’g’ri manzilga yechilyapti"
degan holatning klassik sababi.

## DNS yechish

```bash
cat /etc/resolv.conf
resolvectl status                          # systemd-resolved'ning haqiqati
resolvectl query example.com
sudo resolvectl flush-caches
dig example.com; dig +short example.com; dig @1.1.1.1 example.com
dig -x 192.168.1.60                        # teskari qidiruv
host example.com; nslookup example.com
getent hosts example.com                    # dasturlar qanday yechsa, shunday (hosts + DNS)
```

systemd-resolved ishlaydigan tizimlarda DNS’ni `/etc/resolv.conf`ni
tahrirlab emas, nmcli/netplan orqali sozlang - u yaratilgan stub faylga
symlink.

## Har safar tekshirish

```bash
ip -br a; ip r
ping -c2 <gateway>; ping -c2 8.8.8.8; ping -c2 example.com
ss -tulpn | head
traceroute 8.8.8.8
```

:::exam-tip
"eth0’ni A/N statik manzil, G gateway va D DNS bilan doimiy sozlang" →
nmcli’ning to’rtta `ipv4.*` xossasi, keyin `con up`, yoki netplan bloki,
keyin `netplan apply`. `ip a`, `ip r` va `ping` bilan tekshiring - va eng
ko’p tushirib qoldiriladigan qism bo’lgan DNS yarmini unutmang.
:::

## O’zingizni tekshiring

1. Nega `ip addr add` manzilni sozlash uchun yetarli emas va u nimaga
   yaraydi?
2. `eth0`da statik manzil, gateway va DNS o’rnatadigan nmcli buyrug’ini
   yozing.
3. Nega SSH orqali `netplan apply` emas, `netplan try` ishlatish kerak?
