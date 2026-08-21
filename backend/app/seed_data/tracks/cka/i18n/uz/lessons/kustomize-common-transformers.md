## Hammasini bir yo’la o’zgartirish

Transformer - kustomization ishlab chiqaradigan **har bir** resursni
o’zgartiradigan kustomization maydoni. Ulardan to’rttasi amaldagi
qo’llanishlarning deyarli hammasini qoplaydi.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources: [../../base]

namespace: prod               # har bir namespace'li obyektga metadata.namespace qo'yadi
namePrefix: prod-             # name: web  ->  prod-web
nameSuffix: -v2               # name: web  ->  web-v2   (ikkalasi: prod-web-v2)
commonLabels:                 # metadata.labels'ga HAM, selector/template'larga HAM
  org: KodeKloud
  env: prod
commonAnnotations:
  owner: platform-team
```

```bash
kubectl kustomize overlays/prod | grep -E "^  name:|namespace:|org:|owner:"
```

## namespace

Har bir namespace’li resursga `metadata.namespace` qo’yadi va fayllarda
nima yozilgan bo’lsa, bosib ketadi. Klaster darajasidagi obyektlarga
(Namespace, ClusterRole, CRD) tegmaydi. U Namespace’ni **yaratmaydi** -
`resources` ichiga Namespace manifestini qo’shing yoki uni oldin yarating.

## namePrefix / nameSuffix

Har bir obyektni qayta nomlaydi va - eng muhimi - unga bo’lgan **har bir
havolani tuzatadi**: Ingress backend’idagi Service nomi, Deployment’ning
`envFrom`idagi ConfigMap nomi, RoleBinding’dagi ServiceAccount nomi. Ana shu
havolalarni tuzatish prefikslarni ishlatib bo’ladigan qiladi; usiz har bir
overlay o’z ulanishlarini buzib qo’yardi.

## commonLabels va labels

`commonLabels` label’larni `metadata.labels`’ga **va** har bir selectorga
qo’shadi: Deployment’larda `spec.selector.matchLabels`, Service’larda
`spec.selector`, hamda `spec.template.metadata.labels`. Bu Service va
Deployment’larni mos holda ushlab turadi - va amalda label’larni
**o’zgarmas** qilib qo’yadi, chunki Deployment’ning selectori yaratilgandan
keyin o’zgara olmaydi. Shu sababli allaqachon deploy qilingan overlay’ga
commonLabel qo’shish `field is immutable` xatosi bilan tugaydi.

Yangiroq `labels` maydoni tanlash imkonini beradi:

```yaml
labels:
  - pairs:
      team: payments
    includeSelectors: false      # faqat metadata - keyin qo'shsa ham xavfsiz
    includeTemplates: true       # Pod template'larida ham, ya'ni Pod'lar oladi
  - pairs:
      app: web
    includeSelectors: true       # commonLabels bilan bir xil
```

:::warning
`commonLabels` (yoki `includeSelectors: true`) faqat birinchi kundanoq
ilovaning o’ziga xosligiga kiradigan label’lar uchun ishlatilsin. Keyinroq
qo’shishingiz mumkin bo’lgan hamma narsa - `team`, `cost-center`,
`version` - `includeSelectors: false` bilan `labels`’ga tushadi, aks holda
bitta label’ni o’zgartirish uchun Deployment’larni o’chirib, qaytadan
yaratasiz.
:::

## Oilaning qolgan qismi

| Transformer | Nima qiladi |
|---|---|
| `images` | image nomi/tegi/digest’ini o’zgartiradi (keyingi dars) |
| `replicas` | nomi ko’rsatilgan Deployment/StatefulSet’larga patchsiz replika soni qo’yadi |
| `commonAnnotations` | hamma joyga annotation’lar |
| `configMapGenerator` / `secretGenerator` | kontent hash’i qo’shilgan obyektlar generatsiya qiladi; havolalar yangilanadi |
| `patches` | nishonli o’zgarishlar (patch darslari) |

```yaml
replicas:
  - name: web
    count: 5
```

## Tartib faqat qat’iy belgilangani bilan muhim

Kustomize transformer’larni o’z tartibida qo’llaydi (namespace, nomlar,
label’lar, annotation’lar, images, replicas, keyin patch’lar), shuning uchun
siz bu haqda hech o’ylamaysiz - bitta istisno bilan: **patch** obyektni
transformer’lardan **keyin** ko’radi, shuning uchun `namePrefix: prod-`
qo’yilganda `name: web`’ga mo’ljallangan patch `prod-web`’ni emas, `web`’ni
nishonga olishi kerak - Kustomize patch nishonlarini original nomlar bilan
solishtiradi. Patch’lar darsi bunga qaytadi.

## O’zingizni tekshiring

1. `namePrefix` qayta nomlashdan tashqari yana nima qiladi va nega bu shart?
2. `commonLabels` bilan `includeSelectors: false` li `labels` orasidagi farq
   nima va u qachon og’riq keltiradi?
3. `namespace: prod` namespace’ni yaratadimi?
