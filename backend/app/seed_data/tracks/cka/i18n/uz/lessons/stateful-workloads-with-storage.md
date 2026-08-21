## "Stateful" aslida nimani talab qiladi

Stateless replikani istalgan narsa o’ldirib, istalgan joyda almashtira oladi;
ma’lumotlar bazasi replikasini esa yo’q. Unga Deployment bermaydigan uchta
narsa kerak:

1. **barqaror identifikatsiya** - `db-0` doim primary, `db-1` doim birinchi
   replika bo’ladi va ular bir-birini nom orqali topadi;
2. **o’ziga ergashadigan o’z storage’i** - `db-1`’ning ma’lumoti keyin
   yaratilgan qaysidir Pod’ga emas, aynan `db-1`’ga qaytadi;
3. **tartiblangan amallar** - `db-0`’ni `db-1`’dan oldin ishga tushirish,
   `db-2`’ni `db-1`’dan oldin to’xtatish, shunda replikatsiya va kvorum
   mantiqqa ega bo’ladi.

**StatefulSet** uchalasini ham beradi; bu dars esa ular shu haftaning storage
obyektlari bilan qanday birlashishi haqida.

## Barqaror nomlar: headless Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: db
spec:
  clusterIP: None              # headless: VIP yo'q, DNS Pod IP'larini qaytaradi
  selector:
    app: db
  ports:
    - port: 5432
```

StatefulSet’da `serviceName: db` bo’lsa, har bir Pod DNS nomiga ega bo’ladi:

```
db-0.db.default.svc.cluster.local
db-1.db.default.svc.cluster.local
db-2.db.default.svc.cluster.local
```

Replikani "primary - `db-0.db`" deb sozlash mumkin va bu qayta ishga
tushirishlar hamda qayta rejalashtirishlar davomida to’g’ri bo’lib qoladi.
Shunchaki *biror* ulanish kerak bo’lgan mijozlar uchun yonida oddiy Service
ham turishi mumkin (`db-rw` - operator qo’llab turadigan label orqali faqat
primary’ni tanlaydi, `db-ro` esa hammasini tanlaydi).

## Ergashadigan storage: volumeClaimTemplates

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: db
spec:
  serviceName: db
  replicas: 3
  podManagementPolicy: OrderedReady          # yoki Parallel
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0                           # >0: faqat partition dan katta-teng tartib raqamlari yangilanadi (canary)
  selector:
    matchLabels: {app: db}
  template:
    metadata:
      labels: {app: db}
    spec:
      containers:
        - name: postgres
          image: postgres:16
          ports: [{containerPort: 5432}]
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: [ReadWriteOnce]
        storageClassName: fast
        resources: {requests: {storage: 20Gi}}
```

`data-db-0..2` claim’lari shablondan yaratiladi, har bir tartib raqamiga
bittadan; har biri RWO va faqat o’z Pod’iga tegishli;
`WaitForFirstConsumer` class esa har bir diskni Pod rejalashtirilgan joyda
yaratadi. Bog’lanish **nom** bo’yicha: `db-1` nomli Pod doim `data-db-1`
nomli claim’ni mount qiladi.

```bash
kubectl get sts db
kubectl get pods -l app=db -o wide          # db-0, db-1, db-2 - tasodifiy suffiks yo'q
kubectl get pvc -l app=db
kubectl delete pod db-1                     # db-1 bo'lib qaytadi, o'sha PVC, o'sha ma'lumot
kubectl scale sts db --replicas=5           # avval db-3, keyin db-4, tartib bilan, har biriga yangi claim
kubectl scale sts db --replicas=3           # avval db-4, keyin db-3 olib tashlanadi; data-db-3/4 CLAIM'LARI QOLADI
```

## Tartib

`OrderedReady` (sukut bo’yicha): Pod’lar `0, 1, 2` tartibida yaratiladi, har
biri oldingisi Running va Ready bo’lishini kutadi; o’chirish esa teskari
tartibda. `Parallel` buni ahamiyat bermaydigan workload’lar uchun olib
tashlaydi. Yangilanishlar eng katta tartib raqamidan pastga qarab boradi;
`partition: 2` faqat `db-2`’ni yangilaydi - keyin 0 ga tushiradigan bir Pod’lik
canary.

## Nima avtomatik emas

StatefulSet sizga nomlarni, disklarni va tartibni beradi. U PostgreSQL’ni
**bilmaydi**: replikani primary qilib ko’tarmaydi, uni primary’dan qayta
qurmaydi va backup olmaydi. Bu bilim **operator**da (PostgreSQL uchun
CloudNativePG, Zalando, Crunchy; Kafka uchun Strimzi) yashaydi, u esa ostida
StatefulSet’lardan yoki o’zining Pod boshqaruvidan foydalanadi. Imtihon uchun
obyekt - StatefulSet; productionda esa deyarli har doim uning ustida operator
kerak bo’ladi.

:::exam-tip
Imtihondagi StatefulSet topshiriqlari mexanikaga oid: N replika va
volumeClaimTemplate bilan bittasini yarating, Pod nomlari va PVC’larni
tasdiqlang, masshtabini o’zgartiring, ehtimol headless Service qo’ying.
Tekshiring: `serviceName` mavjud headless Service’ga mos kelsin;
`volumeClaimTemplates` `template` ostida emas, `spec` ostida bo’lsin;
`volumeMounts` nomi shablonning `metadata.name` iga teng bo’lsin.
:::

## O’zingizni tekshiring

1. Stateful workload’ga kerak bo’lgan, Deployment bermaydigan uchta narsani
   ayting.
2. `kubectl delete pod db-1`’dan keyin o’rniga kelgan Pod qaysi PVC’ni mount
   qiladi va nega?
3. StatefulSet’ni 5 dan 3 ga kamaytirganingizda nima qolib ketadi va nega bu
   to’g’ri sukut sozlamasi?
