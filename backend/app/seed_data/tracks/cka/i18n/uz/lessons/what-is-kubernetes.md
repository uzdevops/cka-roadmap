## Orkestratsiya nega paydo bo’ldi

Konteynerlar paketlash muammosini hal qildi. Konteyner image’i ilovangizni
uning bog’liqliklari bilan birga o’raydi, shuning uchun u noutbukda, CI’da va
productionda bir xil ishlaydi. Konteynerlar hal qilmagan narsa - `docker run`
dan **keyin** sodir bo’ladigan hamma narsa:

- Node soat 03:00 da o’ladi. Unda ishlayotgan o’n ikkita konteynerni kim qayta
  ishga tushiradi?
- Trafik uch barobar oshdi. Kim ko’proq replika ishga tushiradi va yuk
  muvozanatlagichga kim xabar beradi?
- Siz yangi image chiqardingiz. So’rovlarni yo’qotmasdan eski konteynerlarni
  kim almashtiradi?
- Ikki xizmat bir-birini topishi kerak. Manzillarni kim beradi?

Buni qo’lda qilish - odamlar navbati. Shell skriptlar bilan qilish - odamlar
navbati va ustiga pager. Kubernetes - butun soha kelgan javob: klasterni siz
e’lon qilgan holatga uzluksiz olib boradigan boshqaruv tsikli.

## Deklarativ, imperativ emas

Bu Kubernetesdagi boshqa hamma narsa osilib turgan yagona g’oya.

**Imperativ** tizim buyruq oladi: *bu konteynerning uchta nusxasini ishga
tushir*. Agar biri o’lsa, hech narsa bo’lmaydi, chunki buyruq allaqachon
bajarilgan.

**Deklarativ** tizim esa kutilgan natija tavsifini oladi: *bu konteynerning
uchta nusxasi bo’lishi kerak*. Kubernetes bu tavsifni saqlaydi va keyin
abadiy - haqiqatni unga moslashtirish ustida ishlaydi.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3          # <- kutilgan holat
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: nginx:1.27
          ports:
            - containerPort: 80
```

Siz shu hujjatni yuborasiz. Shundan keyin Pod o’chirilsa, node bo’shatilsa yoki
konteyner tugasa, kontroller bo’shliqni sezadi va uni yopadi. Siz hech qayerda
"qayta ishga tushir" deb yozmadingiz.

:::tip
Imtihonda savolda qotib qolsangiz, uni qayta o’qing va "kutilgan holat nima?"
deb so’rang. Javob deyarli har doim kichik YAML o’zgarishi va `kubectl apply`,
qo’lda bajariladigan qadamlar ketma-ketligi emas.
:::

## Moslashtirish tsikli

Kubernetesdagi har bir kontroller bir xil tsiklni bajaradi:

1. API server orqali joriy holatni **kuzatadi**.
2. Uni etcd’da saqlangan kutilgan holat bilan **solishtiradi**.
3. Farqni yopish uchun **harakat qiladi**.
4. Abadiy takrorlaydi.

```text
        kutilgan holat (spec)
                |
                v
   +------------------------+
   |       kontroller       |
   | kuzat -> solishtir -> harakat |
   +------------------------+
                |
                v
        joriy holat (status)
```

Shuning uchun har bir Kubernetes obyektining ikki yarmi bor: siz yozadigan
`spec` va tizim yozadigan `status`. `status`ni o’qishga o’rganish - klasterni
tekshira oladiganlarni faqat narsa yarata oladiganlardan ajratadigan narsa.

```bash
# spec - siz so'raganingiz; status - aslida sodir bo'lgani
kubectl get pod web-5d4f8b6c9-abcde -o yaml | less
```

## Kubernetes nima beradi

| Imkoniyat | Amalda nimani anglatadi |
| --- | --- |
| O’z-o’zini tiklash | Ishdan chiqqan konteynerlar qayta ishga tushadi; o’lgan node’dagi Pod’lar qayta rejalashtiriladi |
| Gorizontal masshtablash | Replika soni bitta raqamni tahrirlash bilan yoki avtomatik o’zgaradi |
| Service discovery | O’zgarib turuvchi Pod’lar oldida barqaror DNS nomlari va virtual IP’lar |
| Rollout va rollback | Avtomatik versiya tarixi bilan bosqichma-bosqich almashtirish |
| Konfiguratsiya boshqaruvi | Image’ni qayta qurmasdan ConfigMap va Secret kiritish |
| Saqlash orkestratsiyasi | Volume’lar talab bo’yicha ta’minlanadi va ulanadi |
| Bin packing | Scheduler Pod’larni so’ralgan resurslar asosida joylashtiradi |

## Kubernetes nima **emas**

Imtihon chegaralarni bilishingizni ham kutadi.

- **PaaS emas.** U kodingizni qurmaydi, CI’ni ishga tushirmaydi va `git push`
  bilan deploy bermaydi. Bular Kubernetes **ustiga** qurilgan qatlamlar.
- **Service mesh emas.** Qayta urinishlar, xizmatlararo mTLS va nozik trafik
  taqsimoti Istio yoki Linkerd kabi loyihalardan keladi.
- **Monitoring tizimi emas.** U metrikalar va hodisalarni beradi; Prometheus va
  shu kabilar ularni yig’adi va ogohlantiradi.
- **Ma’lumotlar bazasi yoki navbat emas.** U bularni *ishga tushira* oladi,
  lekin ilova darajasida bardoshlilik kafolatini bermaydi.
- **Qayta ishga tushirishga chidamsiz ilovalar uchun sehr emas.** Agar
  ilovangiz qayta ishga tushirilishga yoki ko’chirilishga chiday olmasa,
  Kubernetes vaziyatni yaxshilamaydi, yomonlashtiradi.

:::warning
Juda keng tarqalgan noto’g’ri tushuncha: Kubernetes o’zi nol uzilishni
kafolatlamaydi. Rolling update + to’g’ri sozlangan readiness probe +
PodDisruptionBudget sizni shunga olib boradi. Bulardan biri yetishmasa,
yangilash paytida so’rovlarni yo’qotasiz.
:::

## CKA qayerda turadi

Certified Kubernetes Administrator imtihoni amaliy: jonli klaster, terminal va
taxminan ikki soat vazifalar. Hech kim sizdan "orkestratsiya" ta’rifini
so’ramaydi. Sizdan narsalarni *bajarish* so’raladi, quyidagi og’irliklar bilan:

- Nosozliklarni bartaraf etish - 30%
- Klaster arxitekturasi, o’rnatish va sozlash - 25%
- Service’lar va tarmoq - 20%
- Workload’lar va rejalashtirish - 15%
- Saqlash - 10%

:::exam-tip
E’tibor bering: nosozliklarni bartaraf etish va klaster administratsiyasi
imtihonning yarmidan ko’pini tashkil qiladi. Deployment’ni tez yarata olish -
minimal talab; aslida imtihondan o’tkazadigan narsa - u **nega** oldinga
siljimayotganini aniqlay olish. Bu yo’l xaritasidagi har bir dars faqat
muvaffaqiyatli stsenariy bilan emas, nosozlik holatlari bilan tugaydi.
:::

## O’zingizni tekshiring

Davom etishdan oldin bularga konspektsiz javob bera olishingiz kerak:

1. Kubernetes obyektidagi `spec` va `status` orasidagi farq nima?
2. Nega Deployment’ga tegishli Pod’ni o’chirish replika sonini kamaytirmaydi?
3. Odamlar Kubernetes qiladi deb o’ylaydigan, lekin u ataylab qilmaydigan uchta
   narsani ayting.
