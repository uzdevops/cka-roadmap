## Nega bitta Pod hech qachon yetarli emas

Pod - o’lguvchi. Uning node’i o’lishi mumkin, uning o’zi evict qilinishi
mumkin, konteyneri restart policy’ning sabri tugagunicha qulashi mumkin. Agar
sizga "har doim nginx’ning uchta nusxasi" kerak bo’lsa, siz uchta Pod
yaratmaysiz - siz uchta Pod *xohlaydigan* bitta obyekt va uni haqiqat holida
ushlab turadigan kontroller yaratasiz. O’sha obyekt - **ReplicaSet**.

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
```

Uch qism:

- **replicas** - nechta.
- **selector** - qaysi Pod’lar hisobga olinadi. ReplicaSet label’lari mos
  keladigan har bir Pod’ga egalik qiladi, ularni o’zi yaratgan yoki
  yaratmaganidan qat’i nazar.
- **template** - Pod’lar yetishmaganda yaratiladigan Pod. Uning label’lari
  selector’ni **qanoatlantirishi shart**, aks holda API server ReplicaSet’ni
  rad etadi.

Eskiroq `ReplicationController` xuddi shu ishni faqat tenglikka asoslangan
selector bilan va `matchExpressions`’siz bajargan. Uni eski manifestlarda hali
ham ko’rasiz; o’zingiz ReplicaSet yozing.

## Butun gap selector’da

```bash
kubectl get rs
kubectl get pods -l app=web
kubectl describe rs web | grep -E "Selector|Replicas"
```

Egalik label orqali aniqlangani uchun undan ikki narsa kelib chiqadi:

1. **Asrab olish**: `app: web` bilan qo’lda Pod yarating va ReplicaSet uni
   hisobga oladi - endi to’rtta bo’lgani uchun u bittasini o’chiradi (albatta
   siznikini emas).
2. **Yetim qoldirish**: `kubectl label pod web-abc12 app-` label’ni olib
   tashlaydi, Pod endi hisobga olinmaydi va ReplicaSet o’rniga yangisini
   yaratadi. Eski Pod boshqarilmagan holda ishlab turaveradi. Bu - bitta
   Pod’ni to’plamdan chiqarib olib tekshirishning usuli.

:::exam-tip
"ReplicaSet yaratmayapti" degani deyarli har doim
`spec.selector.matchLabels`’ning `spec.template.metadata.labels` bilan mos
kelmasligi. Xato aynan shuni aytadi - uni o’qing. Ikkinchi o’rindagi sabab:
noto’g’ri `apiVersion` (`v1` emas, `apps/v1`).
:::

## Masshtablash

```bash
kubectl scale rs web --replicas=5
kubectl scale --replicas=2 -f rs.yaml        # fayldan
kubectl edit rs web                          # spec.replicas'ni o'zgartirish
```

Kamaytirish Pod’larni o’chiradi; oshirish esa ularni shablondan yaratadi.
`scale` **nima qilmasligiga** e’tibor bering: u diskingizdagi faylni
o’zgartirmaydi. Keyingi `kubectl apply -f rs.yaml` replikalarni faylda nima
yozilgan bo’lsa, o’shanga qaytaradi.

## Shablonni o’zgartirish ishlab turgan Pod’larga hech narsa qilmaydi

ReplicaSet shablonidagi image’ni tahrirlang va ... hech narsa bo’lmaydi.
ReplicaSet Pod’larni faqat ular yetishmaganda yaratadi, shuning uchun mavjud
Pod’lar o’lgunicha eski image’da qolaveradi. O’zgarishni yoyish uchun
Pod’larni birma-bir o’chirib, qayta yaratilishini kutishingizga to’g’ri
kelardi. Bu zerikarli va xavfli - aynan shuning uchun siz ReplicaSet’ni
deyarli hech qachon to’g’ridan-to’g’ri yaratmaysiz: **Deployment** sizning
o’rningizga ReplicaSet’larni boshqaradi va rollingni bajaradi. Keyingi dars.

## Uni tez generatsiya qilish

`kubectl create replicaset` degan buyruq yo’q. Eng tez yo’l:

```bash
kubectl create deployment web --image=nginx:1.27 --replicas=3 --dry-run=client -o yaml \
  | sed 's/kind: Deployment/kind: ReplicaSet/' | grep -v strategy > rs.yaml
```

Yoki o’n ikki qatorni qo’lda yozing - bu yaxshi mashq va imtihonda
`kubectl explain rs.spec` sizga ochiq.

## O’zingizni tekshiring

1. ReplicaSet spec’ining uchta majburiy bo’limini yoddan yozing.
2. ReplicaSet sezmasligi uchun undan bitta Pod’ni tekshirishga qanday chiqarib
   olasiz - va u javoban *nima* qiladi?
3. ReplicaSet shablonidagi image’ni o’zgartirdingiz. Ishlab turgan uchta
   Pod’ga nima bo’ladi?
