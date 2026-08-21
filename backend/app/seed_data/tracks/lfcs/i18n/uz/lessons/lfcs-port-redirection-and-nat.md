## NAT deb ataladigan uchta narsa

| Nomi | Nimani o’zgartiradi | Nima uchun |
|---|---|---|
| **SNAT / masquerade** | chiquvchi paketlarning **manba** manzilini | ko’p xususiy host bitta ommaviy manzilni bo’lishishi uchun |
| **DNAT / port forwarding** | kiruvchi paketlarning **manzilini** | tashqaridan ichki serverga yetib borish uchun |
| **REDIRECT** | o’sha host’dagi manzil **portini** | 80’ni bind qila olmaydigan service uchun 80 → 8080 |

Masquerade - bu chiquvchi interfeysning joriy manzilini oladigan SNAT -
o’sha manzil dinamik bo’lganda to’g’ri tanlov.

## Old shart: IP forwarding

Interfeyslar orasida paket uzatadigan host’ga buni aytish kerak:

```bash
sysctl net.ipv4.ip_forward
sudo sysctl -w net.ipv4.ip_forward=1                       # hozir
echo "net.ipv4.ip_forward = 1" | sudo tee /etc/sysctl.d/99-forward.conf
echo "net.ipv6.conf.all.forwarding = 1" | sudo tee -a /etc/sysctl.d/99-forward.conf
sudo sysctl --system                                        # doimiy
```

Usiz quyidagi har bir NAT rule’i indamay hech narsa qilmaydi.

## firewalld

```bash
# masquerade: 192.168.100.0/24 shu host orqali internetga chiqsin
sudo firewall-cmd --permanent --zone=public --add-masquerade
sudo firewall-cmd --permanent --zone=internal --add-source=192.168.100.0/24
sudo firewall-cmd --reload
firewall-cmd --list-all --zone=public | grep masquerade

# o'sha host'ning o'zida port forwarding: 80 → 8080
sudo firewall-cmd --permanent --add-forward-port=port=80:proto=tcp:toport=8080

# BOSHQA host'ga uzatish (masquerade ham kerak)
sudo firewall-cmd --permanent --add-forward-port=port=443:proto=tcp:toport=443:toaddr=192.168.100.10
sudo firewall-cmd --permanent --add-masquerade
sudo firewall-cmd --reload
firewall-cmd --list-forward-ports
```

Esda tuting: portning o’ziga ham filtr tomonidan **ruxsat** berilishi kerak:
`--add-port=80/tcp`.

## nftables

```bash
sudo nft add table ip nat
sudo nft 'add chain ip nat prerouting  { type nat hook prerouting  priority -100; }'
sudo nft 'add chain ip nat postrouting { type nat hook postrouting priority 100; }'

# eth0 orqali chiqayotgan hamma narsani masquerade qilish
sudo nft add rule ip nat postrouting oifname "eth0" masquerade
# yoki qat'iy ommaviy manzilga aniq SNAT
sudo nft add rule ip nat postrouting oifname "eth0" ip saddr 192.168.100.0/24 snat to 203.0.113.5

# DNAT: eth0'ga kirayotgan 8080 → ichki host
sudo nft add rule ip nat prerouting iifname "eth0" tcp dport 8080 dnat to 192.168.100.10:80
# REDIRECT: shu host'da 80 → 8080
sudo nft add rule ip nat prerouting iifname "eth0" tcp dport 80 redirect to :8080

sudo nft list table ip nat
sudo nft list ruleset | sudo tee /etc/nftables.conf       # saqlash
```

Filtr siyosati `drop` bo’lganda forward chain ham bu trafikka ruxsat
berishi kerak:

```bash
sudo nft add rule inet filter forward ct state established,related accept
sudo nft add rule inet filter forward iifname "eth1" oifname "eth0" accept
```

## iptables (o’sha rule’lar, eskiroq sintaksis)

```bash
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -t nat -A POSTROUTING -s 192.168.100.0/24 -o eth0 -j SNAT --to-source 203.0.113.5
sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8080 -j DNAT --to-destination 192.168.100.10:80
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080
sudo iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT
sudo iptables -t nat -L -n -v
sudo netfilter-persistent save
```

## ufw

ufw’da to’laqonli NAT buyruqlari yo’q; uning rule fayllarini tahrirlang:

```bash
sudo sed -i 's/^DEFAULT_FORWARD_POLICY=.*/DEFAULT_FORWARD_POLICY="ACCEPT"/' /etc/default/ufw
sudo vi /etc/ufw/before.rules       # *filter bo'limidan YUQORIGA *nat blokini qo'shing:
```

```
*nat
:POSTROUTING ACCEPT [0:0]
-A POSTROUTING -s 192.168.100.0/24 -o eth0 -j MASQUERADE
COMMIT
```

```bash
sudo ufw disable && sudo ufw enable
```

## Qaysi hook qachon ishlaydi

```
 kiruvchi ──▶ PREROUTING (DNAT) ──▶ routing qarori ──▶ FORWARD/INPUT (filtr) ──▶ POSTROUTING (SNAT) ──▶ chiqish
```

Siz albatta duch keladigan ikki oqibat:

- **DNAT filtrlashdan oldin sodir bo’ladi**, shuning uchun filtr rule’i
  asl portga emas, **tarjima qilingan** manzilga (ichki host’dagi 80-port)
  ruxsat berishi kerak.
- **Ulanishning faqat birinchi paketi** NAT chain’laridan o’tadi;
  qolganlari conntrack ortidan boradi. Shu sababli ulanish o’rtasida
  qo’shilgan rule ishlamayotganday tuyuladi - mavjud ulanishlar o’z eski
  tarjimasini saqlab qoladi.

## Sinash

```bash
# router'da
sysctl net.ipv4.ip_forward
sudo nft list table ip nat
sudo conntrack -L | head                   # jonli tarjimalar (conntrack-tools)
sudo tcpdump -ni eth0 'port 8080'          # paket yetib kelyaptimi va qaysi manzillar bilan?

# router ortidagi client'dan
ip r                                        # router default gateway'mi?
curl -s ifconfig.me                         # qaysi ommaviy manzil sifatida ko'rinyapman?
ping -c2 8.8.8.8

# tashqaridan
nc -zv <public-ip> 8080
curl -I http://<public-ip>:8080
```

| Alomat | Sababi |
|---|---|
| client’lar internetga chiqa olmayapti | `ip_forward=0`, masquerade rule’i yo’q, yoki FORWARD siyosati drop |
| uzatilgan port refused beryapti | filtr tarjima qilingan portga ruxsat bermayapti; yoki backend tinglamayapti |
| tashqaridan ishlaydi, ichkaridan ommaviy IP bilan ishlamaydi | hairpin NAT sozlanmagan (ichki manba uchun mos rule qo’shing) |
| ishlagan edi, reboot’dan keyin to’xtadi | rule’lar saqlanmagan, yoki `ip_forward` faqat `sysctl -w` bilan o’rnatilgan |
| bitta client ishlaydi, boshqalari yo’q | client’larning default gateway’i bu host emas |

:::exam-tip
Imtihonda odatda ikkitasidan biri so’raladi: "bu host A portini B portiga
uzatsin" (`firewall-cmd --add-forward-port=...` yoki nft’ning `redirect`
rule’i), yoki "ichki tarmoqdagi mashinalar internetga chiqa olsin"
(`ip_forward`’ni **doimiy** yoqish + tashqi interfeysda masquerade).
Ikkala yarmini ham doimiy qiling va rule’larni ro’yxatlash bilan emas,
haqiqiy ulanish bilan tekshiring.
:::

## O’zingizni tekshiring

1. SNAT, masquerade va DNAT orasidagi farq nima?
2. Qaysi sysctl o’rnatilishi kerak va nega yolg’iz `sysctl -w` yetarli
   emas?
3. DNAT rule’i 8080-portni ichki host’ning 80-portiga yuboradi. Filtr
   rule’lari qaysi portga ruxsat berishi kerak va nega?
