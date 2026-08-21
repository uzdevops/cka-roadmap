## Hech qanday interfeysda bo’lmagan manzil

Pod’lar haqiqiy IP’ga ega haqiqiy interfeys oladi. Service’ning ClusterIP’i
boshqacha: u faqat qoidalar sifatida mavjud. Har bir node’da **kube-proxy**
Service va EndpointSlice’larni kuzatadi hamda shunday qoidalar yozadi: "shu
IP:portga ketayotgan paket → manzilini mana bu Pod IP:portlaridan biriga
qayta yoz". ClusterIP’ni hech qanday jarayon tinglamaydi; unga qilingan
`ping` hech qayerga bormaydi.

```
Pod A ── 10.96.12.7:80 ──┐
                          ├── iptables on the node: DNAT to 10.244.2.5:8080 (or .6, or .7)
                          └── the packet leaves with a Pod destination; the CNI carries it
```

## Yana uchta oraliq

| Oraliq | Sukut bo’yicha | Egasi |
|---|---|---|
| Pod CIDR | `10.244.0.0/16` (Flannel an’anasi) | CNI + controller manager |
| Service CIDR | `10.96.0.0/12` | API server’dagi `--service-cluster-ip-range` |
| node portlari | `30000-32767` | API server’dagi `--service-node-port-range` |

Ular bir-biri bilan kesishmasligi kerak va Service oralig’i butunlay virtual.

```bash
ps -ef | grep kube-apiserver | grep -o -- '--service-cluster-ip-range=[^ ]*'
kubectl get svc -A          # har bir ClusterIP shu oraliq ichida
```

## kube-proxy nima yozadi

```bash
kubectl get svc db -o wide
# NAME   TYPE        CLUSTER-IP     PORT(S)    SELECTOR
# db     ClusterIP   10.96.12.7     3306/TCP   app=db
kubectl get endpointslices -l kubernetes.io/service-name=db
# ... ENDPOINTS 10.244.2.5,10.244.1.9
```

Istalgan node’da, iptables rejimida:

```bash
iptables -t nat -L KUBE-SERVICES -n | grep 10.96.12.7
#  KUBE-SVC-XYZ  tcp  --  0.0.0.0/0  10.96.12.7  /* default/db cluster IP */ tcp dpt:3306
iptables -t nat -L KUBE-SVC-XYZ -n
#  KUBE-SEP-AAA  ... statistic mode random probability 0.5   <- yarmida 1-endpoint tanlanadi
#  KUBE-SEP-BBB  ...                                          <- aks holda 2-endpoint
iptables -t nat -L KUBE-SEP-AAA -n
#  DNAT  ... to:10.244.2.5:3306
```

`KUBE-SERVICES` → har bir Service uchun bitta `KUBE-SVC-*` zanjiri → har bir
endpoint uchun DNAT bajaradigan bitta `KUBE-SEP-*` zanjiri. Teng ehtimollik
bilan tasodifiy tanlash - bu yuk taqsimlash. NodePort node portiga mos
keladigan va o’sha `KUBE-SVC-*` zanjiriga o’tadigan `KUBE-NODEPORTS` yozuvini
qo’shadi; butun farq shundan iborat.

**IPVS** rejimida xuddi shu ma’lumot yadro darajasidagi virtual server
jadvali bo’ladi (`ipvsadm -Ln`) - katta miqyosda yaxshiroq, algoritmlari
ko’proq (round-robin, least connections), g’oyasi esa o’sha. **nftables**
rejimida (yangiroq sukut bo’yicha rejim) qoidalar nft set va map’laridan
iborat bo’ladi.

```bash
kubectl logs -n kube-system -l k8s-app=kube-proxy | grep -i "proxy mode"
kubectl get cm kube-proxy -n kube-system -o yaml | grep -A1 "mode:"
```

## Paketni kuzatib borish

1. Pod A (10.244.1.2) `db:3306` ga ulanadi; CoreDNS `db` = 10.96.12.7 deydi.
2. Paket A’ning namespace’idan node’ning bridge’iga 10.96.12.7 manzili bilan
   chiqadi.
3. Node’da `nat` PREROUTING hook’i `KUBE-SERVICES` ni ishga tushiradi; manzil
   10.244.2.5:3306 ga qayta yoziladi.
4. Node 10.244.2.5 ni boshqa har qanday Pod paketi kabi node02 tomon
   yo’naltiradi (marshrutlar yoki overlay - bu CNI ishi).
5. 10.244.2.5 dan kelgan javob qaytish yo’lida conntrack tomonidan un-NAT
   qilinadi, shuning uchun A uni 10.96.12.7 dan kelgandek ko’radi.

Service mavjud bo’lgan yagona joy - 3-qadam. Agar **A turgan node**’dagi
kube-proxy buzilgan bo’lsa, A hech qanday Service’ga yeta olmaydi - boshqa
node’dagi Pod B esa yeta oladi. Ana shu assimetriya - diagnostikaning kaliti.

## Service’lar nega buziladi

| Alomat | Nimaga qaraysiz |
|---|---|
| DNS aniqlaydi, ulanish **har bir** node’dan qotib qoladi | endpoint’lar bo’sh (selector/readiness) → `kubectl get endpoints` |
| faqat **bitta** node’dan qotib qoladi | o’sha node’dagi kube-proxy Pod’i: `kubectl get pods -n kube-system -o wide -l k8s-app=kube-proxy` va uning loglari |
| ClusterIP orqali ishlaydi, NodePort orqali yo’q | node portidagi firewall; o’sha node’da Pod yo’q holda `externalTrafficPolicy: Local` |
| ishlagan, kube-proxy o’zgarishidan keyin to’xtagan | DaemonSet’da noto’g’ri `--config` yo’li yoki ConfigMap - loglarda `open ...: no such file` |
| bir xil node’dagi Pod Service’ga yeta olmaydi | `net.bridge.bridge-nf-call-iptables` 0 ga teng |

:::exam-tip
Node’da `iptables -t nat -L KUBE-SERVICES -n | grep <clusterIP>` bitta qatorda
kube-proxy o’sha yerda Service’ni dasturlagan yoki dasturlamaganini
isbotlaydi. Qator yo’q = kube-proxy o’sha node’da o’z ishini bajarmayapti;
qator bor = Service mavjud va muammo endpoint’larda yoki undan keyingi CNI
yo’lida.
:::

## O’zingizni tekshiring

1. ClusterIP qayerda "mavjud" va uni o’sha yerga qaysi komponent qo’yadi?
2. iptables rejimida kube-proxy bitta Service uchun yaratadigan uch zanjirli
   tuzilmani tasvirlab bering.
3. node02’dagi Pod’lar hech qanday Service’ga yeta olmaydi; node01’dagilar
   yeta oladi. Qaysi komponent, qayerda?
