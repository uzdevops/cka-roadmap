## Nega har bir strelka shifrlangan

Kubernetes - bu turli mashinalardagi jarayonlar to’plami bo’lib, ular
bir-biriga ko’rsatma yuboradi: "bu Pod’ni ishga tushir", "mana bu Secret",
"o’sha namespace’ni o’chir". TLS bo’lmasa, tarmoqdagi istalgan mashina bu
ko’rsatmalarni o’qiy olardi yoki - bundan ham yomoni - o’zinikini yubora
olardi. Shuning uchun komponentlar orasidagi har bir ulanish TLS va ikkala
tomon ham sertifikatlar bilan kimligini isbotlaydi.

```
kubectl ──TLS──▶ kube-apiserver ──TLS──▶ etcd
                    ▲    │
        TLS ────────┘    └──TLS──▶ kubelet
   (scheduler, controller-manager, kubelet'lar)
```

TLS har bir strelkaga ikki narsa beradi:

1. **Shifrlash** - o’rtadagi hech kim uni o’qiy olmaydi.
2. **Shaxs** - har bir tomon ikkinchisi kimligini biladi, chunki u
   ko’rsatgan sertifikatni ikkalasi ham ishonadigan CA imzolagan.

Kubernetes xavfsizligini ishlatadigan narsa - aynan ikkinchisi: API server
kubelet’ning trafigini shunchaki *shifrlab* qolmaydi, u bu node01’ning
kubelet’i ekanini *biladi*, chunki node01’ning sertifikatida
`CN=system:node:node01` yozilgan va uni klaster CA’si imzolagan.

## Bu bosqich nimaga olib boradi

| Dars | Nimaga javob beradi |
|---|---|
| TLS asoslari | kalit, sertifikat, CA va handshake nima - noldan |
| Kubernetes’da TLS | klasterda qaysi sertifikatlar bor va ularni kim imzolagan |
| Sertifikat yaratish | openssl bilan CA, server sertifikati va client sertifikatini qanday qilish |
| Sertifikat tafsilotlarini ko’rish | istalgan sertifikatni o’qish va klasterning butun to’plamini tekshirish |
| Certificates API | sertifikatni klaster *orqali*, tasdiqlash bilan qanday berish |

Amaliy foyda ikkita imtihon topshirig’ida ko’rinadi: **"bir komponent
ikkinchisiga yeta olmayapti, tuzating"** (deyarli har doim sertifikat yo’li
yoki muddati o’tgan sertifikat) va **"X foydalanuvchisi uchun hisob
ma’lumotlarini yarating"** (klaster CA’si tasdiqlab imzolagan CSR).

## Doim eshitadigan uchta so’z

- **Server sertifikati** - *server* o’zi client yetmoqchi bo’lgan tomon
  ekanini isbotlash uchun ko’rsatadigan narsa. API serverda bittasi bor
  (CN=kube-apiserver, u javob beradigan har bir nom va IP bilan); etcd’da
  bittasi bor; har bir kubelet’da ham bittasi bor.
- **Client sertifikati** - *client* o’zi kimligini isbotlash uchun
  ko’rsatadigan narsa. Admin kubeconfig’ida bittasi bor; API serverda etcd
  bilan gaplashish uchun bittasi va kubelet’lar bilan gaplashish uchun
  yana bittasi bor; har bir kubelet’da API server bilan gaplashish uchun
  bittasi bor.
- **CA (certificate authority)** - qolganlarini imzolaydigan kalitlar juftligi.
  Sertifikat siz ishonadigan CA imzolagan bo’lsa, unga ishoniladi. kubeadm
  klaster CA’si (`ca.crt`/`ca.key`), etcd CA’si va front-proxy CA’sini
  yaratadi.

Keyingi dars to’liq tushuntiradigan narsaning ko’p qismi shu; agar bu uchta
ta’rif sizga hozirdan tushunarli bo’lsa, siz oldindasiz.

:::tip
kubeadm control plane’da hamma narsa `/etc/kubernetes/pki` ichida yashaydi.
Hozir o’sha katalogni bir marta `ls` qiling va nomlarga qarang -
`apiserver.crt`, `apiserver-kubelet-client.crt`, `etcd/server.crt`, `ca.crt` -
keyingi darslar esa siz allaqachon ko’rgan jadvalni to’ldirib boradi.
:::

## O’zingizni tekshiring

1. TLS ikki komponent orasidagi ulanishga qanday ikki kafolat beradi?
2. Server sertifikati bilan client sertifikati orasidagi farq nima?
3. kubeadm klasterining sertifikatlari qayerda saqlanadi?
