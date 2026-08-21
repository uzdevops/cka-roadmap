## Map’ni patch qilish

Manifestning katta qismi map’lardan iborat - `metadata.labels`,
`spec.template.spec`, `resources.limits`. Ularni uchta amal qoplaydi:
qiymatni almashtirish, kalit qo’shish, kalitni o’chirish.

Boshlang’ich nuqta:

```yaml
# base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  labels:
    component: api
spec:
  replicas: 1
  template:
    metadata:
      labels:
        component: api
    spec:
      containers:
        - name: api
          image: myapi:1.0
```

## Replace

```yaml
# JSON 6902
patches:
  - target: {kind: Deployment, name: api}
    patch: |-
      - op: replace
        path: /spec/template/metadata/labels/component
        value: web
```

```yaml
# strategic merge - xuddi shu o'zgarish
patches:
  - patch: |-
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: api
      spec:
        template:
          metadata:
            labels:
              component: web
```

Strategic merge’da siz yozgan kalit o’sha kalitning mavjud qiymatini
**almashtiradi** va yondosh kalitlarga tegmaydi - shuning uchun
`component: web` bitta label’ni o’zgartiradi va boshqalarini saqlab qoladi.

## Add

```yaml
# JSON 6902
- op: add
  path: /spec/template/metadata/labels/org
  value: KodeKloud
```

```yaml
# strategic merge: qo'shish - bu shunchaki bo'lmagan kalitni yozish
spec:
  template:
    metadata:
      labels:
        org: KodeKloud
```

Allaqachon mavjud yo’lda `add` replace kabi ishlaydi. Ota-elementi yo’q
yo’lga `add` xato beradi - avval otasini qo’shing (yoki oraliq map’larni
o’zi yaratadigan strategic merge’dan foydalaning).

## Remove

```yaml
# JSON 6902
- op: remove
  path: /spec/template/metadata/labels/org
```

```yaml
# strategic merge: kalitga null qiymat bering
spec:
  template:
    metadata:
      labels:
        org: null
```

Ikkalasi ham ishlaydi; JSON 6902’ning `remove` amali oshkora, merge
patch’dagi `null` esa odamlar borligini unutadigan usul.

## Map’lar ichiga yo’llar

JSON pointer yo’li - `/` bilan ajratilgan kalitlar:

```
/metadata/labels/component
/spec/template/spec/containers/0/resources/limits/memory     <- LIST ichidan indeks bo'yicha
/spec/template/metadata/annotations/prometheus.io~1scrape    <- "/" bor kalit ~1 sifatida escape qilinadi
```

Oxirgisi slash’li annotation’lar uchun muhim (`prometheus.io/scrape`,
`nginx.ingress.kubernetes.io/rewrite-target`): `/` belgisi `~1` ga
aylanadi, `~` esa `~0` ga. Strategic merge patch’da esa kalitni shunchaki
qo’shtirnoq ichida yozasiz.

```yaml
# strategic merge, escaping yo'q
metadata:
  annotations:
    prometheus.io/scrape: "true"
```

## Tekshirish

```bash
kubectl kustomize . | grep -A3 "labels:"
kubectl kustomize . | grep -c "org: KodeKloud"
```

:::exam-tip
Map maydonlari uchun, kalitni **o’chirish** kerak bo’lmasa, strategic merge
shaklini oling - u YAML kabi o’qiladi, yetishmagan ota-elementlarni o’zi
yaratadi va annotation’dagi slash escaping’i umuman chiqmaydi. JSON 6902’ni
o’chirishlar uchun va keyingi darsdagi list’lar uchun saqlang.
:::

## O’zingizni tekshiring

1. Pod template’idagi `component` label’ini `web` ga o’zgartiradigan
   patch’ning ikkala shaklini yozing.
2. Strategic merge patch bilan kalitni qanday o’chirasiz?
3. Pod template’idagi `prometheus.io/scrape` annotation’i uchun JSON
   pointer yo’lini yozing.
