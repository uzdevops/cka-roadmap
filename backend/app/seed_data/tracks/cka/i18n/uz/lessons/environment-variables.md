## env maydoni

Eng oddiy konfiguratsiya shakli: nom va qiymat, jarayonga muhit o’zgaruvchisi
sifatida ko’rinadi.

```yaml
spec:
  containers:
    - name: app
      image: myapp:2.0
      env:
        - name: APP_COLOR
          value: blue
        - name: APP_MODE
          value: "prod"
```

```bash
kubectl run app --image=myapp:2.0 --env=APP_COLOR=blue --env=APP_MODE=prod
kubectl exec app -- env | grep APP_
kubectl set env deployment/app APP_COLOR=green          # Deployment'da: rollout boshlanadi
kubectl set env deployment/app APP_COLOR-               # o'chirish
```

Qiymatlar - **satrlar**. `value: 8080` bu YAML uchun butun son va rad etiladi;
`value: "8080"` deb yozing.

## Qiymat uchun uchta manba

```yaml
env:
  - name: APP_COLOR
    value: blue                          # 1. to'g'ridan-to'g'ri qiymat

  - name: DB_HOST
    valueFrom:
      configMapKeyRef:                   # 2. ConfigMap'dagi bitta kalit
        name: app-config
        key: db_host

  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:                      # 3. Secret'dagi bitta kalit
        name: db-secret
        key: password
```

Va to’rtinchisi - u umuman konfiguratsiya emas, lekin bebaho:

```yaml
  - name: POD_NAME
    valueFrom:
      fieldRef:
        fieldPath: metadata.name         # Pod'ning o'z nomi, namespace'i, IP'si, node'i...
  - name: CPU_LIMIT
    valueFrom:
      resourceFieldRef:
        containerName: app
        resource: limits.cpu
```

Bu - **downward API**, ya’ni Pod o’zi haqida ma’lumot oladi. Ko’p
ishlatiladiganlari: `metadata.name`, `metadata.namespace`,
`metadata.labels['app']`, `status.podIP`, `spec.nodeName`.

## Hamma kalitni birdaniga: envFrom

```yaml
envFrom:
  - configMapRef:
      name: app-config           # ConfigMap'dagi har bir kalit o'zgaruvchiga aylanadi
  - secretRef:
      name: db-secret
  - configMapRef:
      name: feature-flags
      prefix: FF_                # ixtiyoriy: FF_<key>
```

`envFrom` - "butun ConfigMap’ni kiritish" uchun qisqa yo’l. Muhit
o’zgaruvchisi nomi sifatida yaroqsiz kalitlar tashlab ketiladi (hodisa bilan
birga). Agar bir nom `env`da ham, `envFrom`da ham bo’lsa, **`env` yutadi**.

:::exam-tip
"Pod `APP_COLOR`ni `webapp-config-map` ConfigMap’idan o’qisin" -
`valueFrom.configMapKeyRef`. "ConfigMap’ning hamma kalitini kiriting" -
`envFrom.configMapRef`. Ikkinchisi qisqaroq; topshiriqda aniq kalit
nomlanmagan yoki kalitdan boshqa o’zgaruvchi nomi so’ralmagan bo’lsa, o’shani
ishlating.
:::

## Nima noto’g’ri ketadi

| Alomat | Sababi |
|---|---|
| `CreateContainerConfigError` | `valueFrom`da nomlangan ConfigMap/Secret yoki **kalit** mavjud emas - `describe pod` qaysi biri ekanini aytadi |
| o’zgaruvchi bor, lekin eskirgan | Pod ishga tushgandan keyin ConfigMap o’zgargan; env faqat ishga tushishda o’qiladi - Pod’ni qayta yarating (rollout) |
| faylda qiymat `8080`, lekin API rad etadi | satr bo’lishi shart: `"8080"` |
| `envFrom` bir kalitni indamay tashlab ketdi | kalit yaroqli o’zgaruvchi nomi emas (`-` yoki `.` bor) |

`configMapKeyRef`/`secretKeyRef`dagi `optional: true` manba yo’q bo’lsa ham
Pod’ning ishga tushishiga imkon beradi - foydali, va o’zgaruvchi nega umuman
yo’qligini o’ylayotganingizda tuzoq.

## Natijani ko’rish

```bash
kubectl exec app -- env                                   # jarayon nimani ko'radi
kubectl exec app -- printenv APP_COLOR
kubectl describe pod app | grep -A10 "Environment:"       # nima sozlangani, manbalari bilan
kubectl get pod app -o jsonpath='{.spec.containers[0].env}'
```

:::tip
Secret’dan olingan o’zgaruvchilar uchun `kubectl describe` qiymat o’rniga
`<set to the key 'password' in secret 'db-secret'>` ko’rsatadi; haqiqiy
qiymatni `kubectl exec -- env` ko’rsatadi. Topshiriq qaysi birini o’qishni
so’rayotganini bilib oling.
:::

## O’zingizni tekshiring

1. `db-secret` Secret’ining `password` kalitidan `DB_PASSWORD`ni
   o’rnatadigan `env` yozuvini yozing.
2. ConfigMap’ni yangiladingiz. Uni `env` orqali o’qiydigan Pod bir soatdan
   keyin ham eski qiymatni ko’rsatyapti. Nega, va buni Deployment uchun
   qanday tuzatasiz?
3. `env` ham, `envFrom` ham `APP_MODE`ni turli qiymat bilan belgilagan.
   Konteyner qaysi birini ko’radi?
