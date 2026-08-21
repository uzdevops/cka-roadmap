## Bir-biridan uzoqlashadigan o’n ikkita fayl

Bitta ilova: `deployment.yaml`, `service.yaml`, `configmap.yaml`,
`ingress.yaml`. Uchta muhit. Sodda javob:

```
k8s/
  dev/    deployment.yaml service.yaml configmap.yaml ingress.yaml
  stg/    deployment.yaml service.yaml configmap.yaml ingress.yaml
  prod/   deployment.yaml service.yaml configmap.yaml ingress.yaml
```

O’n ikkita fayl, ulardan to’qqiztasi deyarli bir xil nusxa. Readiness probe
qo’shish: uchta faylni tahrirlash. Label’ni tuzatish: uchta fayl. Bir oy
ichida `dev`’da `prod`’da yo’q probe paydo bo’ladi va qaysi farqlar ataylab
qilinganini hech kim bilmaydi.

## G’oya: baza va overlay’lar

Umumiy manifestlarni **bir marta** yozing - bu baza - va har bir muhit uchun
faqat **nimasi farq qilishini**:

```
k8s/
  base/
    deployment.yaml  service.yaml  configmap.yaml  ingress.yaml
    kustomization.yaml          # to'rttasini sanaydi
  overlays/
    dev/
      kustomization.yaml        # resources: [../../base] ; replicas: 1 ; namePrefix: dev-
    stg/
      kustomization.yaml        # replicas: 2
    prod/
      kustomization.yaml        # replicas: 5 ; image tag 2.1.0 ; qo'shimcha HPA
```

```bash
kubectl apply -k overlays/prod
```

Kustomize overlay’ni o’qiydi, bazani tortib oladi, overlay’ning
o’zgarishlarini qo’llaydi va to’liq YAML chiqaradi. Baza - oddiy, to’g’ri
Kubernetes YAML’i, hech qanday joy egallovchisiz - har bir overlay esa diff
sifatida o’qiladigan qisqa farqlar ro’yxati.

## "customize" nimani anglatadi

Overlay ifodalay oladigan o’zgarishlar:

- har bir resursga tegadigan **transformerlar**: nom prefiksi yoki suffiksi,
  namespace, umumiy label yoki annotatsiya qo’shish, image tag’larini
  o’zgartirish;
- aniq resurslarning aniq maydonlarini o’zgartiradigan **patch’lar**: replika
  soni, resurs limiti, env o’zgaruvchisi, butunlay yangi konteyner;
- literal yoki fayllardan ConfigMap va Secret yaratadigan **generatorlar** -
  nomida mazmun hash’i bo’ladi, shuning uchun o’zgarish Pod’larni rollout
  qiladi;
- boshqa kataloglarni, boshqa overlay’larni yoki ixtiyoriy komponentlarni
  tortib oladigan **kompozitsiya**.

Shablon tili yo’q. `{{ }}` yo’q. Baza o’z holicha apply qilinadigan bo’lib
qoladi, ya’ni u o’qiladigan bo’lib qoladi va uni istalgan YAML asbobi lint
qila oladi.

## Ideologiya, uch qatorda

1. **To’liq deklarativ**: kustomization - bu YAML’ni tasvirlaydigan YAML.
2. **Shablonsiz**: faylni yaroqli qilish uchun uni hech qachon tahrirlamaysiz.
3. **kubectl ichiga qurilgan**: `kubectl apply -k` va `kubectl kustomize` uchun
   hech narsa o’rnatish shart emas.

:::exam-tip
Imtihon topshirig’ining shakli shunday: "baza katalogi va overlay berilgan;
`kubectl apply -k` X ni hosil qiladigan qilib overlay’ni tuzating yoki
to’ldiring". Siz `kustomization.yaml`’ni o’qiysiz, transformer yoki patch
qo’shasiz va apply qilasiz. Faylning bo’limlarini va `-k` bayrog’ini biling.
:::

## O’zingizni tekshiring

1. Har bir muhit uchun bittadan manifest katalogi bo’lishining muammosi nima?
2. Baza nima va overlay nimani o’z ichiga oladi?
3. Kustomization ifodalay oladigan o’zgarishlarning to’rt turini ayting.
