## Avval shuni ishlating, oxirigacha

**Init konteyner** ilova konteynerlaridan oldin ishlaydi, muvaffaqiyatli
chiqishi shart va shu bilan uning ishi tugaydi. Bir nechtasi **navbat bilan,
tartibda** ishlaydi; oxirgi init konteyner 0 bilan chiqmaguncha ilova
konteynerlari ishga tushmaydi. Ulardan ilova boshlanishidan oldin bajarilgan
bo’lishi kerak bo’lgan ishlar uchun foydalaning: sxema migratsiyasi,
shablondan yasaladigan konfiguratsiya fayli, bog’liqlikni kutish tsikli,
umumiy volume’ga yuklab olinadigan fayl.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  initContainers:
    - name: wait-for-db
      image: busybox:1.36
      command: ["sh", "-c", "until nslookup db.payroll.svc.cluster.local; do echo waiting; sleep 2; done"]
    - name: fetch-config
      image: busybox:1.36
      command: ["sh", "-c", "wget -O /work/app.conf http://config-svc/app.conf"]
      volumeMounts: [{name: work, mountPath: /work}]
  containers:
    - name: app
      image: myapp:1.0
      volumeMounts: [{name: work, mountPath: /etc/app}]
  volumes:
    - name: work
      emptyDir: {}
```

Init konteynerlar qolgan hamma jihatdan oddiy konteynerlar: o’z image’i,
buyrug’i, resurslari, volume mount’lari bor. Ularda ilova image’ida yo’q
vositalar bo’lishi mumkin (curl, nslookup, migratsiya CLI’si) - bu
ulardan foydalanishning eng yaxshi sabablaridan biri.

## Ular ishlayotganda nima ko’rasiz

```bash
kubectl get pod app
# NAME   READY   STATUS     RESTARTS   AGE
# app    0/1     Init:0/2   0          5s      <- 2 ta init konteynerdan 0 tasi tugadi
# app    0/1     Init:1/2   0          12s
# app    0/1     PodInitializing
# app    1/1     Running
```

| STATUS | Ma’nosi |
|---|---|
| `Init:0/2` | ikkita init konteynerdan birinchisi ishlayapti |
| `Init:Error` | init konteyner noldan farqli kod bilan chiqdi |
| `Init:CrashLoopBackOff` | u qayta-qayta ishlamayapti; kubelet urinishlar orasidagi kutishni uzaytirmoqda |
| `PodInitializing` | init tugadi, ilova konteynerlari yaratilmoqda |

```bash
kubectl describe pod app | grep -A12 "Init Containers:"
kubectl logs app -c wait-for-db             # init konteyner loglari, nomi bo'yicha
kubectl logs app -c wait-for-db --previous  # ishlamay qolgan urinish
```

:::exam-tip
`Init:...`’da qotib qolgan Pod - init konteyner muammosi, ilova konteyneriga
aloqasi yo’q - va `-c`’siz ishlatilgan `kubectl logs <pod>` sizga init
konteynerni **ko’rsatmaydi** (u hali ishga tushmagan ilovani ko’rsatishga
urinadi va xato beradi). Yechim har doim `kubectl logs <pod> -c <init-name>`
va o’n holatning to’qqiztasida sabab - init buyrug’idagi xato: `sleeeep`,
noto’g’ri Service nomi, URL’da tushib qolgan sxema.
:::

## Qayta ishga tushish qoidalari

Init konteyner ishlamasa, kubelet aynan **o’shani** qayta ishga tushiradi
(Pod’ning `restartPolicy`siga bo’ysunadi; `Never` bo’lsa butun Pod ishdan
chiqadi). U nihoyat muvaffaqiyatli tugagach, keyingi init konteyner ishlaydi.
Agar *Pod*ning o’zi qayta ishga tushsa - node qayta yuklandi, Pod evict
qilinib qaytadan yaratildi - **hamma** init konteynerlar birinchisidan
boshlab yana ishlaydi, shuning uchun ular idempotent bo’lishi kerak: "jadval
mavjud bo’lmasa, uni yarat", "jadvalni yarat" emas.

## Init konteynerlar nima emas

- Ular doimiy ishlab turishi kerak bo’lgan narsalar uchun emas. Ilova yonida
  tirik turishi kerak bo’lgan yordamchi - bu sidecar, yoki native sidecar
  (`restartPolicy: Always` bilan init konteyner, oldingi dars), bu esa "avval
  ishga tushish" *va* "ishlashda davom etish"ni birga olishning zamonaviy
  yo’li.
- Ularda readiness probe bo’lmaydi (ular chiqishi bilan tugagan hisoblanadi) -
  lekin resurs request’lari bo’lishi mumkin va Pod’ning amaldagi request’i (eng
  katta init konteyner, ilova konteynerlari yig’indisi) ikkovidan **maksimumi**
  bo’ladi, chunki ular hech qachon ilova bilan bir vaqtda ishlamaydi.

## Mavjud Pod’ga bittasini qo’shish

`initContainers` ishlab turgan Pod’da o’zgarmas:

```bash
kubectl get pod red -o yaml > red.yaml
# spec.initContainers: [{name: warm-up, image: busybox, command: [sleep, "20"]}] ni qo'shing
kubectl replace --force -f red.yaml
kubectl get pod red -w                    # 20 s davomida Init:0/1, keyin Running
```

## O’zingizni tekshiring

1. Ikkita init konteyner va ikkita ilova konteyneri qanday tartibda ishga
   tushadi va har biri nimani kutadi?
2. Pod `Init:CrashLoopBackOff` ko’rsatmoqda. Sababini aynan qaysi buyruq
   ko’rsatadi?
3. Nega init konteynerning ishi idempotent bo’lishi kerak?
