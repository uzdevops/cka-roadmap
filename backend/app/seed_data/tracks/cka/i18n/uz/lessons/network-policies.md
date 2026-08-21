## Sukut bo’yicha holat - "hamma hamma bilan gaplashadi"

Kubernetes tarmoq modeli har bir Pod har qanday namespace’dagi har qanday
boshqa Pod’ga NAT’siz yeta olishini kafolatlaydi. Qulay, va oylik
ma’lumotlar bazasi bilan marketing front end’i orasida aynan siz
istamaydigan narsa. **NetworkPolicy** - "faqat bular ular bilan gaplasha
oladi" deyish usuli.

YAML’dan oldin ikki narsa:

1. NetworkPolicy label’lar orqali Service’larni yoki node’larni emas,
   **Pod’larni tanlaydi**.
2. U faqat **CNI plagini** qo’llab-quvvatlasa majburlanadi. Calico, Cilium,
   Weave: ha. Flannel: **yo’q** - policy’lar API tomonidan qabul qilinadi va
   jimgina hech nima qilmaydi. Flannel klasterida "nega NetworkPolicy’m
   ishlamayapti" savolining javobi - "u ishlay olmaydi".

## Tanlash va yo’nalish qanday ishlaydi

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-policy
  namespace: prod
spec:
  podSelector:                  # bu policy QAYSI Pod'larni himoya qiladi (shu namespace da)
    matchLabels:
      role: db
  policyTypes:
    - Ingress                   # bu policy KIRUVCHI trafik haqida gapiradi
    - Egress                    # ... va CHIQUVCHI haqida
  ingress:
    - from:
        - podSelector:          # SHU namespace dagi role=api Pod'lar
            matchLabels:
              role: api
      ports:
        - protocol: TCP
          port: 3306
  egress:
    - to:
        - podSelector:
            matchLabels:
              role: backup
      ports:
        - protocol: TCP
          port: 80
```

Policy’larning xatti-harakatini belgilaydigan qoida: **biror policy Pod’ni
bir yo’nalish uchun tanlashi bilanoq, o’sha Pod uchun o’sha yo’nalish sukut
bo’yicha taqiqlanadi va uni faqat sanab o’tilgan qoidalar ochadi.**
Policy’dan oldin `role: db` Pod’lari hamma narsani qabul qilardi; undan keyin
esa faqat `role: api`’dan TCP 3306 ni qabul qiladi va faqat `role: backup`’ga
80 portda yubora oladi. Hech bir policy tanlamagan Pod’lar tegilmagan
qoladi - hamon to’la ochiq.

Yo’nalishni hisobga oladigan narsa - `policyTypes`. `policyTypes:
[Ingress]` va `egress:` bloki bor policy egress blokini e’tiborsiz qoldiradi;
`policyTypes: [Ingress, Egress]` bor va hech qanday `egress:` qoidasi yo’q
policy **barcha** egress’ni rad etadi. `policyTypes`’ni tushirib
qoldirsangiz, u sukut bo’yicha Ingress bo’ladi, agar `egress` bloki mavjud
bo’lsa, ustiga Egress ham.

:::warning
Policy’lar **qo’shiluvchi** (faqat ruxsat beruvchi). Taqiqlash qoidasi yo’q.
Bitta Pod’ni tanlagan ikki policy birlashtiriladi: ikkovidan biri ruxsat
bergan narsa ruxsat etilgan. Taqiqlash uchun siz Pod’ni tanlaysiz va o’sha
narsaga shunchaki ruxsat bermaysiz.
:::

## Javoblar bilan muammo yo’q

Policy’lar yangi ulanishlar haqida. Agar `db`’ga 3306 portda `api`’dan
ingress ruxsat etilgan bo’lsa, javoblar `db`’da egress qoidasisiz qaytib
oqadi - CNI ulanishni kuzatib turadi. Egress qoidasi faqat `db` ulanishni
*o’zi boshlaganda* kerak bo’ladi.

## `from` / `to` ichidagi uchta selektor

| Selektor | Nimaga mos keladi |
|---|---|
| `podSelector` | policy’ning o’z namespace’idagi Pod’lar, label bo’yicha |
| `namespaceSelector` | shu label’larga ega namespace’lardagi har bir Pod |
| `ipBlock` | CIDR (ixtiyoriy `except` bilan), klaster tashqarisidagi narsalar uchun |

```yaml
ingress:
  - from:
      - podSelector:
          matchLabels: {role: api}
        namespaceSelector:              # O'SHA ro'yxat elementi, chiziqchasiz: VA - prod namespace laridagi api Pod'lar
          matchLabels: {env: prod}
      - ipBlock:                        # YANGI ro'yxat elementi, chiziqcha bilan: YOKI - yoki shu CIDR
          cidr: 192.168.5.10/32
```

O’sha chiziqcha - butun imtihon savoli: **bitta** `from` yozuvidagi ikki
selektor VA bilan bog’lanadi; ikkita `from` yozuvi esa YOKI bilan.

## Keng tarqalgan shakllar

```yaml
# namespace da barcha ingress ni sukut bo'yicha taqiqlash
spec:
  podSelector: {}
  policyTypes: [Ingress]
---
# barcha egress ni sukut bo'yicha taqiqlash (DNS'ni unutmang!)
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector: {}      # har qanday namespace
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
---
# hamma narsani kiritishga ruxsat (ba'zi Pod'lar uchun taqiqni bekor qilish)
spec:
  podSelector:
    matchLabels: {role: public}
  ingress:
    - {}
```

`podSelector: {}` namespace’dagi har bir Pod’ni tanlaydi; bo’sh `- {}`
qoidasi esa har qayerdan ruxsat beradi.

:::exam-tip
Egress policy’lar birinchi navbatda DNS’ni sindiradi. `policyTypes: [Egress]`
deb yozgan zahotingiz Pod nomlarni yecha olmaydi - siz sanaganlaringizdan
hech biri 53 portga ruxsat bermagan. Topshiriqda boshqacha aytilmagan bo’lsa,
yuqoridagi DNS egress qoidasini har bir egress policy’ga qo’shing.
:::

## Tekshirish

```bash
kubectl get netpol -n prod
kubectl describe netpol db-policy -n prod          # o'qishga qulay "Allowing ingress traffic: ... From: ..."
kubectl exec api-pod -- nc -zv db 3306             # ulanishi kerak
kubectl exec other-pod -- nc -zv db 3306           # kutish vaqti tugashi kerak
```

`describe` - aql-idrok tekshiruvi: u policy’ni CNI o’qigan tarzda chiqaradi
va selektorlaringizning VA/YOKI mantiqi ravshan bo’ladi.

## O’zingizni tekshiring

1. `role: db`’ni tanlaydigan va faqat ingress qoidasi bor policy
   yaratganingizdan keyin db ning chiquvchi ulanishlariga nima bo’ladi?
2. "env=prod label’li namespace’lardagi api Pod’lar" uchun - VA sifatida -
   `from` blokini yozing, va "api Pod’lar YOKI env=prod namespace’laridagi
   har qanday narsa" uchun ham.
3. Egress policy’ingiz IP’lar uchun ishlaydi, nomlar uchun sinadi. Nimani
   unutdingiz?
