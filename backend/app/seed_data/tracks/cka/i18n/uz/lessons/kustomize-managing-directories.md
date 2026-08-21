## Har katalogga bitta kustomization, katalog ichidagi kataloglar

Haqiqiy loyiha - bitta papkadagi to’rtta fayl emas. U API, ma’lumotlar bazasi,
kesh, monitoring sidecar’i - har biri o’z manifestlari bilan - va siz butun
narsani bitta buyruq bilan yoki istalgan qismini alohida qo’llashni xohlaysiz.

```
k8s/
  kustomization.yaml          # resources: [api/, db/, cache/]
  api/
    kustomization.yaml        # resources: [deployment.yaml, service.yaml]
    deployment.yaml
    service.yaml
  db/
    kustomization.yaml        # resources: [statefulset.yaml, service.yaml, secret.yaml]
    statefulset.yaml
    service.yaml
    secret.yaml
  cache/
    kustomization.yaml
    deployment.yaml
    service.yaml
```

```yaml
# k8s/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - api
  - db
  - cache
```

```bash
kubectl apply -k k8s/            # hammasi
kubectl apply -k k8s/api/        # faqat API
```

**Katalog** bo’lgan `resources` yozuvi o’zining `kustomization.yaml` faylini
saqlashi shart; Kustomize uni rekursiv render qiladi va natijani qo’shadi. Har
bir ost-katalog o’zicha to’liq, mustaqil qo’llasa bo’ladigan birlik, root esa
ularni birlashtiradi. Uch daraja chuqurlik ham normal; qoida har bir darajada
bir xil.

## Nega har bir faylni sanaydigan bitta katta kustomization emas

```yaml
# bu ishlaydi va kataloglarni o'rganmaguningizcha sizda aynan shu bo'ladi
resources:
  - api/deployment.yaml
  - api/service.yaml
  - db/statefulset.yaml
  - db/service.yaml
  - db/secret.yaml
  - cache/deployment.yaml
  - cache/service.yaml
```

Bu shu paytgacha ishlaydi: faqat ma’lumotlar bazasini qo’llamoqchi
bo’lguningizcha; db obyektlariga `namespace: data` kerak, api’ga esa kerak
emas deguningizcha; to’rtinchi xizmat qo’shib, uning uchta faylidan birini
unutguningizcha. Har katalogga alohida kustomization har bir qismga o’z
transformer’larini va o’z `kubectl apply -k` sini beradi, root esa faqat
kataloglarni sanaydi.

## Har bir darajadagi transformer’lar

```yaml
# k8s/db/kustomization.yaml
resources: [statefulset.yaml, service.yaml, secret.yaml]
namespace: data              # faqat db obyektlari
commonLabels: {tier: data}
```

```yaml
# k8s/kustomization.yaml
resources: [api, db, cache]
commonLabels: {app: shop}    # hammasiga, bolalar qo'ygani ustiga
```

Avval bolalar o’zinikini qo’llaydi, keyin ota birlashgan natijaga o’zinikini
qo’llaydi. Label’lar to’planadi; otadagi `namespace` bolanikini bosib ketadi.

## Uzoqdagi kataloglar

```yaml
resources:
  - https://github.com/kubernetes-sigs/kustomize//examples/helloWorld?ref=v5.4.0
  - github.com/org/platform-base//k8s/base?ref=main
```

Repo’ni yo’ldan `//` ajratib turadigan va tag yoki commit’ni `?ref=` bilan
qotiradigan Git URL. Base’ni repozitoriylar orasida ana shunday ulashiladi -
albatta qotirilgan ref bilan, aks holda build’laringiz o’zingizdan bexabar
o’zgarib turadi.

:::exam-tip
Topshiriqning katalog daraxtida ost-kataloglar o’z kustomization’iga ega
bo’lsa, faqat bitta qismni qo’llash aytilmagan bo’lsa, ularni sanaydigan
**root**dan qo’llang (`kubectl apply -k k8s/`). Agar `kubectl kustomize`
katalog haqida "must have a kustomization file" desa, siz sanagan
ost-katalogda u yo’q - uni o’sha katalog fayllarini sanaydigan `resources:`
bilan yarating (yoki uning ichida `kustomize create --autodetect` ishga
tushiring).
:::

## O’zingizni tekshiring

1. `resources` ostida sanalishi uchun katalogda nima bo’lishi shart?
2. Ota kustomization `namespace: prod`, bola esa `namespace: data` qo’ysa,
   bolaning obyektlari uchun qaysi biri g’olib chiqadi?
3. Nega hamma fayllarni bitta ro’yxatga yig’ish o’rniga har katalogga alohida
   kustomization qilinadi?
