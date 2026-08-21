## Haqiqiy talabni YAML’ga aylantirish

Talab: *`internal` Pod faqat `mysql` bilan 3306 portda va `payroll` bilan
8080 portda gaplasha oladi. Boshqa hech nima ichkariga, boshqa hech nima
tashqariga, DNS’dan tashqari.* Deyarli har bir NetworkPolicy topshirig’i shu
shaklda bo’ladi; uni to’rt qadamda bajaring.

### 1. Policy nima haqida va qaysi yo’nalishlar uchun?

U `name: internal` label’li Pod’larni himoya qiladi. U ularning nima
**yuborishini** (egress) va - "boshqa hech nima ichkariga" - nima
**qabul qilishini** (ingress) cheklaydi. Demak:

```yaml
podSelector:
  matchLabels:
    name: internal
policyTypes:
  - Ingress
  - Egress
```

Hech qanday `ingress:` qoidasi sanalmagani uchun `internal` uchun Ingress
**to’liq taqiqlanadi** - "boshqa hech nima ichkariga" aynan shuni so’ragan
edi. (Agar `internal`’ga, aytaylik, front end 8080 portda yeta olishi kerak
bo’lsa, bu yana bitta `ingress` qoidasi.)

### 2. Mos keladigan label’larni toping

```bash
kubectl get pods --show-labels
# internal   name=internal
# mysql      name=mysql
# payroll    name=payroll
kubectl describe pod mysql | grep -i "labels" -A2
```

Nima bor bo’lsa, shunga mos qo’ying. Policy’lar **Pod** label’lariga mos
keladi - Service’ning nomiga emas, Service’ning label’lariga ham emas. Agar
topshiriqda faqat Service’lar nomlangan bo’lsa, ularning selektorlarini
qarang: `kubectl describe svc mysql | grep Selector`.

### 3. Har bir manzil uchun bittadan egress qoidasi yozing

```yaml
egress:
  - to:
      - podSelector:
          matchLabels:
            name: mysql
    ports:
      - protocol: TCP
        port: 3306
  - to:
      - podSelector:
          matchLabels:
            name: payroll
    ports:
      - protocol: TCP
        port: 8080
```

Har bir `- to:` yozuvi *o’zining* manzillarini *o’zining* portlari bilan
juftlaydi. Ikkala Pod’ni bitta `to:` ichiga ikkala port bilan qo’yish
`mysql:8080` va `payroll:3306`’ga ham ruxsat bergan bo’lardi - bu yerda
zararsiz, lekin prinsipial jihatdan xato, va tekshiruvchi buni sinashi
mumkin.

### 4. DNS, aks holda hech nima ishlamaydi

```yaml
  - ports:
      - protocol: UDP
        port: 53
      - protocol: TCP
        port: 53
```

`ports` bor va **`to:` yo’q** qoida "har qayerga, shu portlarda" degani -
DNS’ga ruxsat berishning eng toza usuli. (Ba’zi tekshiruvchilar qoida
`kube-system` bilan cheklanishini xohlaydi; u holda `to: [{namespaceSelector: {matchLabels:
{kubernetes.io/metadata.name: kube-system}}}]` qo’shing.)

### To’liq holi

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: internal-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      name: internal
  policyTypes:
    - Egress
    - Ingress
  egress:
    - to:
        - podSelector:
            matchLabels:
              name: mysql
      ports:
        - protocol: TCP
          port: 3306
    - to:
        - podSelector:
            matchLabels:
              name: payroll
      ports:
        - protocol: TCP
          port: 8080
    - ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

```bash
kubectl apply -f internal-policy.yaml
kubectl describe netpol internal-policy
kubectl exec internal -- nc -zv -w 2 mysql 3306          # ochiq
kubectl exec internal -- nc -zv -w 2 payroll 8080        # ochiq
kubectl exec internal -- nc -zv -w 2 payroll 80          # kutish vaqti tugaydi - to'g'ri
kubectl exec internal -- nslookup payroll                 # ishlaydi - DNS'ga ruxsat berilgan
```

:::exam-tip
Har safar shu tartibda quring: `podSelector` → `policyTypes` → har bir
(manzil, port) uchun bitta qoida → DNS. Keyin `kubectl describe netpol` va
uni ingliz tilida qaytib o’qing. Baholashgacha yetib boradigan ikki xato:
`podSelector` himoyalanayotgan Pod’niki emas, *manzilning* label’lariga
qo’yilgani va YOKI bilan bog’langan ikki manbani bitta VA’ga aylantirgan
tushib qolgan chiziqcha.
:::

## Uchraydigan variantlar

| Talab | O’zgarish |
|---|---|
| "faqat **`prod` namespace’idagi** `api` Pod’laridan" | `podSelector` va `namespaceSelector` ikkalasi bor bitta `from` elementi (VA) |
| "`monitoring` namespace’idagi har qanday narsadan" | yolg’iz `namespaceSelector`; label’i bo’lmasa, namespace’ga label qo’ying |
| "tashqi IP diapazonidan" | `ipBlock: {cidr: 10.0.0.0/8}` |
| "bu Pod’larga hamma narsani taqiqlash" | ularni tanlang, `policyTypes: [Ingress, Egress]`, qoidalarsiz (nom yechishi kerak bo’lsa, ustiga DNS egress) |
| "web Pod’larga barcha ingress’ga ruxsat" | `ingress: [{}]` |

```bash
kubectl label namespace monitoring team=monitoring
kubectl get ns --show-labels     # har bir namespace da avtomatik kubernetes.io/metadata.name=<name> bor
```

O’sha avtomatik `kubernetes.io/metadata.name` label’i - namespace’ni hech
nimaga label qo’ymasdan nomi bo’yicha tanlashning eng oson yo’li.

## O’zingizni tekshiring

1. Nega har bir egress manzili o’z `ports`i bilan o’z `- to:` yozuvini olishi
   kerak?
2. Har qayerga DNS’ga ruxsat beradigan egress qoidasini yozing.
3. Klasterda policy "hech nima qilmayapti" - CNI haqida birinchi navbatda
   nimani tekshirasiz?
