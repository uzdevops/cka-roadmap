## Bitta so’rov, barcha qatlamlar

Brauzer `https://shop.example.com/watch/movies/1`’ni so’raydi. Uni to
konteynergacha va orqaga qaytguncha kuzatib boring, har bir qadamda
komponentni nomlab. Buni yoddan so’zlab bera olsangiz, tarmoq bosqichi
sizniki.

### 1. Klaster tashqarisida

`shop.example.com` uchun DNS (CoreDNS emas, sizning ommaviy DNS’ingiz) kirish
nuqtasining manzilini qaytaradi: cloud yuk muvozanatlagichi, MetalLB IP’si
yoki ortida NodePort turgan node IP’si. TCP ulanishi **Gateway
kontrollerining Service’iga** (yoki Ingress kontrollerinikiga) tushadi.

### 2. Kirish nuqtasi

Service - `type: LoadBalancer` yoki `NodePort`. Qabul qiluvchi node’dagi
**kube-proxy**’da iptables (yoki IPVS/nftables) qoidalari bor: manzil
NodePort 30443 → kontroller Pod’laridan birining IP:443 iga DNAT. Endi
paketning manzili - **Pod IP**.

### 3. Kontroller Pod’igacha

Node uni yo’naltiradi: kontroller Pod’i shu node’da bo’lsa - bridge (`cni0`)
orqali Pod’ning veth’iga; boshqa node’da bo’lsa - **CNI**’ning marshruti yoki
overlay orqali o’sha node’ga, so’ng uning bridge’iga. Kontroller Pod’i ichida
nginx (yoki Envoy) Gateway listener’i / Ingress `tls` ko’rsatgan `shop-tls`
Secret’idagi sertifikat bilan **TLS**’ni tugatadi.

### 4. Yo’naltirish

Kontroller `Host: shop.example.com` va `/watch/movies/1` path’ini o’zining
**HTTPRoute** (yoki Ingress) qoidalariga solishtiradi: `/watch` →
`video-service:8080`, va URLRewrite/rewrite-target path’ni `/movies/1`’ga
aylantiradi. U `video-service:8080`’ga ulanish ochadi.

### 5. Service discovery

`video-service` nomini **CoreDNS** yechadi - kontroller Pod’ining
`/etc/resolv.conf` i `10.96.0.10`’ga ishora qiladi; `kubernetes` plagini
Service’lar kuzatuvidan javob beradi: `video-service.app-space.svc.cluster.local →
10.96.44.3`. (Ko’p kontrollerlar buni o’tkazib yuborib, to’g’ridan-to’g’ri
EndpointSlice’larni kuzatadi va Pod IP’lariga boradi - lekin oddiy klient
nomni yechardi.)

### 6. Yana Service

Kontroller Pod’idan `10.96.44.3:8080`’ga ulanish kontroller node’idagi
**kube-proxy**’ning qoidalariga uriladi: `KUBE-SERVICES` → `KUBE-SVC-*` →
tasodifiy tanlangan bitta `KUBE-SEP-*` → video Pod’iga, `10.244.2.7:8080`’ga
DNAT. Service umuman faqat o’sha qoida sifatida mavjud edi.

### 7. Pod’dan Pod’ga

`10.244.2.7` node02’da. Uni **CNI** olib boradi: `10.244.2.0/24 via
192.168.1.12` marshruti va `eth0` orqali chiqib, yoki `flannel.1` orqali
VXLAN’ga o’ralib. node02’ga yetib keladi, kerak bo’lsa o’ramidan chiqariladi,
`cni0` orqali video Pod’ining veth’iga va uning namespace’iga `eth0`
sifatida kiradi.

### 8. Policy

Yetkazishdan oldin CNI video Pod’ini tanlagan **NetworkPolicy**’larni
tekshiradi: ingress policy’si bo’lsa, 8080 portga faqat ruxsat etilgan
manbalar o’tadi. Kontrollerning Pod’i ruxsat etilgan `from` ichida bo’lishi
shart.

### 9. Ilova

Konteyner jarayoni `:8080`’ni tinglaydi - bu `containerPort`, Service’ning
`targetPort` i unga mos keladi. U `/movies/1`’ni beradi. Agar u Ready
bo’lmaganida, EndpointSlice’ga tushmasdi va 6-qadam uni hech qachon
tanlamasdi.

### 10. Qaytish yo’li

Javob video Pod’idan `10.244.1.x` (kontroller Pod’i) tomon chiqadi; node02
uni CNI orqali qaytaradi; kontroller node’ida **conntrack** manbani un-NAT
qiladi, shuning uchun kontroller uni o’zi so’ragan Service - `10.96.44.3`’dan
kelgandek ko’radi. Kontroller HTTP javobini TLS ulanishiga yozadi; node
chiqishda NodePort DNAT’ini un-NAT qiladi; brauzer o’z sahifasini oladi.

## Xuddi shu manzara, tekshiruv ro’yxati sifatida

| Qatlam | Komponent | Qanday sinadi |
|---|---|---|
| kirish | LB / NodePort / kube-proxy | tashqaridan connection refused / timeout |
| TLS + yo’naltirish | Gateway/Ingress kontrolleri + uning Route/Ingress obyektlari | 404 (qoida yo’q), 503 (endpoint yo’q), TLS xatolari |
| nomlar | CoreDNS | "could not resolve", NXDOMAIN |
| Service’lar | **klient** node’idagi kube-proxy | nom yechiladi, ulanish osilib qoladi, faqat bitta node’da |
| Pod’dan Pod’ga | CNI DaemonSet, node marshrutlari, firewall’dagi CNI porti | node’lararo osiladi, bitta node ichida ishlaydi |
| policy | NetworkPolicy + uni majburlaydigan CNI | faqat muayyan manbalar uchun osiladi |
| ilova | Pod readiness, `targetPort`, jarayonning o’zi | endpoint’lar bo’sh, Pod IP’sida connection refused |

:::exam-tip
Topshiriqda "foydalanuvchilar ilovaga yeta olmayapti" deyilsa, **oxiridan**
boshlab orqaga qarab ishlang: Pod Ready va tinglayaptimi (`kubectl exec ... curl
localhost:8080`)? Service’ning endpoint’lari bormi? Klasterdagi Pod
Service’ga yetadimi? Kontroller unga yetadimi (uning loglari)? Kontrollerga
tashqaridan yetib bo’ladimi? Har bir qadam bitta qatlamni ajratadi va
nosozliklarning ko’pi birinchi ikkitasida bo’ladi.
:::

## O’zingizni tekshiring

1. Bu yo’lda kube-proxy manzilni qaysi ikki joyda qayta yozadi?
2. Paketni kontroller node’idan video Pod’ining node’iga qaysi komponent olib
   boradi va o’sha Pod uni qabul qila olishini qaysi biri hal qiladi?
3. So’rov kontrollerga yetib boradi va 503 qaytaradi. Qaysi qadam ishlamadi
   va birinchi buyruq nima?
