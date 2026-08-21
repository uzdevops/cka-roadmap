## Bitta obyektda bitta narsani o’zgartirish

Transformer’lar har bir resursni o’zgartiradi. **Patch** esa aniq
resurslarning aniq maydonlarini o’zgartiradi: mana bu Deployment’ning
replikalari, ana u konteynerning memory limiti, qo’shimcha env o’zgaruvchi,
yangi volume. Ikkita patch tili, bitta `patches:` maydoni.

```yaml
patches:
  - target:                          # QAYSI resurs(lar)
      kind: Deployment
      name: api
    patch: |-                        # NIMA qilish - JSON 6902 shakli
      - op: replace
        path: /spec/replicas
        value: 3
  - path: memory-patch.yaml          # NIMA qilish - strategic merge shakli, faylda
```

## JSON 6902 patch’lari: yo’llar ustidagi operatsiyalar

```yaml
- op: replace                        # add | remove | replace | move | copy | test
  path: /spec/template/spec/containers/0/resources/limits/memory
  value: 512Mi
- op: add
  path: /spec/template/spec/containers/0/env/-          # `-` = ro'yxat oxiriga qo'shish
  value: {name: MODE, value: prod}
- op: remove
  path: /spec/template/spec/containers/1                # indeks bo'yicha
```

`path` - bu JSON pointer: `/` bilan ajratiladi, ro’yxatlar indeks bo’yicha,
`-` esa "ro’yxat oxiri" degani. Aniq, bir oz quruq va maydonni yoki elementni
toza **o’chira** oladigan yagona shakl.

## Strategic merge patch’lari: qisman obyekt

```yaml
# memory-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api                          # nishonni aniqlaydi
spec:
  template:
    spec:
      containers:
        - name: api                  # merge key: konteynerni indeks emas, NOM bo'yicha topadi
          resources:
            limits:
              memory: 512Mi
```

Siz obyektning o’zgartirmoqchi bo’lgan qismini yozasiz; Kustomize uni
haqiqiysiga birlashtiradi va ro’yxat elementlarini moslashtirishda har bir
maydonning **merge key**ini ishlatadi (konteynerlar, portlar, env
o’zgaruvchilar, volume’lar uchun - `name`). O’qishga qulay va siz allaqachon
biladigan narsaga o’xshagan shakl - lekin u `$patch: delete` direktivasisiz
ro’yxat elementini o’chira olmaydi.

## Nishonga olish

```yaml
patches:
  - path: patch.yaml                         # strategic merge: fayldagi apiVersion/kind/name - AYNAN nishon
  - patch: |- ...
    target:                                  # JSON 6902, yoki o'z nomi yo'q strategic merge patch:
      group: apps
      version: v1
      kind: Deployment
      name: api                              # aniq nom, yoki
      labelSelector: "tier=web"              # shu label'li har bir Deployment
      namespace: shop
      annotationSelector: ...
```

`name`’siz, `labelSelector` bilan berilgan nishon mos keladigan **har bir**
resursni patch qiladi - bitta patch `tier=web` label’i bo’lgan barcha
Deployment’larga `nodeSelector` qo’shadi. `name` regex’ni
qo’llab-quvvatlaydi (`name: "api-.*"`).

## Ikkalasi bitta faylda

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources: [../../base]
patches:
  - path: replicas-patch.yaml                      # strategic merge fayli
  - path: env-patch.yaml
  - target: {kind: Deployment, name: api}          # inline JSON 6902
    patch: |-
      - op: add
        path: /spec/template/spec/nodeSelector
        value: {disktype: ssd}
```

:::exam-tip
Fe’lga qarab tanlang. **Maydonni o’rnatish yoki qo’shish** → ikkala shakl
ham; strategic merge fayli xatoga kamroq olib keladi. Maydonni yoki ro’yxat
elementini **o’chirish** → JSON 6902. **Ro’yxatga qo’shish** (konteyner, env
o’zgaruvchi) → merge key bilan strategic merge eng tushunarli; JSON 6902’da
`/.../-`’ga `add` ham ishlaydi. Keyin maydonni `kubectl
kustomize | grep` bilan qidiring. Nishoni hech narsaga mos kelmagan patch -
bu xato; uni o’qing: u qidirgan kind va nomni aytadi.
:::

## O’zingizni tekshiring

1. Ikkita patch shakli qaysilar va qaysi biri maxsus direktivasiz ro’yxat
   elementini o’chira oladi?
2. Strategic merge patch’ida Kustomize ro’yxatdagi qaysi konteynerni nazarda
   tutayotganingizni qanday biladi?
3. `tier=web` label’i bo’lgan har bir Deployment’ga bitta patch’ni qanday
   qo’llaysiz?
