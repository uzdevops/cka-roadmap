## Hamma bir xil skriptni yozardi

Docker, rkt, Mesos, Kubernetes - har bir konteyner tizimi har bir konteyner
uchun bir xil qadamlarni bajarishi kerak edi: namespace yaratish, veth juftini
yasash, uni bridge’ga ulash, IP tayinlash, marshrutlar qo’shish va o’chirishda
hammasini orqaga qaytarish. Har biri o’z kodini yozardi. **Container Network
Interface** - buni to’xtatish haqidagi kelishuv: runtime chaqiradigan va
plugin implementatsiya qiladigan bitta interfeys.

```
runtime (kubelet, containerd orqali) ──▶ plugin binary: ADD <container-id> <netns>  ──▶ plugin tarmoqni sozlaydi, IP qaytaradi
                                     ──▶ plugin binary: DEL <container-id> <netns>  ──▶ plugin tozalab qo'yadi
```

Kelishuv to’liq holda:

- Runtime tarmoq namespace’ini yaratadi.
- U konteyner qo’shilishi kerak bo’lgan tarmoqni aniqlaydi (config fayldan).
- U plugin **ijro etiluvchi faylini** `ADD` (yoki `DEL`, `CHECK`,
  `VERSION`) bilan chaqiradi, unga konteyner ID’si va namespace yo’lini,
  ustiga stdin orqali config’ni uzatadi.
- Plugin nima qilsa qiladi va o’zi yaratgan interfeyslar hamda IP’lar bilan
  JSON natija chiqaradi.

Plugin - shu fe’llarni qayta ishlaydigan **har qanday dastur**. Ko’pchiligi
Go’da yozilgan; siz uni bash’da ham yozishingiz mumkin.

## Node’da qismlar qayerda turadi

```bash
ls /opt/cni/bin/
# bridge  dhcp  flannel  host-local  loopback  macvlan  portmap  ptp  tuning  vlan  ...  (o'rnatilgan bo'lsa calico, weave-net, cilium-cni ham)
ls /etc/cni/net.d/
# 10-flannel.conflist      (yoki 10-calico.conflist, 05-cilium.conflist, ...)
```

| Yo’l | Nima turadi |
|---|---|
| `/opt/cni/bin` | plugin binary’lari (`--cni-bin-dir`) |
| `/etc/cni/net.d` | tarmoq konfiguratsiyasi; **alifbo bo’yicha birinchi fayl** ishlatiladi (`--cni-conf-dir`) |

```bash
cat /etc/cni/net.d/10-bridge.conf
```

```json
{
  "cniVersion": "1.0.0",
  "name": "mynet",
  "type": "bridge",                 # /opt/cni/bin dagi qaysi binary ishga tushadi
  "bridge": "cni0",
  "isGateway": true,
  "ipMasq": true,
  "ipam": {
    "type": "host-local",           # ikkinchi plugin, manzillarni boshqarish uchun
    "subnet": "10.244.1.0/24",
    "routes": [{"dst": "0.0.0.0/0"}]
  }
}
```

Bu config’ni namespace darsi bilan solishtirib o’qing: `type: bridge` - siz
qo’lda bajargan skript; `isGateway` bridge’ga IP beradi; `ipMasq`
MASQUERADE qoidasini qo’shadi; `ipam` esa IP’ni subnet’dan tanlaydi.

`.conflist` bir nechta plugin’ni zanjirga ulaydi: `flannel`, keyin `portmap`
(hostPort qo’llab-quvvatlashi), keyin `bandwidth`. ADD uchun har biri navbat
bilan, DEL uchun teskari tartibda ishlaydi.

## Reference plugin’lar va haqiqiy CNI’lar

CNI loyihasi **reference plugin’lar** to’plamini beradi - `bridge`, `ptp`,
`macvlan`, `host-local`, `dhcp`, `portmap`, ... - qurilish g’ishtlari.
Flannel, Calico, Cilium yoki Weave kabi **klaster CNI**’si ularni ishlatadi
yoki almashtiradi va reference plugin’larda yetishmaydigan qismni qo’shadi:
*turli node’lardagi* Pod subnet’larini bir-biriga yetadigan qilish
(marshrutlar, VXLAN, BGP, eBPF). Kubernetes o’zi **hech qanday** CNI
bermaydi: `kubeadm init`’dan keyin node’lar siz bittasini o’rnatmaguningizcha
`NotReady` bo’lib turadi va bu ataylab shunday.

## Kubernetes nimaga javobgar emas

- Namespace yaratish: runtime.
- Qaysi IP: IPAM plugin.
- Node’lararo yetib borish: klaster CNI’si.
- **Service’lar**: umuman CNI emas - bu kube-proxy (yoki kube-proxy’ni
  almashtirishni tanlagan Cilium kabi CNI).
- **NetworkPolicy**: CNI, agar u qo’llab-quvvatlasa. Flannel
  qo’llab-quvvatlamaydi.

:::exam-tip
Node darajasida tez topiladigan ikki fakt: `ls /etc/cni/net.d` **qaysi** CNI
sozlanganini aytadi (fayl nomining o’zi aytib turadi); `ls /opt/cni/bin` esa
qaysi plugin binary’lar borligini aytadi. Birinchisi bo’sh bo’lgan node’da
CNI yo’q - Pod’lar `ContainerCreating`’da qotib qoladi va `describe pod`’da
`failed to find plugin` yoki `no networks found` chiqadi. Yechim - bittasini
o’rnatish, odatda CNI manifestini `kubectl apply -f` qilish.
:::

## O’zingizni tekshiring

1. Pod ishga tushganda runtime nima qiladi va CNI plugin nima qiladi?
2. CNI konfiguratsiyasi qaysi katalogda turadi va undagi qaysi fayl
   ishlatiladi?
3. Odamlar CNI’ning ishi deb o’ylaydigan, lekin aslida unday bo’lmagan ikki
   narsani ayting.
