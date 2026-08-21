## So’rov tomoni

PersistentVolumeClaim - bu foydalanuvchining storage uchun so’rovi, namespace
ichida:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: myclaim
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Mi
  storageClassName: manual          # PV'nikiga teng bo'lishi yoki ikkalasida ham bo'lmasligi shart
  # selector:                       # ixtiyoriy: faqat shu label'lardagi PV'lar
  #   matchLabels: {type: ssd}
```

```bash
kubectl apply -f pvc.yaml
kubectl get pvc
# NAME      STATUS   VOLUME    CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# myclaim   Bound    pv-vol1   1Gi        RWO            manual         3s
```

## Bog’lanish qanday ishlaydi

PV kontrolleri claim’ni qanoatlantiradigan `Available` PV’ni qidiradi:

| Claim nimani so’raydi | PV nima qilishi kerak |
|---|---|
| `storage: 500Mi` | sig’imi ≥ 500Mi bo’lishi (claim **butun** PV’ni oladi - bu yerda 1Gi, CAPACITY ustunida ko’rinadi) |
| RWO access mode | shu mode’ni ro’yxatida ko’rsatishi |
| `storageClassName: manual` | xuddi shu class nomiga ega bo’lishi (bo’sh faqat bo’shga mos keladi) |
| selector | mos keluvchi label’larni olib yurishi |

Yetarli bo’lgan eng kichik PV afzal ko’riladi, lekin bog’lanish baribir
bir-birga: 1Gi claim’ga bog’langan 100Gi PV **sarflab bo’lingan** hisoblanadi.
Hech narsa mos kelmasa, claim `Pending` bo’lib qoladi va
`kubectl describe pvc` sababini tushuntiradi - yoki dinamik StorageClass
bo’lsa, mos keladigan PV yaratiladi (keyingi dars).

```bash
kubectl describe pvc myclaim | tail -5
#  Warning  ProvisioningFailed / no persistent volumes available for this claim and no storage class is set
```

:::exam-tip
Qo’lda yaratilgan PV bor klasterda Pending claim deyarli har doim shulardan
biri: access mode mos kelmagan, `storageClassName` mos kelmagan (bir tomonda
`manual`, ikkinchisida hech narsa yo’q) yoki PV allaqachon `Bound`/`Released`.
`kubectl get pv` va `kubectl describe pvc` yonma-yon qaysi biri ekanini
ko’rsatadi.
:::

## Claim’ni Pod’da ishlatish

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: webapp
spec:
  containers:
    - name: webapp
      image: webapp
      volumeMounts:
        - name: log
          mountPath: /log
  volumes:
    - name: log
      persistentVolumeClaim:
        claimName: myclaim
```

Pod hech qachon PV’ni emas, **claim**ni nomlaydi. Gap ham shunda: Pod spec’i
har bir klasterda bir xil bo’ladi; claim esa o’sha klasterda qanday storage
bo’lsa, o’shani topadi.

`Pending` holatdagi claim Pod’ni ham `Pending` holatda ushlab turadi -
`ContainerCreating` yoki bog’lanmagan claim haqidagi hodisa bilan. Pod’ga
emas, claim’ga qarang.

## O’chirish

```bash
kubectl delete pvc myclaim
# (agar Pod hali uni ishlatayotgan bo'lsa, osilib qoladi - kubernetes.io/pvc-protection finalizer)
kubectl get pv pv-vol1         # STATUS Released (Retain) yoki umuman yo'q (Delete)
```

Bilish kerak bo’lgan ikkita himoya:

- **pvc-protection**: Pod ishlatayotgan claim Pod yo’qolmaguncha
  o’chirilmaydi - `kubectl delete pvc` shunchaki kutadi (`Terminating`).
  Avval Pod’ni o’chiring; "delete osilib qoldi"ning tushuntirishi ham shu.
- **pv-protection**: xuddi shunday, bog’langan PV o’z claim’ini kutadi.

## Kengaytirish

Agar StorageClass ruxsat bersa (`allowVolumeExpansion: true`), claim’ning
`resources.requests.storage` qiymatini oshiring va volume kattalashadi (fayl
tizimi o’lchami drayverga qarab keyingi mount’da yoki online o’zgaradi).
Kichraytirish qo’llab-quvvatlanmaydi.

```bash
kubectl patch pvc myclaim -p '{"spec":{"resources":{"requests":{"storage":"2Gi"}}}}'
kubectl describe pvc myclaim | grep -i condition -A3
```

## Odatiy ketma-ketlik, boshidan oxirigacha

```bash
kubectl apply -f pv.yaml && kubectl get pv             # Available
kubectl apply -f pvc.yaml && kubectl get pvc           # Bound, VOLUME = o'sha PV
kubectl apply -f pod.yaml && kubectl get pod           # Running
kubectl exec webapp -- sh -c 'echo hi > /log/test && cat /log/test'
kubectl delete pod webapp && kubectl apply -f pod.yaml
kubectl exec webapp -- cat /log/test                   # hali joyida - persistence shu
```

## O’zingizni tekshiring

1. 1Gi claim 5Gi PV’ga bog’landi. Pod qanchasidan foydalana oladi va
   qolganini boshqa claim ola oladimi?
2. Pod PVC’ga murojaat qiladi; PVC esa Pending. Pod qaysi holatda bo’ladi va
   siz qayerga qaraysiz?
3. `kubectl delete pvc` Terminating’da turib qoldi. Nega va nima qilasiz?
