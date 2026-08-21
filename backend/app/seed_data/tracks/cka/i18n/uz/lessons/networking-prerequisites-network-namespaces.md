## Konteynerlarning o’z tarmoq stegi bor

Konteyner o’z interfeyslarini, o’z marshrutlash jadvalini, o’z ARP keshini
ko’radi - host’nikini emas. Bu izolyatsiya - **network namespace**: yadro
tarmoq holatining nusxasi, ichidagi jarayonlar uchun shaxsiy. Har bir Pod -
shunday namespace. Ularni qo’lda tushunish - CNI plugin nima qilishini
tushunishning eng tez yo’li.

```bash
ip netns add red
ip netns add blue
ip netns                         # ro'yxat
ip netns exec red ip link        # faqat `lo`, va u DOWN holatida
ip -n red link                   # xuddi shu narsa, qisqaroq
ip netns exec red ip route       # bo'sh
ip netns exec red arp           # bo'sh
```

Yangi namespace’da hech nima yo’q: loopback’dan boshqa interfeys yo’q,
route yo’q. Host’ning `eth0` i ichkaridan ko’rinmaydi. Host’ning o’z holati
**root namespace**’da turadi.

## Ikki namespace’ni ulash: veth juftligi

**Virtual Ethernet juftligi** - ikki uchida vilkasi bor kabel; bir uchiga
kirgan narsa ikkinchisidan chiqadi. Har bir namespace’ga bittadan uchini
joylang:

```bash
ip link add veth-red type veth peer name veth-blue
ip link set veth-red netns red
ip link set veth-blue netns blue
ip -n red addr add 192.168.15.1/24 dev veth-red
ip -n blue addr add 192.168.15.2/24 dev veth-blue
ip -n red link set veth-red up
ip -n blue link set veth-blue up
ip netns exec red ping 192.168.15.2        # ishlaydi: red <-> blue kabel orqali
ip netns exec red arp                      # blue'ning MAC'i o'rganildi
```

Ikki Pod va ular orasida kabel. Bu masshtablanmaydi: to’rtta namespace uchun
oltita kabel kerak bo’lardi.

## Ko’pini ulash: bridge

**Bridge** - root namespace’dagi dasturiy switch. Har bir namespace veth
juftligini oladi: bir uchi namespace ichida, ikkinchi uchi bridge’ga
ulanadi:

```bash
ip link add v-net-0 type bridge
ip link set v-net-0 up
ip addr add 192.168.15.5/24 dev v-net-0          # bridge'da HOST'ga ham manzil berish

ip link add veth-red type veth peer name veth-red-br
ip link set veth-red netns red
ip link set veth-red-br master v-net-0
ip -n red addr add 192.168.15.1/24 dev veth-red
ip -n red link set veth-red up
ip link set veth-red-br up
# blue uchun ham xuddi shunday, 192.168.15.2 bilan
ip netns exec red ping 192.168.15.2              # bridge orqali
ping 192.168.15.1                                # host'dan, chunki host'da bridge ustida 192.168.15.5 bor
```

Bu - bitta node’dagi Pod tarmog’i: `v-net-0` ni Docker `docker0` deb, CNI
plugin esa `cni0` yoki `cbr0` deb ataydi; veth juftliklari - Pod’larning
`eth0` lari.

## Tashqariga chiqish: route va NAT

`red` dan `ping 192.168.1.3` (LAN’dagi host) ishlamaydi - red’ning
marshrutlash jadvali uning qayerdaligini bilmaydi. Unga gateway bering:
bridge orqali host.

```bash
ip -n red route add 192.168.1.0/24 via 192.168.15.5
ip netns exec red ping 192.168.1.3       # yuborildi... lekin javob yo'q: 192.168.1.3 da 192.168.15.0/24 ga qaytish route'i yo'q
```

Javob hech qayerga bormaydi, chunki tashqi tarmoq shaxsiy 192.168.15.0/24
borligini bilmaydi. Ikki yechim bor, ikkalasi ham haqiqiy klasterlarda
ishlatiladi:

```bash
# 1. NAT: chiqishda manba manzilini host manziliga qayta yozish
iptables -t nat -A POSTROUTING -s 192.168.15.0/24 -j MASQUERADE
# 2. yoki boshqa hostlarga route o'rgatish: "192.168.15.0/24 via 192.168.1.x (shu host)"
```

Internet uchun esa: `ip -n red route add default via 192.168.15.5` va
yuqoridagi MASQUERADE. Tashqaridan `red` ichidagi xizmatga kirish yana bitta
qoida - host’da DNAT/port forward - va NodePort aynan shuning o’zi.

## Siz nima qurdingiz

| Qo’lda | Kubernetes nomi |
|---|---|
| network namespace | Pod |
| veth juftligi | Pod’ning `eth0` i + host tomonidagi `vethXXXX` |
| `v-net-0` bridge’i | `cni0` / `cbr0` / `docker0` |
| namespace ichidan bridge IP’siga route | Pod’ning default route’i |
| MASQUERADE | Pod’larning internetga chiqishini ta’minlaydigan narsa |
| boshqa hostlarda shu host’ning Pod diapazoniga route | node’dan node’ga Pod trafigi overlay’siz qanday ishlashi |

CNI plugin har safar Pod ishga tushganda aynan shu buyruqlarni, boshqa
nomlar bilan, bajaradi. Keyingi darslar - Docker’ning varianti va undan
keyin CNI standarti.

:::tip
`ip netns exec <ns> <command>` namespace ichida istalgan buyruqni bajaradi -
`ip`, `ping`, `ss`, `curl`. Bu - "bu Pod nimani ko’radi" degan savol uchun
tekshirish usuli: `kubectl exec` mavjud bo’lmasa yoki image’da vositalar
bo’lmasa, Pod’ning namespace’ini `crictl inspect` yoki `lsns -t net` bilan
toping va host vositalarini uning ichida ishlating.
:::

## O’zingizni tekshiring

1. Yangi network namespace ichida nima bo’ladi?
2. veth juftligining ikki uchi nima va bridge sxemasida ular qayerga boradi?
3. Namespace LAN’ga yubora oladi, lekin javob olmaydi. Nima yetishmayapti va
   uni tuzatishning ikki yo’li qanday?
