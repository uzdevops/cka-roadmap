## Terminalingizda allaqachon turgan hujjatlar

Siz har bir kind’ning har bir maydonini eslab qolmaysiz, buning hojati ham
yo’q. API server o’zining to’liq sxemasini e’lon qiladi va `kubectl explain`
uni sizga o’qib beradi - turlari, tavsiflari va qaysi maydonlar majburiy
ekani bilan.

```bash
kubectl explain pod
kubectl explain pod.spec
kubectl explain pod.spec.containers
kubectl explain pod.spec.containers.livenessProbe
kubectl explain deployment.spec.strategy.rollingUpdate
```

```
KIND:       Pod
VERSION:    v1

FIELD: livenessProbe <Probe>

DESCRIPTION:
    Periodic probe of container liveness. Container will be restarted if the
    probe fails. ...

FIELDS:
  exec          <ExecAction>
  failureThreshold      <integer>
  httpGet       <HTTPGetAction>
  initialDelaySeconds   <integer>
  periodSeconds <integer>
  ...
```

Har bir qator - maydon nomi, uning turi va - pastga aylantirsangiz - u nima
qilishi haqidagi xatboshi. Ichma-ich turlar bir daraja pastga tushib
tushuntiriladi.

## Ahamiyatga ega ikki bayroq

```bash
kubectl explain pod.spec.affinity --recursive      # butun quyi daraxt, faqat nomlar, chekinish bilan
kubectl explain pod.spec.affinity --recursive | less
```

`--recursive` yo’l ostidagi har bir maydonni matnsiz daraxt ko’rinishida chop
etadi. Bu - sizga *taxminan* nima kerakligini bilganingizda (node affinity,
volume mount) va faqat yozilishi hamda ichma-ich joylashuvi to’g’ri bo’lishi
kerak bo’lganda kerak bo’ladigan ko’rinish.

```bash
kubectl explain deployment --api-version=apps/v1
kubectl explain ingress --api-version=networking.k8s.io/v1
kubectl explain cronjob.spec.jobTemplate.spec.template.spec.containers.resources
```

`--api-version` bitta kind bir nechta guruh versiyasida mavjud bo’lganda
kerakligini tanlaydi (masalan, HorizontalPodAutoscaler `autoscaling/v1` va
`autoscaling/v2`’da bor).

## Qisqa nomlar ham ishlaydi

```bash
kubectl explain deploy.spec.template.spec
kubectl explain svc.spec.ports
kubectl explain netpol.spec.ingress
kubectl explain pvc.spec
```

`kubectl api-resources` - uning hamrohi: u har bir kind’ni qisqa nomi, API
guruhi va namespace’ga bog’liq yoki yo’qligi bilan ro’yxatlaydi. Ikkalasi
yordamida siz hech qachon ko’rmagan obyekt uchun ham manifest yoza olasiz.

:::exam-tip
Maydon yo’lini noto’g’ri yozish - imtihondagi eng keng tarqalgan YAML xatosi:
bitta ortiqcha chekinish darajasi, `matchExpressions` o’rniga
`matchExpression`, `volumeMounts` o’rniga `volumeMount`.
`kubectl explain <kind>.<path> --recursive` nomni ham, ichma-ich joylashuvni
ham ikki soniyada aytadi va imtihon terminalida internetsiz ishlaydi. Uni
hujjatlardan oldin ishlating.
:::

## explain va hujjatlar sayti

| Savol | Tezroq usul |
|---|---|
| bu maydon qanday ataladi / qayerga qo’yiladi | `kubectl explain` |
| nusxa olish uchun to’liq misol manifest | kubernetes.io/docs (kind’ni qidiring, misolni nusxalang) |
| maydon qanday qiymatlarni qabul qiladi | `explain` (tavsifda enum’larni sanaydi) |
| tushunchaviy izoh | hujjatlar |

:::tip
`kubectl explain` uchun API server kerak - u sxemani klasterdan o’qiydi.
Shuning uchun u *shu* klasterga o’rnatilgan CRD’lar haqida ham aytadi, buni
ommaviy hujjatlar qila olmaydi.
:::

## O’zingizni tekshiring

1. Sizga `nodeAffinity` bloki kerak, lekin ichma-ich joylashuvini eslay
   olmayapsiz. Uni ko’rsatadigan aniq buyruq qaysi?
2. Bitta kind’ning ikkita API versiyasidan birini tanlashga qaysi bayroq
   imkon beradi?
3. Nega `kubectl explain` hujjatlar sayti eshitmagan CRD haqida biladi?
