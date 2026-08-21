## Ixtiyoriy imkoniyatlar, har overlay’da alohida yoqiladi

Overlay’lar "dev yoki prod" savoliga javob beradi. Component’lar esa boshqa
savolga javob beradi: **"X imkoniyati bilanmi yoki usizmi"** - kesh, tashqi
ma’lumotlar bazasi, LDAP auth, debug sidecar’i - bunda bir xil imkoniyat
bir nechta overlay’da kerak bo’lib, boshqalarida kerak bo’lmasligi mumkin,
uning patch’larini har bir overlay’ga nusxalash esa yana o’sha
bir-biridan uzoqlashish muammosi.

**Component** - bu overlay o’ziga **qo’shib oladigan**, qayta ishlatiladigan
resurslar va patch’lar to’plami. U baza emas (o’zi mustaqil turmaydi) va
overlay ham emas (to’liq ilova hosil qilmaydi); u - istalgan
kustomization’ga qo’shsa bo’ladigan bo’lak.

```
k8s/
  base/                         ilovaning o'zi
  components/
    caching/
      kustomization.yaml        kind: Component
      redis.yaml                Redis Deployment va Service
      api-patch.yaml            api konteyneriga REDIS_HOST beradi
    external-db/
      kustomization.yaml        kind: Component
      db-patch.yaml             ichki db ni olib tashlaydi, api ni tashqi hostga qaratadi
  overlays/
    dev/        resources: [../../base]                                      # oddiy
    prod/       resources: [../../base]; components: [../../components/caching, ../../components/external-db]
    staging/    resources: [../../base]; components: [../../components/caching]
```

## Uni yozish

```yaml
# components/caching/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component
resources:
  - redis.yaml
patches:
  - path: api-patch.yaml
```

```yaml
# components/caching/api-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  template:
    spec:
      containers:
        - name: api
          env:
            - name: REDIS_HOST
              value: redis
```

`kind: Component` va `v1alpha1` apiVersion’iga e’tibor bering - component
o’zining alohida kind’i. Uning patch’lari **uni qo’shgan overlay**
beradigan resurslarga qaratilgan (bu yerda - bazadagi `api` Deployment’i);
o’z holicha `kubectl kustomize components/caching` xato beradi, chunki
patch qiladigan narsa yo’q.

## Undan foydalanish

```yaml
# overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
components:
  - ../../components/caching
  - ../../components/external-db
namespace: prod
```

```bash
kubectl kustomize overlays/prod | grep -E "^kind:|REDIS_HOST"     # Redis obyektlari va env o'zgaruvchisi bor
kubectl kustomize overlays/dev  | grep -c redis                    # 0
```

Component’lar `resources` yuklangandan **keyin** va overlay’ning o’z
transformer’lari hamda patch’laridan oldin, sanalgan tartibda qo’llanadi -
shuning uchun keyingi component oldingisi qo’shgan narsani patch qila
oladi.

## Overlay va component

| | Overlay | Component |
|---|---|---|
| javob beradi | qaysi muhit | qaysi ixtiyoriy imkoniyat |
| nimani qo’shadi | bazani (`resources`) | o’zi hech narsani; uni `components:` orqali qo’shishadi |
| `kind` | Kustomization | Component |
| birlashtirish | har muhitga bitta | har overlay’ga istalgancha |

Yutuq kombinatorikada: 3 muhit × 4 ixtiyoriy imkoniyat - component’siz 12
ta overlay, ular bilan esa 3 ta overlay va 4 ta component.

:::exam-tip
Topshiriqda component’lar tilga olinsa, uchta narsani tekshiring:
component faylida `v1alpha1` apiVersion bilan `kind: Component` turibdimi;
overlay uni `components:` ostida sanaganmi (`resources:` ostida emas - siz
ko’radigan xato aynan shu); va component’ning patch’lari bazada mavjud
nomlarga qaratilganmi. So’ng overlay’ni `kubectl kustomize` qiling va
component qo’shadigan narsani grep qiling.
:::

## O’zingizni tekshiring

1. Overlay’lar javob bermaydigan qaysi savolga component’lar javob beradi?
2. Component’ning `apiVersion` va `kind` qiymatlari qanday va u overlay’ning
   qaysi maydoni ostida qo’shiladi?
3. Nega `kubectl kustomize components/caching` o’z holicha xato beradi?
