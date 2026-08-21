## Ikki mashina, bitta switch

Har qanday Pod networking’idan oldin - har bir node va har bir konteyner
tayanadigan asoslar. Bitta tarmoqdagi ikki host:

```
A (eth0: 192.168.1.10) ──┐
                         ├── switch ── network 192.168.1.0/24
B (eth0: 192.168.1.11) ──┘
```

```bash
ip link                                  # interfeyslar: lo, eth0, ...
ip addr add 192.168.1.10/24 dev eth0     # eth0 ga shu tarmoqdagi manzilni berish
ip addr                                  # manzillarni ko'rsatish
ping 192.168.1.11                        # bir xil tarmoq: switch yetkazib beradi
```

**Switch** bitta tarmoqdagi hostlarni ulaydi; freymlar MAC manzil bo’yicha
yetkaziladi, ARP (`ip neigh`) esa host o’z tarmog’idagi IP uchun MAC’ni
shu tariqa bilib oladi. Hech narsa marshrutlanmaydi; hammasi lokal.

## Ikki tarmoq, bitta router

```
A (192.168.1.10) ── switch 1 ── router ── switch 2 ── C (192.168.2.10)
                    192.168.1.0/24  │  │  192.168.2.0/24
                   router: 192.168.1.1  192.168.2.1
```

**Router**ning har bir tarmoqda interfeysi bor va u paketlarni ular orasida
uzatadi. A C’ga yetishi uchun A’ga **route** kerak: "192.168.2.0/24 ga
yetish uchun 192.168.1.1 ga yubor".

```bash
ip route add 192.168.2.0/24 via 192.168.1.1
ip route                                 # marshrutlash jadvali
```

Va har bir hostda bo’ladigan o’sha yagona route: **default gateway** -
"route’i yo’q hamma narsani shu yerga yubor".

```bash
ip route add default via 192.168.1.1
ip route
# default via 192.168.1.1 dev eth0
# 192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.10
```

:::tip
`ip route` yuqoridan pastga "eng aniq prefiks yutadi" qoidasi bilan
o’qiladi: `/24` route `default`ni yengadi. Paket "hech qayerga bormasa",
birinchi o’qiladigan narsa - shu jadval: o’sha manzil uchun route bormi va
`via` lokal tarmoqda yetib boriladigan narsani ko’rsatyaptimi?
:::

## Linux host router sifatida

Ikkita interfeysi bor har qanday Linux mashina ular orasida paket uzata
oladi - agar unga aytilsa:

```bash
cat /proc/sys/net/ipv4/ip_forward       # 0 = menga atalmagan paketlar tashlanadi
echo 1 > /proc/sys/net/ipv4/ip_forward  # ularni uzat
# saqlab qolish: /etc/sysctl.d/99-k8s.conf da net.ipv4.ip_forward = 1, keyin sysctl --system
```

Bu ko’ringanidan muhimroq: **har bir Kubernetes node’i** o’z Pod’lari uchun
**router**. `ip_forward=1` - kubeadm va CNI talab qiladigan yadro
sozlamalaridan biri; u o’chirilgan node’dagi Pod’lar tashqariga gaplasha
olmaydi.

## Vositalar: zamonaviy va eski

| Eski (net-tools) | Zamonaviy (iproute2) | Nimani ko’rsatadi |
|---|---|---|
| `ifconfig` | `ip addr`, `ip link` | interfeyslar va manzillar |
| `route -n` | `ip route` | marshrutlash jadvali |
| `arp -a` | `ip neigh` | ARP kesh |
| `netstat -nltp` | `ss -nltp` | tinglanayotgan soketlar |
| `brctl show` | `ip link show type bridge`, `bridge link` | bridge’lar |

Imtihon node’larida zamonaviy to’plam aniq bor; eskisi - ehtimol. `ip`ni
o’rganing.

```bash
ip link show eth0                        # holat, MAC
ip -br addr                              # qisqacha, har interfeysga bitta qator
ip route get 8.8.8.8                     # manzil qaysi route va interfeysdan foydalanishi
```

## Nega bu birinchi tarmoq darsi

Bir haftadan keyin uchratadigan Pod tarmog’i shundan iborat: har bir node’da
**bridge** (dasturiy switch), har bir Pod’ni unga ulaydigan **veth
juftliklari**, har bir node’da "node02 ning Pod CIDR’i node02 ning IP’si
orqali" deydigan **route’lar** va paketlarni **uzatadigan** node. Har bir
bo’lak shu sahifada. Qolgani - nomlash.

## O’zingizni tekshiring

1. Switch va router orasidagi farq nima - ularning har biri nimaga qaraydi?
2. 192.168.1.1 ni default gateway qilib qo’shadigan buyruqni va marshrutlash
   jadvalini ko’rsatadigan buyruqni yozing.
3. Kubernetes node’ida `net.ipv4.ip_forward` nega 1 bo’lishi kerak?
