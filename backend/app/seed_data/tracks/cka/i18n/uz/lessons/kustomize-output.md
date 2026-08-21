## Avval render, keyin apply

Kustomize ishlab chiqaradigan yagona narsa - stdout’ga chiqadigan YAML.
Qolgan hammasi - siz o’sha YAML bilan nima qilishingiz.

```bash
kubectl kustomize overlays/prod
# yoki: kustomize build overlays/prod
```

```yaml
apiVersion: v1
kind: Service
metadata:
  labels:
    app: web
  name: prod-web
  namespace: prod
spec:
  ...
---
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: web
  name: prod-web
  namespace: prod
spec:
  replicas: 5
  ...
```

Ko’p hujjatli oqim, tartiblangan (avval Namespace va CRD’lar, keyin
qolganlari), shuning uchun yuqoridan pastga qo’llash ishlaydi. Uni o’qing:
API server’ga **aynan** shu boradi. Agar natija noto’g’ri bo’lsa,
kustomization noto’g’ri; ikkisi orasida hech narsa buni o’zgartira olmaydi.

## Uni qo’llash

```bash
kubectl kustomize overlays/prod | kubectl apply -f -      # ikki qadamli shakl: render, pipe
kubectl apply -k overlays/prod                             # bir qadamli shakl: natija aynan bir xil
kubectl apply -k overlays/prod --dry-run=server           # klasterga qarshi tekshiradi, hech narsa qo'llamaydi
kubectl diff -k overlays/prod                              # jonli holatga nisbatan nima o'zgaradi
kubectl delete -k overlays/prod                            # overlay yaratgan hamma narsani o'chiradi
```

Ikki qadamli shaklning odatdan tashqari foydasi ham bor: render qilingan
faylni saqlab commit qilish, uni `-k`’ni tushunmaydigan asbobga berish yoki
CI’da uni `grep` qilish.

```bash
kubectl kustomize overlays/prod > rendered/prod.yaml
```

## Natijani tez tekshirish

```bash
kubectl kustomize overlays/prod | grep -c "^kind:"                     # nechta obyekt
kubectl kustomize overlays/prod | grep -E "^kind:|^  name:"            # kind va nomlar
kubectl kustomize overlays/prod | yq '.metadata.namespace' -            # yq o'rnatilgan bo'lsa
kubectl kustomize overlays/prod | kubectl apply --dry-run=client -f -   # umuman obyekt sifatida o'qiladimi
```

## Xatolar apply’dan emas, render’dan keladi

```
error: accumulating resources: ... 'deployment.yml' must be a file (got 'deployment.yaml')
error: no matches for Id Deployment.v1.apps/api.[noNs]; failed to find unique target for patch
error: evalsymlink failure on '../../base' : lstat ...: no such file or directory
```

Ular maydon va yo’lni aytib beradi. Shuning uchun tekshiruv asbobi -
`kubectl kustomize`: toza natija bermaguncha uni ishga tushiravering, faqat
shundan keyin `apply -k`.

:::exam-tip
Topshiriqda har doim `kubectl apply -k <dir>`’dan oldin
`kubectl kustomize <dir>`’ni ishga tushiring - bu bitta buyruq, uch soniya
turadi va "apply nega bunday qildi" degan savolni "ha, patch hech nimani
nishonga olmayapti"ga aylantiradi. Apply’dan keyin `kubectl get all -n <ns>`
natija va’da qilgan nomlarni tasdiqlaydi.
:::

## O’zingizni tekshiring

1. `kubectl kustomize` nima ishlab chiqaradi va uning `kubectl apply -k`
   bilan aloqasi qanday?
2. Hech narsani qo’llamasdan, apply nimani o’zgartirishini **oldindan**
   qanday ko’rasiz?
3. Patch xatosi chiqdi. Bu render paytidagi xatomi yoki apply paytidagimi va
   bu sizga uni qayerda tuzatish kerakligi haqida nima deydi?
