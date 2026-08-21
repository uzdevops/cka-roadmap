## Host gaplashishi uchun nima bajarilgan bo’lishi kerak

To’rtta narsa, va har qanday tarmoq muammosi - shulardan birining yo’qligi:

1. ko’tarilgan (up) **interfeys**,
2. prefiks uzunligi bilan **manzil**,
3. qolgan hamma narsaga **route** (odatda default gateway),
4. nomlardan foydalanmoqchi bo’lsangiz - **nom yechish** (DNS).

```bash
ip a          # 1 va 2
ip r          # 3
cat /etc/resolv.conf   # 4
```

## Manzillar va prefikslar

IPv4 manzili - 32 bit, to’rtta bayt ko’rinishida yoziladi: `192.168.1.10`.
**Prefiks uzunligi** (`/24`) boshidagi nechta bit tarmoq ekanini aytadi;
qolgani host’ni belgilaydi.

| CIDR | Netmask | Hostlar | Izoh |
|---|---|---|---|
| `/24` | 255.255.255.0 | 254 | kundalik LAN |
| `/25` | 255.255.255.128 | 126 | |
| `/16` | 255.255.0.0 | 65534 | |
| `/30` | 255.255.255.252 | 2 | point-to-point ulanishlar |
| `/32` | 255.255.255.255 | 1 | bitta host (loopback’lar, route’lar) |

`192.168.1.10/24` uchun: network `192.168.1.0`, broadcast `192.168.1.255`,
foydalanish mumkin bo’lgani `.1`-`.254`. Har bir subnet’ning ikkita manzili
ishlatilmaydi - network va broadcast - shuning uchun `/24` 256 emas, 254
beradi.

**Xususiy diapazonlar** (RFC 1918), internetda hech qachon
marshrutlanmaydi: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`. Ustiga
`127.0.0.0/8` loopback va `169.254.0.0/16` link-local (shu diapazondagi
manzil "DHCP ishlamadi" degani).

```bash
ipcalc 192.168.1.10/26        # network, broadcast, diapazon - o'rnatilgan bo'lsa
sipcalc 10.0.0.0/22
```

## IPv6, sizga kerak bo’ladigan qismlar

128 bit, to’rttadan hex raqamli sakkizta guruh, qisqartirish qoidalari
bilan:

```
2001:0db8:0000:0000:0000:ff00:0042:8329
2001:db8:0:0:0:ff00:42:8329        ← har guruhdagi boshidagi nollar tashlanadi
2001:db8::ff00:42:8329             ← :: nol guruhlarning BITTA ketma-ketligini almashtiradi (faqat bir marta)
```

| Prefiks | Turi |
|---|---|
| `::1/128` | loopback (IPv4’dagi 127.0.0.1) |
| `fe80::/10` | **link-local** - har bir interfeysda avtomatik bittadan bor; faqat o’sha link’da amal qiladi |
| `fc00::/7` | unique local (IPv4’dagi xususiy diapazonlar) |
| `2000::/3` | global unicast - marshrutlanadigan internet |
| `ff00::/8` | multicast (IPv6’da broadcast yo’q) |

Odatdagi taqsimot - har bir subnet uchun `/64`, va hostlar ko’pincha
router advertisement’lardan **SLAAC** orqali o’zini sozlaydi - DHCP kerak
emas. Link-local manzil o’z interfeysi bilan yozilishi shart: `ping6
fe80::1%eth0`.

## Marshrutlash

```bash
ip r
# default via 192.168.1.1 dev eth0 proto dhcp metric 100
# 192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.10
```

Har bir paket uchun yadro mos keladigan **eng aniq** route’ni tanlaydi;
`default` (`0.0.0.0/0`) qolgan hamma narsaga mos keladi va gateway’ni
ko’rsatadi. Gateway **bevosita ulangan subnet’da** bo’lishi shart - shuning
uchun prefiksingizdan tashqaridagi gateway "Network is unreachable" beradi.

```bash
ip r get 8.8.8.8          # qaysi route va source manzil ishlatilgan BO'LARDI
ip -6 r
```

## Nom yechish

```bash
cat /etc/nsswitch.conf | grep hosts
# hosts: files dns          ← avval /etc/hosts, keyin DNS
cat /etc/hosts
cat /etc/resolv.conf
# nameserver 192.168.1.1
# search example.com        ← to'liqsiz nomlarga shu qo'shiladi
resolvectl status           # systemd-resolved'ning haqiqiy ko'rinishi (resolv.conf stub symlink bo'lishi mumkin)
```

Tartib: `/etc/hosts`, keyin `/etc/resolv.conf`’dagi DNS serverlar.
systemd-resolved ishlaydigan tizimlarda `/etc/resolv.conf` stub’ga
(`127.0.0.53`) symlink bo’ladi va haqiqiy serverlar `resolvectl status`’da
turadi - unda faylni to’g’ridan-to’g’ri tahrirlash befoyda, chunki u qayta
yaratiladi.

## Portlar va kim tinglayapti

```bash
ss -tulpn
# tcp LISTEN 0 128 0.0.0.0:22   users:(("sshd",pid=800,fd=3))
```

Manzil va port birgalikda servisni belgilaydi. `0.0.0.0:22` har bir
interfeysda tinglaydi; `127.0.0.1:5432` esa faqat loopback’da - shuning
uchun ma’lumotlar bazasi "ishlab turgan" bo’lib, boshqa hostdan yetib
bo’lmaydigan bo’lishi mumkin. 1024 dan pastdagi portlar root talab qiladi
(yoki `CAP_NET_BIND_SERVICE`). `/etc/services` mashhurlarini nomlaydi: 22
ssh, 25 smtp, 53 dns, 80 http, 443 https, 3306 mysql, 5432 postgres.

## Diagnostika narvoni

```bash
ip link show                     # 1. interfeys UP mi? (NO-CARRIER = kabel/link muammosi)
ip a                             # 2. manzil bormi? 169.254.x.x = DHCP ishlamadi
ping -c2 192.168.1.1             # 3. gateway'ga yetib boramanmi? (o'z subnetimda layer 2 + 3)
ping -c2 8.8.8.8                 # 4. internetga IP bo'yicha yetib boramanmi? (marshrutlash + NAT)
ping -c2 google.com              # 5. DNS ishlaydimi? (4 ishlab, 5 ishlamasa - bu DNS)
ss -tulpn                        # 6. servis tinglayaptimi va qaysi manzilda?
traceroute 8.8.8.8               # yo'l qayerda to'xtaydi
```

Uni tartib bilan bajaring - ishlamagan pog’ona nosozlikning o’zi. "IP bilan
ishlaydi, nom bilan yo’q" - bu DNS; "gateway ping bo’ladi, internet yo’q" -
bu marshrutlash yoki NAT; "manzil yo’q" - bu DHCP yoki konfiguratsiya.

:::exam-tip
Nazariyani imtihonning amaliy savollariga javob bera oladigan darajada
biling: `/26` qaysi netmask ekani, gateway berilgan manzildan yetib
boriladimi va nega `127.0.0.1`’dagi servisga masofadan yetib bo’lmaydi.
Keyingi dars sozlash bilan shug’ullanadi; bu narvon esa har bir
o’zgarishdan oldin va keyin ishga tushiradigan narsangiz.
:::

## O’zingizni tekshiring

1. Host boshqa hostga nom orqali yetib borishi uchun qaysi to’rtta narsa
   bajarilgan bo’lishi kerak?
2. `/26`’da nechta foydalanish mumkin bo’lgan manzil bor va ishlatib
   bo’lmaydigan ikkitasi qaysi?
3. `8.8.8.8`’ga ping ishlaydi, lekin `ping google.com` ishlamaydi. Nima
   buzilgan?
