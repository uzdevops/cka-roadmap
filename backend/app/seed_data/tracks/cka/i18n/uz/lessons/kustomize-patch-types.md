## Inline yoki faylda

Ikkala patch tilini ham `kustomization.yaml` ichida **inline** yoki **alohida
faylda** yozsa bo’ladi; tanlov o’qilishi haqida, imkoniyat haqida emas.

### Inline

```yaml
patches:
  - target: {kind: Deployment, name: api}
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 3
  - target: {kind: Deployment, name: api}
    patch: |-
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: api
      spec:
        template:
          spec:
            containers:
              - name: api
                image: myapi:2.1.0
```

`|-` literal blokni boshlaydi; patch tanasi uning ostida chekinish bilan
yoziladi. Kustomize qaysi til ekanini o’zi aniqlaydi: `op:` yozuvlaridan
iborat YAML **ro’yxati** - JSON 6902; `kind:` bor YAML **map**’i - strategic
merge.

Inline bir qatorlik narsalar uchun to’g’ri keladi - replika soni, bitta env
o’zgaruvchi - bunda alohida fayl mazmunidan ko’ra ko’proq ortiqcha yuk
bo’lardi.

### Fayl

```yaml
patches:
  - path: patches/api-resources.yaml                         # strategic merge; target fayldan o'qiladi
  - path: patches/api-nodeselector.json                      # JSON 6902; aniq target kerak
    target: {kind: Deployment, name: api}
```

```yaml
# patches/api-resources.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  template:
    spec:
      containers:
        - name: api
          resources:
            requests: {cpu: 250m, memory: 256Mi}
            limits:   {cpu: "1",  memory: 512Mi}
```

```json
[
  {"op": "add", "path": "/spec/template/spec/nodeSelector", "value": {"disktype": "ssd"}}
]
```

Fayl esa patch bir necha qatordan uzun bo’lsa, uni bir nechta overlay
bo’lishsa (`- path: ../../patches/common.yaml`) yoki uni alohida diff
sifatida ko’rib chiqishni xohlasangiz to’g’ri keladi.

## Ikki o’qni aralashtirish

| | JSON 6902 | Strategic merge |
|---|---|---|
| inline | `op:` ro’yxati bo’lgan `patch: \|-` + `target:` | qisman obyekt bo’lgan `patch: \|-` (obyekt o’z nomini aytsa, target ixtiyoriy) |
| fayl | `path: x.json` yoki `x.yaml` + `target:` | `path: x.yaml` (target fayldan) |

Yagona qoida: **JSON 6902 patch’iga har doim `target:` kerak**, chunki
operatsiyalar ro’yxati u qaysi obyektga tegishli ekani haqida hech narsa
demaydi. Strategic merge patch’i o’zining `apiVersion`/`kind`/`metadata.name`
ini olib yuradi va `target` unga faqat shuni bekor qilish yoki kengaytirish
uchun kerak (`labelSelector`).

## Hali ham uchraydigan eski maydonlar

```yaml
patchesStrategicMerge:        # eskirgan: strategic merge patch fayllari ro'yxati
  - memory-patch.yaml
patchesJson6902:              # eskirgan: target + JSON 6902 fayliga yo'l
  - target: {group: apps, version: v1, kind: Deployment, name: api}
    path: replicas.json
```

Ikkalasi ham ogohlantirish bilan hamon ishlaydi; `patches:` ularning o’rnini
egalladi va har qanday holatni uddalaydi. `patches:` deb yozing.

:::exam-tip
Agar topshiriq sizga patch **fayli**ni bersa, uni `- path:` bilan ulang (JSON
6902 bo’lsa, ustiga `target:`). Agar o’zgarish jumla bilan tasvirlangan
bo’lsa, inline `patch: |-` eng tez yo’l. Har ikki holatda ham odatdagi xato -
`patch: |-` ostidagi chekinish: patch tanasi `patch:`’ning o’zidan ko’proq
chekintirilishi kerak, strategic merge tanasi esa `apiVersion:`’dan
boshlanishi shart.
:::

## O’zingizni tekshiring

1. Kustomize inline JSON 6902 patch’ini inline strategic merge patch’idan
   qanday ajratadi?
2. Qaysi patch shakli har doim `target:` talab qiladi va nega?
3. Patch’ni inline emas, faylga qachon joylashtirasiz?
