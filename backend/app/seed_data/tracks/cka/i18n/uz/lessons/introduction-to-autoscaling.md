## Ikkita o’q, ikkita daraja

Kubernetesda "autoscaling" to’rt xil narsani anglatadi va bu haqdagi har
qanday suhbat shu to’rttasi ajratilmaguncha chalkash bo’lib qoladi.

```
                    │  scale OUT/IN (ko’proq nusxa)      │  scale UP/DOWN (kattaroq nusxa)
────────────────────┼────────────────────────────────────┼────────────────────────────────
 workload (Pod’lar) │  Horizontal Pod Autoscaler (HPA)   │  Vertical Pod Autoscaler (VPA)
 klaster (node’lar) │  Cluster Autoscaler / Karpenter    │  (instance turini o’zgartirish)
```

- **Gorizontal** - replika qo’shish yoki olib tashlash. Ilova shuncha nusxada
  ishlashga chidashi kerak (stateless, yoki ehtiyotkorlik bilan stateful).
- **Vertikal** - o’sha replikaga ko’proq yoki kamroq CPU va memory berish.
  Ilovaga o’zgarish yo’q, lekin Pod qayta ishga tushirilishi kerak - klaster
  in-place resize’ni qo’llab-quvvatlamasa.
- **Workload darajasi** - Kubernetes obyektlari Kubernetes obyektlarini
  sozlaydi.
- **Klaster darajasi** - Pod’lar joylashtirilmay qolganda (yoki node’lar bo’sh
  turganda) kontroller cloud bilan gaplashib node qo’shadi yoki olib
  tashlaydi. Borligini bilishdan boshqasi CKA doirasidan tashqarida.

## Qo’lda masshtablash - boshlang’ich nuqta

Avtomatik narsalarning hammasi - siz qo’lda qila oladigan ishni bajaradigan
kontroller:

```bash
kubectl scale deployment web --replicas=5                         # gorizontal, qo'lda
kubectl set resources deployment web --requests=cpu=500m,memory=512Mi   # vertikal, qo'lda (Pod'larni rollout qiladi)
```

HPA siz uchun `spec.replicas`’ni yozadi; VPA siz uchun resurs request’larini
yozadi. Shu ikki buyruqni tushunsangiz, kontrollerlarga nimaga tegishga
ruxsat berilganini tushunasiz.

## Ishlashi uchun ularga nima kerak

| Autoscaler | Nima kerak |
|---|---|
| HPA | **Metrics Server** (yoki custom/external metrics adapter) va Pod’larda **resurs request’lari** - foizli maqsad "request’ning foizi" degani |
| VPA | o’rnatilgan VPA komponentlari (u ichida kelmaydi) va Auto rejimi uchun Pod qayta ishga tushishiga chidam |
| Cluster Autoscaler | cloud provider va u o’lchamini o’zgartira oladigan node group’lar |

:::exam-tip
Imtihon to’g’ridan-to’g’ri HPA’ni tekshiradi - `kubectl autoscale` va
`autoscaling/v2` manifesti - va muammo aynan uning ikkita sharti ichida
yashiringan: `<unknown>/50%` ko’rsatayotgan HPA metrika yo’qligini bildiradi
(Metrics Server yo’q yoki Pod’larda CPU request’lari yo’q). VPA va in-place
resize - o’quv dasturining yangiroq bandlari; tushunchalarni va obyektlarni
biling.
:::

## Tanlash

- Trafikka bog’liq, stateless, ko’p kichik replika bitta kattasidan arzon
  → **HPA**.
- To’g’ri o’lchamini bilmaydigan bitta replikali xizmat yoki ortiqcha ham,
  kam ham resurs berilgan batch workload → **VPA**, yoki hech bo’lmaganda
  faqat tavsiya beruvchi rejimdagi VPA.
- Bitta Deployment’da bir xil metrika (CPU) uchun ikkalasi ham → **yo’q**:
  ular bir-biri bilan urishadi. CPU’da HPA va memory’da VPA, yoki faqat
  tavsiya olish uchun `Off` rejimidagi VPA - ishlaydigan kombinatsiyalar
  shular.
- Joy yetmagani uchun Pod’lar Pending → **Cluster Autoscaler**; HPA faqat
  replika so’ray oladi, node yarata olmaydi.

## Oldindagi hafta

1. Kontrollerlar nimani avtomatlashtirishini his qilish uchun qo’lda
   masshtablash laboratoriyasi.
2. HPA: obyektning o’zi, algoritm, `kubectl autoscale` va uning yukka
   javobini kuzatish.
3. In-place Pod resize: konteyner resurslarini qayta ishga tushirmasdan
   o’zgartirish.
4. VPA: komponentlar, yangilash rejimlari va uni qachon afzal ko’rish.

## O’zingizni tekshiring

1. Bularning har birini gridning to’g’ri katagiga joylashtiring: HPA, VPA,
   Cluster Autoscaler.
2. HPA joriy CPU sifatida `<unknown>` ko’rsatyapti. Ikkita odatiy sababni
   ayting.
3. Nega bitta Deployment’ning CPU’siga HPA va VPA ikkalasi birga ta’sir
   qilmasligi kerak?
