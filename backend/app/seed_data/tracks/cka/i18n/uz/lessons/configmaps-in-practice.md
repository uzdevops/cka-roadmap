## Konfiguratsiya - obyekt sifatida

ConfigMap - bu namespace’ga tegishli kalit/qiymat satrlari xaltasi. Uning
yagona vazifasi - maxfiy bo’lmagan konfiguratsiyani image’dan *tashqarida* va
Pod spec’idan tashqarida saqlash, shunda bir xil Deployment dev va prod’da
turli qiymatlarni o’qiy oladi va konfiguratsiyani o’zgartirish har bir Pod
shablonini tahrirlash emas, bitta obyektni o’zgartirish bo’ladi.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_COLOR: blue
  APP_MODE: prod
  nginx.conf: |                     # butun bir fayl - shunchaki ko'p qatorli qiymat
    server {
      listen 80;
      location / { return 200 'ok'; }
    }
```

## Uni yaratish

```bash
# to'g'ridan-to'g'ri qiymatlar
kubectl create configmap app-config --from-literal=APP_COLOR=blue --from-literal=APP_MODE=prod

# fayldan: kalit = fayl nomi, qiymat = fayl mazmuni
kubectl create configmap nginx-conf --from-file=nginx.conf
kubectl create configmap nginx-conf --from-file=site.conf=nginx.conf     # kalitni qayta nomlash

# katalogdagi har bir fayl
kubectl create configmap all-conf --from-file=./conf/

# env uslubidagi fayldan key=value satrlari
kubectl create configmap app-env --from-env-file=app.env

kubectl create configmap app-config --from-literal=A=1 $do > cm.yaml   # generatsiya, keyin apply
kubectl get configmap app-config -o yaml
kubectl describe configmap app-config
```

## Uni ishlatish - uchta shakl

**1. Bitta kalit, bitta muhit o’zgaruvchisi**

```yaml
env:
  - name: APP_COLOR
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: APP_COLOR
```

**2. Har bir kalit muhit o’zgaruvchisi sifatida**

```yaml
envFrom:
  - configMapRef:
      name: app-config
```

**3. Kalitlar katalogdagi fayllar sifatida**

```yaml
volumes:
  - name: config
    configMap:
      name: app-config
      # items:                       # ixtiyoriy: faqat ba'zi kalitlar, qayta nomlangan
      #   - key: nginx.conf
      #     path: default.conf
containers:
  - name: web
    volumeMounts:
      - name: config
        mountPath: /etc/nginx/conf.d
        readOnly: true
```

Har bir kalit o’z nomi bilan atalgan faylga aylanadi, ichida esa qiymat
turadi. Konfiguratsiya *fayllari* uchun shakl aynan shu.

```bash
kubectl exec web -- ls /etc/nginx/conf.d
kubectl exec web -- cat /etc/nginx/conf.d/nginx.conf
```

:::exam-tip
Mount qilingan ConfigMap o’zi ulangan **katalogni almashtiradi** - image’da
`/etc/nginx/conf.d` ichida nima bo’lgan bo’lsa, yo’qoladi, siz faqat
ConfigMap kalitlarini ko’rasiz. Boshqalarini yashirmasdan bitta fayl qo’shish
kerak bo’lsa, `subPath` bilan mount qiling:

```yaml
volumeMounts:
  - name: config
    mountPath: /etc/nginx/conf.d/default.conf
    subPath: nginx.conf
```

- va bilingki, `subPath` bilan mount qilinganlar ConfigMap o’zgarganda
yangilan**maydi**.
:::

## Yangilash va buni kim sezadi

| Qanday ishlatilgan | ConfigMap tahrirlangandan keyin |
|---|---|
| env o’zgaruvchisi | Pod qayta yaratilmaguncha hech narsa o’zgarmaydi |
| volume (katalog) | fayllar bir daqiqacha ichida joyida yangilanadi; ilova ularni qayta o’qishi kerak |
| `subPath` bilan volume | Pod qayta yaratilmaguncha hech narsa o’zgarmaydi |

Deployment uchun o’zgarishni tarqatishning ishonchli yo’li -
`kubectl rollout restart deployment/web`. Ba’zi jamoalar Pod shabloni
annotatsiyasiga ConfigMap hash’ini qo’yadi, shunda `apply` avtomatik rollout
qiladi; Kustomize buni `configMapGenerator` bilan siz uchun qiladi.

```yaml
immutable: true        # ConfigMap'da: tahrirlash mumkin emas; o'chirib qayta yarating
```

O’zgarmas ConfigMap’lar kubelet uchun arzonroq (u ularni kuzatishni to’xtatadi)
va tasodifiy jonli tahrirlardan himoya qiladi; evaziga esa aynan shu -
ularni tahrirlab bo’lmaydi.

## Cheklovlar va tuzoqlar

- ConfigMap hajmi **1 MiB** bilan chegaralangan. Kattaroq konfiguratsiya
  boshqa turdagi volume’ga tegishli.
- U **namespace’ga tegishli**: Pod faqat o’z namespace’idagi ConfigMap’ga
  murojaat qila oladi.
- `env`/`volumes`’da nomlangan ConfigMap yo’q bo’lsa, konteyner bloklanadi:
  abadiy `CreateContainerConfigError` / `ContainerCreating`, nomi esa
  `describe pod` hodisalarida ko’rinadi. `optional: true` buni "usiz ishga
  tush"ga o’zgartiradi.
- Binar ma’lumot `data`’ga emas, `binaryData`’ga (base64) yoziladi.

## O’zingizni tekshiring

1. `app.properties` faylini xuddi shu nomdagi ConfigMap kalitiga
   aylantiradigan `kubectl create configmap` buyrug’ini yozing.
2. ConfigMap’ni `/etc/app`’ga mount qildingiz va image’ning `/etc/app`
   ichidagi o’z fayllari yo’qoldi. Nega, va uning o’rniga bitta faylni nima
   mount qiladi?
3. Uchta ishlatish shaklidan qaysi biri ConfigMap tahririni Pod’ni qayta
   ishga tushirmasdan oladi?
