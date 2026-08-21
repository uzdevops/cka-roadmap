## Ikki konteyner qachon birga bo’ladi

Har Pod’ga bitta konteyner - qoida. Istisno - ikki jarayon **hayot tsikli**ni,
**network namespace**ni va **storage**ni shu qadar zich bo’lishishi kerak
bo’lgan holat: ularni ajratib ishga tushirish shu uchtalasini qaytadan ixtiro
qilish degani bo’ladi - ilovaning fayliga tail qiladigan log yig’uvchi, ilova
oldida localhost’da turadigan proxy, ilova o’qiydigan sertifikatni yangilab
turadigan agent.

Ko’p konteynerli Pod ularga aynan shuni beradi:

- **bir xil network namespace** - ular bitta IP va bitta port fazosini
  bo’lishadi; `localhost` orqali gaplashadi; ikkalasi ham 8080-portni band
  qila olmaydi;
- **umumiy volume’lar** - Pod’dagi har qanday volume ikkalasiga ham mount
  qilinishi mumkin;
- **bitta hayot tsikli** - birga, bitta node’ga joylashtiriladi; birga ishga
  tushadi; Pod *hammasi* tayyor bo’lgandagina Ready bo’ladi; birga o’chiriladi.

Ular fayl tizimini (faqat aniq mount qilingan volume’lardan tashqari), sukut
bo’yicha process namespace’ni va resurs limitlarini (har konteynerning
o’ziniki bor) **bo’lishmaydi**.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  volumes:
    - name: logs
      emptyDir: {}
  containers:
    - name: app
      image: myapp:1.0
      volumeMounts:
        - name: logs
          mountPath: /var/log/app
    - name: log-shipper
      image: fluent/fluent-bit:2.2
      volumeMounts:
        - name: logs
          mountPath: /var/log/app
          readOnly: true
```

Ilova `/var/log/app/app.log`’ga yozadi; yig’uvchi esa o’sha faylni umumiy
`emptyDir` orqali o’qiydi. Ikkalasi ham bir-birining borligini bilmaydi.

## Ular bilan ishlash

```bash
kubectl get pod app                      # READY 2/2
kubectl describe pod app | grep -A2 "Containers:"
kubectl logs app -c log-shipper          # ikkita konteyner bo'lgach -c majburiy
kubectl logs app --all-containers --prefix
kubectl exec app -c app -- ls /var/log/app
kubectl get pod app -o jsonpath='{.spec.containers[*].name}'
```

`READY 1/2` bitta konteyner tayyor emasligini bildiradi - `describe` qaysi
biri va nega ekanini aytadi. Ikkalasidan birining ishdan chiqishi Pod’ni
emas, o’sha konteynerni qayta ishga tushiradi va `RESTARTS` har konteyner
bo’yicha alohida sanaladi.

:::exam-tip
Imtihonda ikkita shakl uchraydi: "`Z` Pod’iga `Y` image’li `X` sidecar
konteynerini qo’shing" - Pod’ning konteynerlar ro’yxati o’zgarmas, shuning
uchun yo’l `kubectl get pod Z -o yaml`, konteynerni qo’shish,
`kubectl replace --force`. Va "bu ko’p konteynerli Pod Ready emas" -
`kubectl describe` qaysi konteyner ishlamayotganini ko’rsatadi, odatda
sababi noto’g’ri image yoki chiqib ketadigan buyruq.
:::

## `emptyDir` qayerga to’g’ri keladi

`emptyDir` - aynan shu ish uchun yaratilgan volume turi: Pod ishga tushganda
yaratiladigan, Pod yashaguncha yashaydigan va uning konteynerlari o’rtasida
bo’lishiladigan bo’sh katalog. Vaqtinchalik joy, loglarni uzatish, init
konteynerdan ilovaga o’tadigan build artefakti. `emptyDir: {medium: Memory}`
uni tmpfs’ga joylaydi.

## Volume’dan ko’prog’ini bo’lishish

```yaml
spec:
  shareProcessNamespace: true
```

Bu bilan konteynerlar bir-birining jarayonlarini ko’radi (biridagi `ps`
ikkinchisinikini ham ko’rsatadi), bu esa sidecar’larni tekshirish va
signalga asoslangan muvofiqlashtirishni mumkin qiladi. Sukut bo’yicha
o’chirilgan.

## Buni qachon qilmaslik kerak

Agar bu ikki narsa mustaqil masshtablansa, mustaqil qayta ishga tushsa yoki
turli jamoalarga tegishli bo’lsa, ular bitta Pod’dagi ikki konteyner emas,
orasida Service turgan ikki Deployment bo’ladi. Sinov - hayot tsikli: agar
birini ikkinchisisiz qayta ishga tushirish yoki masshtablashni xohlashingiz
ehtimoli bo’lsa, ularni ajrating.

## O’zingizni tekshiring

1. Bitta Pod’dagi konteynerlar bo’lishadigan uchta narsani va bo’lishmaydigan
   ikkita narsani ayting.
2. Ko’p konteynerli Pod’da aniq bir konteynerning loglarini qaysi buyruq
   o’qiydi?
3. Pod `READY 1/2` ko’rsatmoqda. Bu nimani anglatadi va birinchi buyruq
   qaysi?
