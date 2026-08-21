## Bitta mexanizmning uchta nomi

Har qanday ko’p konteynerli Pod bir xil uchta narsadan foydalanadi - umumiy
tarmoq, umumiy volume’lar, umumiy hayot tsikli. *Pattern*lar esa shunchaki
yordamchi qaysi tomonga qaraganini bildiradi.

```
          ┌──────────── Pod ─────────────┐
Sidecar   │  app ──volume──▶ helper      │  yordamchi yonma-yon ishlaydi (loglar, sync, sertifikatlar)
Adapter   │  app ──▶ helper ──▶ outside  │  yordamchi ilova chiqargan narsani qayta shakllantiradi
Ambassador│  outside ◀── helper ◀── app  │  yordamchi ilova iste'mol qiladigan narsani qayta shakllantiradi
          └──────────────────────────────┘
```

## Sidecar

Ilovaning o’zi bilmagan holda uni kengaytiradigan yordamchi: uning log
faylini o’qib jo’natadi, Git repo’ni kuzatib fayllarni umumiy volume’ga
sinxronlaydi, ilova o’qiydigan volume’ga TLS sertifikatini yangilab qo’yadi
yoki service mesh proxy’sini ishga tushiradi.

```yaml
containers:
  - name: web
    image: nginx
    volumeMounts: [{name: html, mountPath: /usr/share/nginx/html}]
  - name: git-sync
    image: registry.k8s.io/git-sync/git-sync:v4
    args: ["--repo=https://github.com/example/site", "--root=/tmp/git"]
    volumeMounts: [{name: html, mountPath: /tmp/git}]
volumes:
  - name: html
    emptyDir: {}
```

## Adapter

Ilova chiqishni *o’z* formatida beradi; adapter uni tashqi dunyo kutayotgan
formatga o’giradi. Klassik misol: ilova metrikalarni o’ziga xos formatda
chiqaradi, adapter (Prometheus exporter) ularni `localhost` orqali o’qiydi va
boshqa portda Prometheus formatida qaytadan chiqaradi. Platforma adapter’dan
yig’adi; ilovaga esa tegilmaydi.

## Ambassador

Buning ko’zgudagi aksi: ilova `localhost:port` bilan gaplashadi, ambassador
esa uni haqiqiy manzilga uzatadi - TLS va failover’ni o’z zimmasiga oladigan
ma’lumotlar bazasi proxy’si, connection pooler, cloud SQL proxy. Ilova bir
marta sozlanadi ("ma’lumotlar bazasi localhost:5432 da"), muhitlar orasidagi
farqlarni esa ambassador olib yuradi.

:::exam-tip
Imtihon pattern nomlarini baholamaydi. U YAML’ni baholaydi: `containers`
ostida ikkinchi element, umumiy `emptyDir`, ikkalasida ham to’g’ri
`volumeMounts`, `logs`/`exec` da `-c`. "Bu sidecar topshirig’i" ekanini
tanib olish sizga faqat qanday shakl kutilayotganini aytadi.
:::

## Native sidecar’lar: ishlashda davom etadigan init konteynerlar

Kubernetes 1.29 dan beri "ilovadan oldin ishga tushishi shart va undan keyin
ham yashashi mumkin bo’lgan yordamchi"ni ifodalashning to’laqonli yo’li bor:
**`restartPolicy: Always` bilan yozilgan init konteyner**.

```yaml
spec:
  initContainers:
    - name: log-shipper
      image: fluent/fluent-bit:2.2
      restartPolicy: Always          # <- uni bir martalik init emas, sidecar qiladi
      volumeMounts: [{name: logs, mountPath: /var/log/app}]
  containers:
    - name: app
      image: myapp:1.0
      volumeMounts: [{name: logs, mountPath: /var/log/app}]
  volumes:
    - name: logs
      emptyDir: {}
```

Oddiy ikkinchi konteynerga nisbatan u nimani tuzatadi:

| | ikkinchi `containers` elementi | native sidecar (init + `restartPolicy: Always`) |
|---|---|---|
| ishga tushish tartibi | kafolat yo’q | ilova konteynerlaridan **oldin** ishga tushadi va ular boshlanishidan avval ishga tushgan (tugagan emas) bo’lishi shart |
| to’xtash tartibi | kafolat yo’q | ilova konteynerlaridan **keyin** to’xtatiladi |
| Job’lar | sidecar Job Pod’ini abadiy tirik qoldiradi | ilova konteyneri chiqishi bilan Job tugaydi |
| qayta ishga tushish | restartPolicy bo’yicha | har doim qayta ishga tushiriladi |

Yordamchi ilova unga murojaat qilishidan oldin tayyor bo’lishi kerak bo’lgan
har qanday holatda shundan foydalaning (proxy, secret agenti) - bu esa
holatlarning aksariyati.

## O’zingizni tekshiring

1. Ilovani localhost orqali o’qib, Prometheus metrikalarini qaytadan
   chiqaradigan metrics exporter - qaysi pattern va nega?
2. Init konteynerni "native sidecar" qiladigan narsa nima va bu qanday tartib
   kafolatini beradi?
3. Nega an’anaviy sidecar Job’ni buzadi va native shakl buni qanday tuzatadi?
