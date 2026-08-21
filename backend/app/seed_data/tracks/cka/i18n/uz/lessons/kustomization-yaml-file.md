## Markazdagi fayl

Kustomize ishlov bera oladigan har bir katalogda bitta `kustomization.yaml`
(yoki `kustomization.yml`, yoki `Kustomization`) bo’ladi. U nimani qo’shishni
va unga nima qilishni sanab beradi.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

# NIMA - kirish manbalari
resources:
  - deployment.yaml
  - service.yaml
  - ../../base                 # o'z kustomization.yaml fayli bor boshqa katalog
  - https://github.com/org/repo//path?ref=v1.2.0    # uzoqdagi katalog

# QANDAY - yuqoridagi hammasiga qo'llanadigan transformerlar
namespace: prod
namePrefix: prod-
nameSuffix: -v2
commonLabels:                   # `labels` foydasiga eskirgan, lekin hali ishlaydi
  app: web
labels:
  - pairs: {team: payments}
    includeSelectors: false     # obyektlarga label qo'yadi, selectorlarga tegmaydi
commonAnnotations:
  owner: platform
images:
  - name: myapp
    newName: registry.example.com/myapp
    newTag: "2.1.0"
replicas:
  - name: web
    count: 5

# nishonga olingan o'zgarishlar
patches:
  - path: resources-patch.yaml                     # strategic merge patch fayli
  - patch: |-                                       # ichkariga yozilgan JSON 6902
      - op: replace
        path: /spec/replicas
        value: 3
    target: {kind: Deployment, name: web}

# yaratiladigan obyektlar
configMapGenerator:
  - name: app-config
    literals: [MODE=prod]
    files: [config.properties]
secretGenerator:
  - name: db-secret
    literals: [password=hunter2]
generatorOptions:
  disableNameSuffixHash: false  # yaratilgan nomlarda kontent hash qolsin (sukut bo'yicha)

# ixtiyoriy qismlar
components:
  - ../../components/caching
```

Hech qachon hammasini birdaniga ishlatmaysiz. Base odatda faqat
`resources:` yozuvidan iborat bo’ladi. Overlay esa
`resources: [../../base]` va qolganidan ikki-uchta yozuv.

## resources

Qo’shiladigan fayllar va kataloglar, tartib bilan. Fayl - oddiy manifest
(`---` bilan ko’p hujjatli ham bo’lishi mumkin). Katalogda esa o’zining
`kustomization.yaml` fayli bo’lishi shart va u rekursiv render qilinadi.
Yo’llar shu faylga nisbatan hisoblanadi.

```bash
kubectl kustomize .          # xato bo'lsa, xabar aynan qaysi fayl va maydon ekanini aytadi
```

Yangi faylni `resources`da sanashni unutish - o’sha klassik "hpa.yaml
qo’shdim, hech narsa o’zgarmadi" holati; Kustomize faqat sanalgan narsani
ko’radi.

## Amallar tartibi

Kustomize avval `resources`ni (rekursiv) yuklaydi, keyin **generator**’larni
qo’llaydi (yaratilgan ConfigMap/Secret’larni qo’shib), so’ng
**transformer**’larni (namespace, prefiks, labels, images, replicas), keyin
**patch**’larni, oxirida esa har bir havolani - Deployment’ning
`configMapRef`ini, Service’ning selector’ini - yangi nomlarga
o’zgartiradigan **name-reference tuzatish**ni bajaradi. Aynan shu oxirgi
qadam `namePrefix`ni xavfsiz qiladi: havolalar orqasidan ergashadi.

## U nima qilishini ko’rish

```bash
kubectl kustomize overlays/prod | less
kubectl kustomize overlays/prod | grep -E "^  name:|namespace:|image:|replicas:"
kubectl kustomize overlays/prod > /tmp/rendered.yaml && kubectl apply --dry-run=client -f /tmp/rendered.yaml
```

:::exam-tip
Notanish `kustomization.yaml`ni yuqoridan pastga shu tartibda o’qing: u
nimani qo’shadi (`resources`), hammasiga nima qiladi (namespace, prefiks,
labels, images), aynan nimani o’zgartiradi (`patches`). Keyin `apply -k`dan
oldin tasdiqlash uchun `kubectl kustomize`ni ishga tushiring. O’n besh
soniya, va natija sizni ajablantirmaydi.
:::

## O’zingizni tekshiring

1. Har bir kustomization’da bo’ladigan yagona maydon qaysi va unda nimalar
   bo’lishi mumkin?
2. Generator, transformer va patch’lar qaysi tartibda qo’llanadi?
3. Katalogga `hpa.yaml` qo’shdingiz, `kubectl apply -k` esa uni e’tiborsiz
   qoldirmoqda. Nega?
