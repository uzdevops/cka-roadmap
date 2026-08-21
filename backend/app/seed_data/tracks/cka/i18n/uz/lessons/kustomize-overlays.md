## Muhitlarni arzon qiladigan tuzilma

```
k8s/
  base/
    kustomization.yaml        # resources: [deployment.yaml, service.yaml, configmap.yaml]
    deployment.yaml
    service.yaml
    configmap.yaml
  overlays/
    dev/
      kustomization.yaml
    staging/
      kustomization.yaml
      replicas-patch.yaml
    prod/
      kustomization.yaml
      resources-patch.yaml
      hpa.yaml                # FAQAT prod'da mavjud obyekt
```

Baza to’liq va to’g’ri. Har bir overlay - bu `resources: [../../base]` va
uning farqlari - hamda muhitga boshqalarda yo’q narsa kerak bo’lsa,
o’zining **qo’shimcha resursi**.

```yaml
# overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources: [../../base]
namespace: dev
nameSuffix: -dev
images: [{name: myapi, newTag: main}]
replicas: [{name: api, count: 1}]
```

```yaml
# overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
  - hpa.yaml                            # faqat prod uchun obyekt
namespace: prod
images: [{name: myapi, newTag: "2.1.0"}]
replicas: [{name: api, count: 5}]
patches:
  - path: resources-patch.yaml          # prod'da kattaroq limitlar
labels:
  - pairs: {env: prod}
    includeSelectors: false
```

```bash
kubectl apply -k k8s/overlays/dev
kubectl apply -k k8s/overlays/prod
diff <(kubectl kustomize k8s/overlays/dev) <(kubectl kustomize k8s/overlays/prod)
```

## Nima qayerga tegishli

| Bazada | Overlay’da |
|---|---|
| hamma joyda to’g’ri bo’lgan hamma narsa: Deployment’ning shakli, Service, probe’lar, ilovani belgilaydigan label’lar | replika sonlari, image tag’lari, resurs o’lchamlari, hostname’lar, namespace, muhitga xos ConfigMap qiymatlari |
| oqilona standart qiymatlar (1 replika, kichik limitlar) - dev’ga o’xshash | faqat bitta muhitda bo’ladigan obyektlar (HPA, PDB, debug sidecar’i) |
| | secret havolalari (Secret’ning o’zi odatda boshqa joydan keladi) |

Agar bir xil patch’ni har bir overlay’da uchratsangiz, uning o’rni bazada.
Agar biror joyda `if prod` ni uchratsangiz, sizda overlay yetishmayapti.

## Overlay ustidagi overlay’lar

Overlay o’ziga baza sifatida boshqa overlay’ni olishi mumkin -
`overlays/prod-eu` `../prod` ni qo’shadi va region label’i bilan
hostname’ni o’zgartiradi. Kustomize cheksiz birlashtiraveradi. Qiymat
qayerdan kelganini topish uchun `kubectl kustomize` chiqishini o’qish sizga
zavq bermasa, ikki daraja bilan cheklaning.

## Har bir muhit uchun generatsiya qilingan ConfigMap’lar

```yaml
# overlays/prod/kustomization.yaml
configMapGenerator:
  - name: app-config
    behavior: merge                # bazadagi app-config ga birlashtiriladi (yoki replace / create)
    literals:
      - LOG_LEVEL=warn
      - DB_HOST=db.prod.svc
```

Sukut bo’yicha nomga qo’shiladigan hash tufayli o’zgargan qiymat yangi
ConfigMap nomini beradi (`app-config-7f9b2c`) va Kustomize Deployment’dagi
havolani qayta yozadi - ya’ni konfiguratsiya o’zgarishi **Pod’larni qayta
yaratadi**, `kubectl edit configmap` esa buni hech qachon qilmaydi.

:::exam-tip
Imtihondagi overlay topshirig’i odatda sizga bazani beradi va "replikani N
ga qo’yadigan, T image tag’ini ishlatadigan va hamma narsani X namespace’iga
joylaydigan" overlay so’raydi - uchta maydon (`replicas`, `images`,
`namespace`) va `resources: [../../base]`. Katalogni yarating, o’sha besh
qatorni yozing, tekshirish uchun `kubectl kustomize`, so’ng `kubectl apply
-k`. Ikki daqiqadan kam.
:::

## O’zingizni tekshiring

1. Bazaga nima kiradi va overlay’ga nima kiradi - har biriga bittadan
   jumla?
2. Boshqalarida yo’q obyektni (masalan, HPA) muhit qanday oladi?
3. Nega generatsiya qilingan ConfigMap qiymatini o’zgartirish Pod’larni
   qayta yaratadi, ConfigMap’ni qo’lda tahrirlash esa yo’q?
