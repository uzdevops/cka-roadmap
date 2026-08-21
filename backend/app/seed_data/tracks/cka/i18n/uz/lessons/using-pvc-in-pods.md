## Claim uchraydigan uchta joy

PersistentVolumeClaim Pod’da, Deployment’da va StatefulSet’da bir xil
ishlatiladi - `persistentVolumeClaim` volume’i va unga mos `volumeMounts`
yozuvi - lekin claim’ga *kim egalik qilishi* har xil, bu esa nechta replika
undan foydalana olishini va ular o’lganda nima bo’lishini hal qiladi.

## Pod ichida

```yaml
spec:
  containers:
    - name: app
      image: myapp
      volumeMounts:
        - name: data
          mountPath: /var/lib/app
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: app-data
```

Claim Pod’dan oldin mavjud bo’ladi; Pod’ni o’chirib qayta yarating -
ma’lumot joyida turadi. Bu shakl bir martalik ish, Job yoki o’zingiz
boshqaradigan yagona replika uchun.

## Deployment ichida

```yaml
kind: Deployment
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: app
          volumeMounts: [{name: data, mountPath: /var/lib/app}]
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: app-data            # BITTA claim, hamma replika uchun umumiy
```

Har bir replika **bir xil** claim’ni mount qiladi. RWO volume bilan bu har
bir replika bitta node’ga tushishi kerakligini anglatadi - aks holda ikkinchi
replika `Multi-Attach error` bilan `ContainerCreating`’da qotib qoladi.
Rolling update paytida ham yangi Pod eskisi volume’ni bo’shatmaguncha uni
ulay olmasligi mumkin, shuning uchun ko’pincha halol sozlama -
`strategy: Recreate`. PVC’li Deployment’lar **bitta replika** uchun yoki
umumiy foydalanish maqsad bo’lgan RWX storage (NFS) uchun.

:::warning
Bitta RWO claim bilan `replicas: 3` - klassik xato: bitta Pod Running, ikkitasi
qotib qolgan, hodisalar esa `Multi-Attach error for volume` bilan to’lgan.
Yechim - StatefulSet, yoki RWX storage, yoki bitta replika yetarli ekanini
tan olish.
:::

## StatefulSet ichida: har replikaga bitta claim

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: db
spec:
  serviceName: db                      # Pod'ga barqaror DNS beruvchi headless Service
  replicas: 3
  selector:
    matchLabels: {app: db}
  template:
    metadata:
      labels: {app: db}
    spec:
      containers:
        - name: postgres
          image: postgres:16
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:                # HAR REPLIKA uchun bittadan bosib chiqariladigan PVC
    - metadata:
        name: data
      spec:
        accessModes: [ReadWriteOnce]
        storageClassName: fast
        resources:
          requests:
            storage: 10Gi
```

```bash
kubectl get pvc
# data-db-0   Bound   pvc-3f1...   10Gi   RWO   fast
# data-db-1   Bound   pvc-8a2...   10Gi   RWO   fast
# data-db-2   Bound   pvc-c91...   10Gi   RWO   fast
```

`volumeClaimTemplates` `data-db-0`, `data-db-1`, `data-db-2`’ni yaratadi -
har bir tartib raqamiga bitta claim. `db-1` qayta rejalashtirilganda, qayerga
tushishidan qat’i nazar, `data-db-1`’ni qaytarib oladi. Masshtabni kamaytirish
claim’larni **o’chirmaydi** (ma’lumot keyingi kengaytirish uchun saqlanadi);
StatefulSet’ni o’chirish ham, agar
`persistentVolumeClaimRetentionPolicy` boshqacha aytmasa, ularni
o’chirmaydi. Bu shakl ma’lumotlar bazalari, broker’lar - har bir replikaning
o’z identifikatsiyasi va o’z diski bo’lishi kerak bo’lgan hamma narsa uchun.

## Tanlash

| Workload | Claim kimga tegishli |
|---|---|
| bitta replika yoki Job | Pod / Deployment ichida qo’lda yaratilgan PVC |
| bitta fayl tizimini bo’lishuvchi N replika (yuklamalar, umumiy kesh) | Deployment ichida bitta RWX PVC |
| har biri o’z diskiga ega N replika (ma’lumotlar bazalari) | `volumeClaimTemplates` bilan StatefulSet |

:::exam-tip
Topshiriqda "har bir replika o’z persistent volume’iga ega bo’lsin" deyilgan
bo’lsa, so’z StatefulSet haqida, maydon esa `volumeClaimTemplates`. Agar
bitta replika bilan "ilova qayta ishga tushirishlar orasida ma’lumotini
saqlasin" deyilgan bo’lsa, PVC va Deployment (yoki Pod) yetarli - ortiqcha
murakkablashtirmang.
:::

## Ulanishni o’qish

```bash
kubectl get pod db-0 -o jsonpath='{.spec.volumes[*].persistentVolumeClaim.claimName}'
kubectl describe pod db-0 | grep -A3 "Volumes:"
kubectl get pvc -l app=db
kubectl get events --field-selector involvedObject.name=db-1 | grep -i attach
```

## O’zingizni tekshiring

1. 3 replikali Deployment bitta RWO claim’ni bo’lishadi. Nima bo’ladi va
   undan chiqishning ikki yo’li qaysi?
2. `volumeClaimTemplates` nima yaratadi va StatefulSet masshtabi
   kamaytirilganda o’sha claim’larga nima bo’ladi?
3. Yuqoridagi uchta shaklning har birida claim’ga kim egalik qiladi?
