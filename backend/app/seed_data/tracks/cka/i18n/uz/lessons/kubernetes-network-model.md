## Va’da

Kubernetes Pod tarmog’ini implementatsiya qilmaydi. U uni *spetsifikatsiya
qiladi* va implementatsiyani CNI plugin’ga qoldiradi. Spetsifikatsiya -
uchta gap:

1. Har bir Pod o’zining IP manziliga ega bo’ladi.
2. Har bir Pod har qanday node’dagi har qanday boshqa Pod’ga o’sha IP orqali,
   **NAT’siz** yeta oladi.
3. Node’dagi agentlar (kubelet, DaemonSet) o’sha node’dagi har bir Pod’ga
   yeta oladi.

Qolgan hamma narsa - bridge’lar, overlay’lar, BGP - plugin’ning shu
va’dalarni bajarish usuli.

## Bitta node

Namespace’lar darsidan ma’lumki, plugin har bir node’da quyidagini quradi:

```
node01 (192.168.1.11)
  ├── cni0 bridge 10.244.1.1/24           har bir node uchun bitta subnet
  ├── vethA ── Pod A (eth0 10.244.1.2)
  └── vethB ── Pod B (eth0 10.244.1.3)
```

Har bir Pod’ning namespace’ida `10.244.1.1` (bridge) orqali o’tuvchi default
route bor. A va B bir-biriga bridge orqali yetadi; node’ga ham u orqali
yetadi; MASQUERADE bilan tashqi dunyoga chiqadi.

## Ko’p node: yagona yangi muammo

Node02’da `10.244.2.0/24` bor. Pod A (10.244.1.2) Pod C (10.244.2.4) ga
jo’natadi. Paket `cni0` ga boradi, node o’zining marshrutlar jadvalidan
10.244.2.0/24 ni qidiradi va ... hech nima yo’q. Javoblarning ikki oilasi bor:

**Marshrutlar.** Har bir node’ga qolgan har bir node’ning subnet’i
qayerdaligini o’rgating:

```bash
# node01'da
ip route add 10.244.2.0/24 via 192.168.1.12     # node02'ning subnet'i node02'da turadi
ip route add 10.244.3.0/24 via 192.168.1.13
```

Bu bitta L2 tarmoqda ishlaydi (har bir node boshqa har bir node’ga bevosita
yeta oladi). Kattaroq miqyosda marshrutlarni har bir node’ga emas, routerga
qo’yasiz - yoki plugin ularni tarqatish uchun **BGP** da gaplashsin
(Calico’da sukut bo’yicha shunday). Inkapsulyatsiya yo’q, to’liq tezlik,
paketlar Pod IP’larini boshidan oxirigacha olib yuradi.

**Overlay’lar.** Node’lar turli tarmoqlarda bo’lsa yoki routerlarga tegib
bo’lmasa, har bir Pod paketini node’dan node’ga ketadigan paket ichiga
o’rang:

```
[tashqi: 192.168.1.11 -> 192.168.1.12][VXLAN][ichki: 10.244.1.2 -> 10.244.2.4][ma'lumot]
```

Flannel (VXLAN rejimi), Weave, IPIP/VXLAN rejimidagi Calico. Ozgina
qo’shimcha yuk, va u node’lar bitta UDP port orqali bir-biriga yeta oladigan
har qanday joyda ishlaydi. Pod’lar nuqtayi nazaridan hamon "NAT yo’q" -
ichki paketga tegilmaydi.

## Plugin har bir Pod uchun nima qiladi

Kubelet Pod yaratganda, u CNI plugin’ni (containerd orqali) `ADD` bilan
chaqiradi; plugin:

1. veth juftini yaratadi va bir uchini Pod’ning namespace’iga `eth0`
   sifatida ko’chiradi;
2. ikkinchi uchini node’ning bridge’iga ulaydi (bridge’siz plugin’larda esa
   marshrutlarni sozlaydi);
3. o’zining **IPAM**’idan shu node’ning subnet’idan manzil so’raydi va uni
   tayinlaydi;
4. Pod’ning default route’ini o’rnatadi;
5. IP’ni kubelet’ga qaytaradi, kubelet esa uni Pod’ning `status.podIP`
   maydoniga yozadi.

Plugin’ning DaemonSet’i esa har bir node’da bir martadan klaster
darajasidagi qismni bajargan: node’ning subnet’ini olgan (`node.spec.podCIDR`
dan, uni esa controller manager `--cluster-cidr` dan tayinlaydi), bridge’ni
yaratgan va boshqa node’larga marshrutlarni yoki overlay’ni sozlagan.

```bash
kubectl get nodes -o custom-columns=NAME:.metadata.name,CIDR:.spec.podCIDR
kubectl get pods -o wide                 # Pod IP'lari o'z node'ining CIDR'iga tushadi
ip route | grep 10.244                   # node'da: marshrutlar (overlay'larda `flannel.1` / `tunl0`)
```

## Qaysi plugin va u qanday ishlashini ko’rish

```bash
ls /etc/cni/net.d                                # 10-flannel.conflist, 10-calico.conflist, ...
kubectl get ds -A | grep -iE "flannel|calico|weave|cilium"
ip -d link show flannel.1 2>/dev/null            # VXLAN qurilmasi -> overlay
ip route | grep tunl0                            # Calico IPIP
```

:::exam-tip
Imtihonning tarmoq topshiriqlari sizdan marshrutlar yoki overlay’ni tanlashni
so’ramaydi. Ular sizdan CNI umuman yo’q joyda uni **o’rnatishni**, Pod
CIDR’ini topishni va "node01’dagi Pod’lar node02’dagi Pod’larga yeta
olmayapti" holatini tahlil qilishni so’raydi - bu esa CNI DaemonSet’ining
bitta node’da ishlamayotgani (`kubectl get pods -n kube-flannel -o
wide`), yoki CNI portidagi firewall (Flannel uchun 8472/UDP).
:::

## O’zingizni tekshiring

1. Tarmoq modelining uchta va’dasini ayting.
2. Ko’p node’li klaster bitta node ustiga qanday yagona muammo qo’shadi va
   yechimlarning ikki oilasi qaysilar?
3. Node’ga tayinlangan Pod subnet’ini qaysi obyekt aytadi va uni kim
   tayinlagan?
