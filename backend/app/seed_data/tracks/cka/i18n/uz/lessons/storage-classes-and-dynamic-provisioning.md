## PV’larni qo’lda yaratishni to’xtating

Statik provisioning - admin PV yozadi, foydalanuvchi PVC yozadi, ular
bog’lanadi - kimdir oldin diskni yaratib qo’yishini talab qiladi.
**StorageClass** buni teskarisiga aylantiradi: class provisioner’ni (CSI
driver’ni) va uning parametrlarini nomlaydi; claim class’ni nomlaydi; claim
paydo bo’lganda provisioner diskni va unga mos PV’ni **yaratadi**. Hech kim
PV yozmaydi.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"    # class ko'rsatilmagan claim'lar shuni oladi
provisioner: ebs.csi.aws.com          # pd.csi.storage.gke.io, disk.csi.azure.com, rbd.csi.ceph.com, ...
parameters:                            # provisioner'ga xos
  type: gp3
  iops: "3000"
reclaimPolicy: Delete                  # Delete (sukut bo'yicha) | Retain
volumeBindingMode: WaitForFirstConsumer   # Immediate (sukut bo'yicha) | WaitForFirstConsumer
allowVolumeExpansion: true
```

```bash
kubectl get sc
# NAME             PROVISIONER          RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
# fast (default)   ebs.csi.aws.com      Delete          WaitForFirstConsumer   true                   30d
# standard         kubernetes.io/no-provisioner   Retain   WaitForFirstConsumer   false              30d
```

Claim esa uni shunchaki nomlaydi:

```yaml
kind: PersistentVolumeClaim
spec:
  storageClassName: fast
  accessModes: [ReadWriteOnce]
  resources: {requests: {storage: 20Gi}}
```

```bash
kubectl apply -f pvc.yaml
kubectl get pvc          # Pending (WaitForFirstConsumer) yoki pvc-<uuid> ga Bound (Immediate)
kubectl get pv           # driver yaratgan pvc-<uuid> nomli PV paydo bo'ldi, reclaim Delete
```

## volumeBindingMode

| Rejim | PV qachon yaratiladi |
|---|---|
| `Immediate` | claim paydo bo’lishi bilanoq - provisioner tanlagan istalgan zona/node’da |
| `WaitForFirstConsumer` | faqat claim’dan foydalanuvchi **Pod** rejalashtirilganda - shunda disk Pod qayerda bo’lsa, o’sha yerda yaratiladi |

Zonaga bog’liq bulut disklari va `local` volume’lar uchun
`WaitForFirstConsumer` yagona to’g’ri tanlov: aks holda disk A zonasida
yaratiladi, Pod esa B zonasida rejalashtiriladi va uni hech qachon ulay
olmaydi. Buning birinchi safar hammani chalg’itadigan bitta ko’rinadigan
yon ta’siri bor: **Pod’i yo’q PVC Pending bo’lib turadi**,
`waiting for first consumer to be created before binding` hodisasi bilan. Bu
xato emas. Pod’ni yarating.

:::exam-tip
"PVC Pending, StorageClass esa WaitForFirstConsumer" → u Pod’ni kutyapti;
nosozlik emas. "PVC Pending, StorageClass esa Immediate" → provisioner yo’q
yoki ishlamayapti: `kubectl describe pvc` driver nomini aytadi,
`kubectl get pods -n kube-system | grep csi` uning ishlab turgan-turmaganini
ko’rsatadi.
:::

## Default class

`storageClassName` **ko’rsatilmagan** claim `DefaultStorageClass` admission
plugin’i orqali default StorageClass’ni (`is-default-class` annotatsiyasi
borini) oladi. `storageClassName: ""` (aniq qo’yilgan bo’sh satr) bo’lgan
claim esa bundan **voz kechadi** va faqat class’i yo’q PV’ga bog’lanadi - bu
statik provisioning yo’li.

```bash
kubectl get sc | grep default
kubectl patch storageclass fast -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
kubectl patch storageclass old -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
```

Bir vaqtda ikkita default bo’lishi yangi claim’lar uchun xato; nolta bo’lsa,
class ko’rsatmagan claim’lar abadiy Pending bo’lib qoladi.

## Provisioner’siz: lokal disklar uchun class

```yaml
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

Provisioner’i hech narsa yaratmaydigan class; u qo’lda yaratilgan `local`
PV’larni guruhlash va bog’lanishni Pod joylashtirilgunga qadar kechiktirish
uchun ishlatiladi (shunda scheduler diski bor node’ni tanlay oladi). Storage
labida aynan shunga duch kelasiz: PVC yarating, uning Pending turishini
kuzating, Pod yarating, bog’lanishini kuzating.

## Class’dan keladigan reclaim policy va kengaytirish

Dinamik yaratilgan PV `reclaimPolicy`’ni class’dan meros oladi - sukut
bo’yicha `Delete`, ya’ni **claim’ni o’chirish diskni ham o’chiradi**. Qayta
tiklab bo’lmaydigan ma’lumot uchun class’larga `Retain` qo’ying.
`allowVolumeExpansion: true` esa keyinchalik `kubectl patch pvc` bilan
volume’ni kattalashtirishga imkon beradi.

## O’zingizni tekshiring

1. Claim StorageClass’ni nomlaganda PersistentVolume’ni nima yaratadi va
   o’sha PV’ning nomi qanday bo’ladi?
2. PVC "waiting for first consumer" bilan Pending. Biror narsa buzilganmi?
3. `storageClassName` ko’rsatilmagan claim bilan `storageClassName: ""`
   bo’lgan claim orasidagi farq nima?
