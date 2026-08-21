## Storage klaster resursi sifatida

`nfs:` yoki `csi:` tafsilotlarini har bir Pod spec’iga yozish har bir
dasturchidan storage qayerdaligini bilishni talab qiladi, uni o’zgartirish esa
har bir Pod’ni tahrirlash demak. Kubernetes ikki tomonni ajratadi:

- administrator **PersistentVolume**larni yaratadi - o’lchami, access
  mode’lari va backend’i bo’lgan storage bo’laklari, klaster miqyosidagi
  obyektlar sifatida;
- foydalanuvchi **PersistentVolumeClaim** yaratadi - "menga 5Gi, o’qish-yozish
  kerak" - va Kubernetes uni mos PV’ga bog’laydi;
- Pod esa claim’ga murojaat qiladi.

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-vol1
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual            # ixtiyoriy; claim mos kelishi kerak bo'lgan yorliq
  hostPath:                           # backend - istalgan volume turi: nfs, csi, local, ...
    path: /tmp/data
    type: DirectoryOrCreate
```

```bash
kubectl apply -f pv.yaml
kubectl get pv
# NAME      CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM   STORAGECLASS   AGE
# pv-vol1   1Gi        RWO            Retain           Available           manual         5s
```

PV’lar **namespace’ga tegishli emas** - ular klaster hovuzi; (namespace’li)
claim’lar esa o’shandan oladi.

## Access mode’lar

| Mode | Qisqasi | Ma’nosi |
|---|---|---|
| `ReadWriteOnce` | RWO | **bitta node** tomonidan o’qish-yozish uchun mount qilinadi (o’sha node’dagi istalgan sondagi Pod) |
| `ReadOnlyMany` | ROX | ko’p node tomonidan faqat o’qish uchun mount qilinadi |
| `ReadWriteMany` | RWX | ko’p node tomonidan o’qish-yozish uchun mount qilinadi - umumiy fayl tizimi kerak (NFS, CephFS), blok disk emas |
| `ReadWriteOncePod` | RWOP | qat’iy ravishda bitta **Pod** |

Blok disk (EBS, lokal SSD) - RWO; tarmoq fayl tizimi RWX bo’la oladi. RWX
so’ragan claim faqat RWO’li PV’ga hech qachon bog’lanmaydi - claim Pending
bo’lib turganda birinchi tekshiriladigan narsa shu.

## Reclaim policy

Claim’i o’chirilganda PV’ga nima bo’ladi:

| Siyosat | Keyin |
|---|---|
| `Retain` | PV `Released` bo’ladi; ma’lumot saqlanadi; uni qayta ishlatishdan oldin admin tozalashi kerak (PV’ni o’chirish, backend’ni tozalash yoki qoldirish) |
| `Delete` | PV **va uning orqasidagi storage** o’chiriladi - dinamik ta’minlangan volume’lar uchun sukut bo’yicha |
| `Recycle` | eskirgan; kontentni `rm -rf` qiladi va uni yana Available holatga qaytaradi |

`Retain` - qo’lda yaratgan har qanday narsangiz uchun xavfsiz sukut.
`Released` holati odamlarni chalg’itadi: PV Available emas, unga yangi claim
bog’lanmaydi va `kubectl get pv` uni eski CLAIM bilan ko’rsatadi. Uni qayta
ishlatish uchun PV’ni o’chirib, qaytadan yarating (`hostPath` yoki NFS
backend’idagi ma’lumot bundan omon qoladi).

## Holat

```
Available  -> Bound (claim'ga)  -> Released (claim o'chdi, Retain)  -> yo'q
                                -> o'chdi (claim o'chdi, Delete)
Failed     (tiklash muvaffaqiyatsiz)
```

```bash
kubectl describe pv pv-vol1
kubectl get pv pv-vol1 -o jsonpath='{.spec.claimRef}'     # uni qaysi claim egallagan
```

## Statik va dinamik

PV obyektlarini qo’lda yozish - bu **statik provisioning**: bir nechta NFS
export yoki lokal disk uchun bo’ladi, yuzta jamoa uchun esa imkonsiz.
**Dinamik provisioning** - claim paydo bo’lganda talab bo’yicha PV yaratadigan
StorageClass - CSI driver’i bor har qanday klasterda odatiy hol va u PVC’lardan
keyingi dars. PV obyekti ikkala holatda ham bir xil; faqat uni kim yaratishi
farq qiladi.

:::exam-tip
Imtihonning PV topshiriqlari sizga raqamlarni beradi - nom, o’lcham, access
mode, hostPath, reclaim policy, ba’zan storageClassName. Ularni aynan yozing;
keyingi qadamdagi claim faqat o’lcham ≤ sig’im bo’lsa, mode’lar mos kelsa va
class nomi aynan o’sha satr bo’lsa (yoki ikkalasi ham bo’sh bo’lsa)
bog’lanadi. Shundan keyin `kubectl get pv` `Bound` ko’rsatadi - isbot shu.
:::

## O’zingizni tekshiring

1. PersistentVolume namespace’ga tegishlimi? Uni odatda kim yaratadi?
2. Claim `ReadWriteMany` so’rayapti; yagona PV esa `ReadWriteOnce`. Nima
   bo’ladi?
3. Claim’i o’chirilgandan keyin `Retain` PV `Released` ko’rsatyapti. Unga
   yangi claim bog’lana oladimi? Siz nima qilasiz?
