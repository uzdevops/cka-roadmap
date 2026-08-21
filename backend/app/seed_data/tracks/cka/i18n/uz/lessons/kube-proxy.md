## kube-proxy hal qiladigan muammo

Pod’larning IP’lari bor, lekin Pod’lar doim almashib turadi. Service Pod’lar
to’plamiga bitta barqaror virtual IP - **ClusterIP** - va nom beradi. Gap
shundaki, bu ClusterIP hech qayerda, hech qanday interfeysga biriktirilmagan.
Uni hech qanday jarayon tinglamaydi. U faqat har bir node’dagi qoida sifatida
mavjud: "shu IP’ga ketayotgan trafikni mana bu Pod IP’laridan biriga qayta
yoz".

kube-proxy - o’sha qoidalarni yozadigan va ularni saqlab turadigan komponent.
U **har bir node**’da DaemonSet sifatida ishlaydi, API server orqali Service
va EndpointSlice’larni kuzatadi va node’ning paket filtrini shunga mos
ravishda dasturlaydi.

```
Pod A ──▶ 10.96.0.10:80 (ClusterIP) ──iptables/IPVS on this node──▶ 10.244.1.5:8080 (a Pod behind the Service)
```

## Rejimlar

| Rejim | Qanday | Izohlar |
|---|---|---|
| **iptables** | har bir Service uchun bitta qoidalar zanjiri; endpoint’lar orasidan tasodifiy tanlash | sukut bo’yicha; bir necha ming Service’gacha yetarli |
| **IPVS** | hash jadvallari bilan yadro darajasidagi virtual server | yaxshiroq masshtablanadi, yuk taqsimlash algoritmlari ko’proq; `ip_vs` modullari kerak |
| nftables | iptables qoidalarining yangiroq o’rinbosari | so’nggi relizlarda sukut bo’yicha bo’lib bormoqda |
| userspace | eski, sekin, yo’qolgan | tarixiy |

```bash
kubectl logs -n kube-system -l k8s-app=kube-proxy | grep -i "proxy mode"
# Using iptables Proxier / Using ipvs Proxier
```

Rejim kube-proxy’ning ConfigMap’ida turadi:

```bash
kubectl get cm kube-proxy -n kube-system -o yaml | grep mode
```

## Qoidalarni ko’rish

```bash
# bitta Service uchun zanjir, iptables rejimi
iptables -t nat -L KUBE-SERVICES -n | grep <cluster-ip>
iptables -t nat -L KUBE-SVC-XXXX -n         # Service zanjiri: har bir endpoint uchun bitta o'tish, ehtimollik bilan
iptables -t nat -L KUBE-SEP-XXXX -n         # bitta endpoint: Pod IP'siga DNAT

# IPVS rejimi
ipvsadm -Ln
```

Zanjir nomlarini yodlash shart emas; bilish kerak bo’lgan narsa shu: Service
"ishlamayotganda" va endpoint’lar to’g’ri ko’rinayotganda, keyingi savol -
klient Pod ishlayotgan node’da bu qoidalar bormi yoki yo’qmi.

## U qanday ishlaydi va qanday buziladi

```bash
kubectl get ds -n kube-system kube-proxy
kubectl get pods -n kube-system -l k8s-app=kube-proxy -o wide   # har bir node'da bitta, hammasi Running'mi?
kubectl describe ds -n kube-system kube-proxy | grep -A3 "Args\|Mounts"
```

Buzilgan kube-proxy alomatlari:

- Pod’lar bir-biriga **IP orqali** yeta oladi, lekin **Service IP** orqali
  yeta olmaydi;
- `nslookup` Service nomini muammosiz aniqlaydi (DNS - bu CoreDNS, kube-proxy
  emas), lekin unga ulanish qotib qoladi;
- faqat bitta node’dagi Pod’lar zarar ko’radi (kube-proxy har bir node uchun
  alohida).

Imtihon uslubidagi nosozliklar: DaemonSet konteyneri ConfigMap mount’iga mos
kelmaydigan config fayl yo’liga murojaat qiladi
(`--config=/var/lib/kube-proxy/...`) yoki ConfigMap nomi o’zgartirilgan.
kube-proxy Pod’idagi `kubectl logs` yetishmayotgan faylni nomi bilan aytadi.

:::exam-tip
Service muammolari aniq ikkiga bo’linadi: **nom aniqlanmasa** → CoreDNS.
**Aniqlanadi, lekin ulanib bo’lmasa** → avval endpoint’lar (selector/portlar),
keyin klient node’idagi kube-proxy. Bu ikkisini ajratib olsangiz, qidiruvni
ikki barobar qisqartirasiz.
:::

## kube-proxy nima emas

U Pod’dan Pod’ga ketadigan trafikning data path’ida turmaydi - buni CNI
plugin bajaradi. U DNS bilan shug’ullanmaydi. Va u Ingress kontrolleri ham
emas - kube-proxy Service’larda to’xtaydi; Ingress esa uning ustidagi boshqa
qatlam.

:::note
Ba’zi CNI plugin’lar (masalan, Cilium) kube-proxy’ni butunlay o’zining eBPF
implementatsiyasi bilan almashtira oladi. Bunday klasterda kube-proxy
DaemonSet’i bo’lmaydi va bu normal - uni "tuzatish"dan oldin tekshiring.
:::

## O’zingizni tekshiring

1. ClusterIP qayerda "yashaydi" va unga ketayotgan paketlarni kim biror joyga
   yetkazadi?
2. Pod boshqa Pod’ning IP’siga `curl` qila oladi, lekin uning oldidagi
   Service’ga qila olmaydi, DNS esa to’g’ri aniqlaydi. Qaysi node’dagi qaysi
   komponentni tekshirasiz?
3. kube-proxy iptables yoki IPVS rejimida ishlayotganini qanday aniqlaysiz?
