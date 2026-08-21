## nmcli bilan bridge qurish

Buni ikkita NIC’li VM’da, **konsoldan** qiling - o’zingiz hozir qo’shmoqchi
bo’lgan interfeys orqali emas.

```bash
nmcli device status
# DEVICE  TYPE      STATE      CONNECTION
# eth0    ethernet  connected  Wired connection 1
# eth1    ethernet  connected  Wired connection 2
```

```bash
# 1. bridge yaratish
sudo nmcli con add type bridge ifname br0 con-name br0 stp no

# 2. bridge'ga manzil berish (bu yerda statik; DHCP uchun ipv4.method auto)
sudo nmcli con mod br0 ipv4.method manual ipv4.addresses 192.168.1.50/24 \
  ipv4.gateway 192.168.1.1 ipv4.dns 1.1.1.1

# 3. jismoniy interfeysni qo'shish
sudo nmcli con add type ethernet ifname eth1 con-name br0-port1 master br0

# 4. ko'tarish (eth1 dagi eski profil tushirilishi kerak)
sudo nmcli con down "Wired connection 2" 2>/dev/null
sudo nmcli con up br0
sudo nmcli con up br0-port1
```

```bash
ip -br a
# br0        UP   192.168.1.50/24        ← IP MANA SHU YERDA
# eth1       UP                          ← o'zining manzili yo'q
bridge link show
ip link show master br0
nmcli con show br0 | grep -Ei "bridge|ipv4"
ping -c2 192.168.1.1
```

`bridge` buyrug’i uni ko’zdan kechiradi:

```bash
bridge link            # portlar va ularning holati
bridge fdb show br br0 # o'rganilgan MAC jadvali
bridge -d link show    # tafsilot: STP holati, yo'l narxlari
```

Uni olib tashlash:

```bash
sudo nmcli con delete br0-port1 br0
sudo nmcli con up "Wired connection 2"
```

## VM’larni bridge’ga ulash

```bash
sudo virsh attach-interface web01 --type bridge --source br0 --model virtio --config
# yoki virt-install'da:  --network bridge=br0
virsh domiflist web01
```

Endi VM har qanday jismoniy mashina kabi LAN’ning DHCP’sidan manzil oladi.

## nmcli bilan bond qurish

```bash
# 1. bond, link monitoringi bilan active-backup
sudo nmcli con add type bond ifname bond0 con-name bond0 \
  bond.options "mode=active-backup,miimon=100,primary=eth1"

# buning o'rniga LACP:
# bond.options "mode=802.3ad,miimon=100,lacp_rate=fast,xmit_hash_policy=layer3+4"

# 2. bond'ga manzil
sudo nmcli con mod bond0 ipv4.method manual ipv4.addresses 192.168.1.60/24 \
  ipv4.gateway 192.168.1.1 ipv4.dns 1.1.1.1

# 3. a'zolarni qo'shish
sudo nmcli con add type ethernet ifname eth1 con-name bond0-p1 master bond0
sudo nmcli con add type ethernet ifname eth2 con-name bond0-p2 master bond0

# 4. ko'tarish
sudo nmcli con up bond0
sudo nmcli con up bond0-p1
sudo nmcli con up bond0-p2
```

```bash
ip -br a | grep bond
cat /proc/net/bonding/bond0
# Bonding Mode: fault-tolerance (active-backup)
# Primary Slave: eth1 (primary_reselect always)
# Currently Active Slave: eth1
# MII Status: up
# Slave Interface: eth1   MII Status: up   Link Failure Count: 0
# Slave Interface: eth2   MII Status: up   Link Failure Count: 0
```

Failover’ni sinang - butun mashqning maqsadi shu:

```bash
ping -i 0.2 192.168.1.1 &                  # trafik oqib tursin
sudo ip link set eth1 down                 # kabelni sug'urishga taqlid
grep "Currently Active Slave" /proc/net/bonding/bond0     # endi eth2
# ping ko'pi bilan bir-ikkita paket yo'qotadi
sudo ip link set eth1 up
```

## Xuddi shuni netplan bilan (Ubuntu)

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth1: {dhcp4: false}
    eth2: {dhcp4: false}
  bonds:
    bond0:
      interfaces: [eth1, eth2]
      parameters:
        mode: active-backup
        primary: eth1
        mii-monitor-interval: 100
      addresses: [192.168.1.60/24]
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1]
  bridges:
    br0:
      interfaces: [bond0]
      addresses: [192.168.1.50/24]
      parameters:
        stp: false
```

```bash
sudo netplan generate
sudo netplan try            # 120 soniyalik avto-rollback - xavfsiz yo'l
```

## Tez, doimiy bo’lmagan variantlar (faqat sinash uchun)

```bash
sudo ip link add br0 type bridge
sudo ip link set eth1 master br0
sudo ip link set br0 up
sudo ip addr add 192.168.1.50/24 dev br0

sudo modprobe bonding
sudo ip link add bond0 type bond mode active-backup miimon 100
sudo ip link set eth1 down && sudo ip link set eth1 master bond0
sudo ip link set eth2 down && sudo ip link set eth2 master bond0
sudo ip link set bond0 up
```

Reboot’dan keyin yo’qoladi - gipotezani isbotlash uchun foydali, hech
qachon konfiguratsiya sifatida emas.

## Ishlamasa

| Alomat | Nimaga qarash kerak |
|---|---|
| bridge up, ulanish yo’q | IP hali ham slave’da; STP kechikishi (~30 s) - `stp no` qo’ying |
| bond’da bitta slave `MII Status: down` | kabel, switch porti yoki slave hali boshqa connection profiliga tegishli |
| LACP bond trafik o’tkazmayapti | switch tomoni LACP uchun sozlanmagan - sozlangunicha active-backup ishlating |
| ikkala slave up, o’tkazuvchanlik o’zgarmadi | kutilgan holat: agregatsiya bitta oqimni emas, oqimlarni taqsimlaydi |
| o’zgarishdan keyin hostga yetib bo’lmayapti | siz ulanib turgan interfeysni qo’shib qo’ydingiz - konsol kerak |

:::exam-tip
Imtihon varianti qisqa: berilgan parametrlar va manzil bilan bridge yoki
bond yarating, uni doimiy qiling va ishlayotganini ko’rsating.
Ketma-ketlik har doim bir xil to’rt qadam - master’ni yaratish, master’ga
manzil berish, a’zolarni qo’shish, hammasini ko’tarish - keyin
`ip -br a`, `bridge link` yoki `/proc/net/bonding/bond0` bilan tekshiring.
Buni konsoldan qiling.
:::

## O’zingizni tekshiring

1. Ishlaydigan bridge yaratadigan to’rtta nmcli qadami qaysilar?
2. Qaysi fayl bond’ning rejimi, faol slave’i va har bir link holatini
   ko’rsatadi?
3. active-backup bond haqiqatan ham failover qilishini qanday isbotlaysiz?
