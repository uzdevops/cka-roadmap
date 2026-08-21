## Ikkita boshqa-boshqa muammo

**Bridge** interfeyslarni bitta layer-2 segmentga birlashtiradi - bu
dasturiy switch. **Bond** esa interfeyslarni zaxiralash yoki
o’tkazuvchanlik uchun bitta mantiqiy interfeysga birlashtiradi. Ular
ko’pincha chalkashtiriladi, chunki ikkalasi ham "interfeyslarni
birlashtiradi"; lekin qarama-qarshi sabablarga ko’ra birlashtiradi.

```
 BRIDGE (host ichidagi switch)              BOND (bir nechtadan yasalgan bitta link)
   eth0 ─┐                                    eth0 ─┐
   vnet0 ─┼─ br0 ── IP shu yerda              eth1 ─┼─ bond0 ── IP shu yerda
   vnet1 ─┘                                          (bitta yo'l, bir nechta kabel)
```

## Bridge’lar

Bridge har bir portda MAC manzillarni o’rganadi va freymlarni ular orasida
uzatadi - xuddi jismoniy switch kabi. Host **bridge**ga IP manzil berib,
uni o’z interfeysi sifatida ishlatishi mumkin.

Uni qayerda uchratasiz:

- **Virtual mashinalar**: `br0` jismoniy NIC’ni va har bir VM’ning
  `vnetN`ini o’z ichiga oladi, shuning uchun VM’lar LAN’da oddiy hostlar
  bo’lib ko’rinadi (VM darsidagi "bridge" tarmoq rejimi).
- **Konteynerlar**: `docker0` - xususiy subnet va NAT bilan bridge.
- Switch sotib olmasdan **ikkita segmentni birlashtirish**.

Yodda tutishga arziydigan faktlar:

- Bridge - layer 2: u **MAC** bo’yicha uzatadi, IP subnet’lar bilan ishi
  yo’q va marshrutlamaydi.
- Interfeys bridge’ga qo’shilgach, **o’zining IP’si bo’lmasligi kerak** -
  manzil bridge’ga ko’chadi.
- Broadcast trafik bridge’dan o’tadi; portlar bitta to’qnashuvsiz
  segmentni bo’lishadi.
- **STP** (Spanning Tree Protocol) bridge’lar halqa qilib ulanganda
  loop’larning oldini oladi; oddiy host bridge’ida `stp off` qilmasangiz,
  u ~30 soniya uzatish kechikishiga tushadi.

## Bond’lar (link agregatsiyasi, "teaming", "NIC teaming")

Bir nechta NIC bitta interfeys kabi ishlaydi. Ikki sabab: **kabel, port
yoki switch nosozligidan omon qolish** va **bittadan ortiq link’ning
o’tkazuvchanligidan foydalanish**. Ba’zi rejimlar switch tomonidan
hamkorlikni talab qiladi, ba’zilari yo’q.

| Rejim | Nomi | Switch qo’llab-quvvatlashi | Nima beradi |
|---|---|---|---|
| 0 | `balance-rr` | statik agregatsiya kerak | round-robin; paketlar tartibini buzishi mumkin |
| **1** | **`active-backup`** | **kerak emas** | faqat zaxiralash - bitta link faol, qolganlari bo’sh |
| 2 | `balance-xor` | statik agregatsiya | MAC/IP hash’i bo’yicha yuk taqsimlash |
| 3 | `broadcast` | kerak emas | har bir freym har bir linkda (kam uchraydi) |
| **4** | **`802.3ad` (LACP)** | **LACP sozlangan** | standart agregatsiya: kelishilgan, yuki taqsimlangan, nosozlikka chidamli |
| 5 | `balance-tlb` | kerak emas | uzatishda yuk taqsimlash |
| 6 | `balance-alb` | kerak emas | uzatish va qabul qilishda yuk taqsimlash |

Amalda ishlatadiganingiz ikkitasi: switch’ni sozlay olmasangiz (yoki
NIC’lar ikki xil switch’ga ketsa) **1-rejim**, sozlay olsangiz **4-rejim
(LACP)** - u sanoat standarti va nosozliklarni to’g’ri aniqlaydi.

Bond parametrlari:

| Parametr | Ma’nosi |
|---|---|
| `miimon=100` | link holatini har 100 ms da tekshirish (asosiy nosozlik detektori) |
| `updelay` / `downdelay` | link’ni up/down deb e’lon qilishdan oldin kutish - flapping’ning oldini oladi |
| `lacp_rate=fast` | LACP paketlari har 30 soniyada emas, har soniyada |
| `xmit_hash_policy=layer3+4` | chiquvchi linkni qaysi maydonlar tanlashi (yaxshiroq taqsimlanish) |
| `primary=eth0` | active-backup’da afzal ko’riladigan faol link |

```bash
cat /proc/net/bonding/bond0        # rejim, faol slave, har bir link holati - diagnostikada o'qiladigan fayl
```

Kutilmani to’g’ri qo’yish muhim: agregatsiya paketlarni emas,
**oqimlarni** taqsimlaydi. Ikkita 1 Gbit link bitta TCP ulanishni
2 Gbit’da ishlatmaydi; ular ikkita ulanishga bittadan link beradi.
Zaxiralash - determinlashgan, o’tkazuvchanlik - statistik.

## Bond ustidagi bridge

Virtualizatsiya hosti uchun production shabloni: zaxiralash uchun
NIC’larni bond qiling, ustiga bridge qo’ying va VM’lar unga ulansin.

```
 eth0 ─┐
       ├─ bond0 (802.3ad) ─── br0 ─── vnet0, vnet1 (VMs)   ← host'ning IP'si br0 da
 eth1 ─┘
```

## VLAN’lar, bitta xatboshida

VLAN tegi bitta jismoniy linkni bir nechta mantiqiy tarmoqqa bo’ladi
(`eth0.10`, `eth0.20`). Bridge, bond va VLAN’lar bir-birining ustiga
qo’yiladi: `bond0.10` - bond’dagi VLAN 10, `br10` esa uni o’sha VLAN’dagi
VM’larga bridge qiladi. Bu asosiy LFCS maqsadi emas, lekin bu atamalar
o’sha suhbatlarda uchrab turadi.

:::warning
Ikkala o’zgarish ham o’z ulanishingizni uzishi mumkin: siz ulanib turgan
interfeysni qo’shish IP’ni bridge yoki bond’ga ko’chiradi va biror qadam
noto’g’ri bo’lsa, sessiya o’ladi. Buni konsoldan qiling (`virsh console`,
IPMI), yoki `nmcli`’ni skriptlangan rollback bilan ishlating, yoki jismoniy
kirish kerak bo’lishi mumkinligini qabul qiling. Masofadagi production
hostda hech qachon "shunchaki sinab ko’ray" demang.
:::

:::exam-tip
Atamalarni va ikkita rejim nomini biling: `active-backup` (switch’ni
sozlash shart emas) va `802.3ad` (LACP, switch kerak). IP qo’shilgan
interfeyslarga emas, `br0`/`bond0`’ga tegishli ekanini va bond’ning haqiqiy
holatini `/proc/net/bonding/bond0`’dan o’qish kerakligini biling. Keyingi
dars ikkalasini quradi.
:::

## O’zingizni tekshiring

1. Bridge qaysi muammoni yechadi va bond qaysi muammoni yechadi?
2. Qaysi bonding rejimi switch’ni sozlashni talab qilmaydi va qaysi biri
   kelishiladigan standart?
3. `eth0` `br0`’ga qo’shilgandan keyin IP manzil qaysi interfeysda turadi
   va nega?
