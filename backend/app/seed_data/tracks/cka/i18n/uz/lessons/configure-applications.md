## Konteynerga o’zini qanday tutishni aytishning to’rtta yo’li

Image qat’iy; ilova esa yo’q. Bir xil nginx image’i mingta turli saytga
xizmat qiladi, chunki konfiguratsiya ishga tushish vaqtida kiritiladi.
Kubernetes sizga to’rtta richag beradi va bu haftaning darslari ularni
bittalab ko’rib chiqadi. Bu sahifa - xarita.

| Richag | Nimani o’zgartiradi | Pod spec’ida qayerda turadi |
|---|---|---|
| **command / args** | qaysi jarayon, qanday argumentlar bilan ishga tushishini | `containers[].command`, `containers[].args` |
| **muhit o’zgaruvchilari** | jarayonga ko’rinadigan key=value | `containers[].env`, `containers[].envFrom` |
| **ConfigMap’lar** | maxfiy bo’lmagan konfiguratsiya: qiymatlar yoki butun fayllar | `env`/`envFrom`’dan murojaat qilinadi yoki volume sifatida mount qilinadi |
| **Secret’lar** | xuddi shu, lekin login-parol va kalitlar uchun | ConfigMap bilan bir xil shakllar, boshqa kind va boshqa muomala |

```yaml
spec:
  containers:
    - name: app
      image: myapp:2.0
      command: ["python", "server.py"]          # ENTRYPOINT ekvivalenti
      args: ["--port", "8080"]                  # CMD ekvivalenti
      env:
        - name: MODE
          value: production                     # literal qiymat
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:                    # ConfigMap'dan bitta kalit
              name: app-config
              key: db_host
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:                       # Secret'dan bitta kalit
              name: db-secret
              key: password
      envFrom:
        - configMapRef:
            name: app-config                    # har bir kalit env o'zgaruvchisi sifatida
      volumeMounts:
        - name: config
          mountPath: /etc/app                   # har bir kalit fayl sifatida
  volumes:
    - name: config
      configMap:
        name: app-config
```

Buni avval yaxlit holda bir marta o’qing, keyingi darslar esa har bir blokni
to’ldiradi.

## Qaysi ish uchun qaysi richag

- Jarayon yoki uning flag’lari muhitga qarab farq qiladi → **command/args**.
- Bir nechta oddiy sozlama → **env** (literal qiymatlar yoki ConfigMap’dan).
- Ilova o’qiydigan konfiguratsiya *fayli* (`nginx.conf`, `application.properties`) → **volume sifatida mount qilingan ConfigMap**.
- Maxfiy har qanday narsa → xuddi shu ikki shaklning **Secret** variantlari.

Sizni keng tarqalgan xatolardan saqlaydigan ikkita qoida:

1. **Muhit o’zgaruvchilari faqat bir marta, jarayon boshlanganda o’qiladi.**
   ConfigMap’ni o’zgartirsangiz, ishlab turgan Pod’ning env’i o’zgarmaydi;
   Pod qayta yaratilishi kerak (Deployment rollout’i shuni qiladi). Mount
   qilingan fayllar esa qisqa kechikishdan keyin joyida yangilanadi - agar
   `subPath` bilan mount qilinmagan bo’lsa.
2. **Secret’lar - shifrlash emas.** Ular API’da base64, etcd diskida esa
   ochiq matn - siz encryption at rest sozlamagan bo’lsangiz. Secret’lar
   ustidagi RBAC va etcd diskini haqiqiy nazorat vositasi deb biling.

:::exam-tip
Bu sohadagi deyarli har bir topshiriq yo "X ni muhit o’zgaruvchisi sifatida
kiriting", yo "X ni /path ga mount qiling" deydi. Muharrirni ochishdan oldin
qaysi shakl ekanini hal qiling; ikkalasining YAML’i shu qadar farq qiladiki,
noto’g’risidan boshlash qayta yozishga olib keladi.
:::

## Konteyner ishga tushganda nima bo’ladi, tartibi bilan

1. Volume’lar (ConfigMap va Secret volume’lari ham) mount qilinadi.
2. Muhit yig’iladi: `env` va `envFrom` hal qilinadi; yetishmayotgan ConfigMap
   yoki Secret kaliti konteynerni `CreateContainerConfigError` bilan ishdan
   chiqaradi - `kubectl describe pod` o’sha kalitning nomini aytadi.
3. `command` va `args` birlashtiriladi va bajariladi.

Uchinchi qadam - keyingi ikki darsning mavzusi: Docker’ning `ENTRYPOINT` va
`CMD` i `command` va `args`’ga qanday moslashadi va nima nimani bekor qiladi.

## O’zingizni tekshiring

1. Pod muhit o’zgaruvchisi sifatida ishlatayotgan ConfigMap’dagi qiymatni
   o’zgartirdingiz. Ishlab turgan Pod nimani ko’radi va siz buni qanday hal
   qilasiz?
2. Dockerfile’dagi `CMD`’ga Pod’ning qaysi maydoni mos keladi?
3. Pod `CreateContainerConfigError`’da qotib qolgan. Eng ehtimolli sabab
   nima va muammoning aniq nomi qayerda chiqariladi?
