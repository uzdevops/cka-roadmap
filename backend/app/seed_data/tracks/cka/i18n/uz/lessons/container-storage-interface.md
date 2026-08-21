## Bu plugin emas, shartnoma

CSI - bu spetsifikatsiya: storage tizimining driver’i javob berishi shart
bo’lgan gRPC chaqiruvlari to’plami va orkestrator ularni qanday chaqirishi
qoidalari. Uni amalga oshirgan har qanday storage vendori orkestrator kodiga
tegmasdan Kubernetes bilan (shuningdek Nomad va Mesos bilan) ishlaydi;
Kubernetes narigi uchda EBS, Ceph yoki shkafdagi NAS turgan-turmaganini
bilmaydi va bu uni qiziqtirmaydi.

```
Kubernetes ──gRPC──▶ CSI driver ──vendor API──▶ the storage system
  "CreateVolume(10Gi)"         create an EBS disk / a Ceph RBD image / an NFS export
  "ControllerPublishVolume"    attach it to node01
  "NodeStageVolume"            format, mount once on the node
  "NodePublishVolume"          bind-mount into the Pod's path
  "DeleteVolume"               tear it down
```

Chaqiruvlar juftlashadi: create/delete, attach/detach (controller tomonida
publish/unpublish), node tomonida stage/unstage va publish/unpublish. Driver
o’z storage’i qila oladigan narsani amalga oshiradi - tarmoq fayl tizimida
"attach" yo’q, blok qurilmada bor - va o’z imkoniyatlarini e’lon qiladi.

## Klasterda driver qanday ko’rinadi

CSI driver’i oddiy Kubernetes workload’lari sifatida yetkaziladi:

| Qism | Nima sifatida ishlaydi | Nima qiladi |
|---|---|---|
| **controller** plugin | Deployment/StatefulSet, bitta yoki bir nechta replika | create/delete/attach - vendor API’si bilan gaplashadigan chaqiruvlar |
| **node** plugin | DaemonSet, har bir node’da | Pod turgan node’da mount/unmount |
| **sidecar**’lar (external-provisioner, external-attacher, node-driver-registrar, ...) | yuqoridagilar yonidagi konteynerlar | Kubernetes obyektlarini (PVC, VolumeAttachment) CSI chaqiruvlariga aylantiradi |

```bash
kubectl get pods -n kube-system | grep -i csi
# ebs-csi-controller-...        5/5
# ebs-csi-node-...              3/3   (har node uchun bitta)
kubectl get csidriver
# NAME              ATTACHREQUIRED   PODINFOONMOUNT   STORAGECAPACITY   MODES
# ebs.csi.aws.com   true             false            true              Persistent
kubectl describe csinode node01          # bu node qaysi driver'larni ro'yxatdan o'tkazgan
```

Sidecar’lar - eng aqlli qism: ularni Kubernetes loyihasi bir marta yozgan,
vendor esa faqat gRPC xizmatini yozadi. Driver’lar ekotizimini mumkin qilgan
narsa ham shu.

## Kubernetes undan qanday foydalanadi

Siz CSI driver’ini hech qachon o’zingiz chaqirmaysiz. Siz **StorageClass**ni
nomlaydigan **PersistentVolumeClaim** yaratasiz; StorageClass driver nomi
bo’lgan `provisioner`ni nomlaydi; external-provisioner sidecar’i claim’ni
ko’radi va `CreateVolume` ni chaqiradi; claim’ingizga bog’langan
**PersistentVolume** paydo bo’ladi; claim’dan foydalanadigan Pod node’ga
tushganda attacher va node plugin’i uni mount qiladi. Keyingi darslar bu
obyektlarni birma-bir - volume’lar, PV’lar, PVC’lar, StorageClass’lar - ko’rib
chiqadi, bularning hammasi ostidagi mexanizm esa shu.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
provisioner: ebs.csi.aws.com          # <- CSI driver'ining nomi
parameters:
  type: gp3
```

CSI driver yaratgan PV buni o’zida yozib qo’yadi:

```yaml
spec:
  csi:
    driver: ebs.csi.aws.com
    volumeHandle: vol-0abc123          # disk uchun vendor ID'si
    fsType: ext4
```

## In-tree va undan ko’chish

Eskiroq manifestlarda PV’da `spec.awsElasticBlockStore:` yoki
`spec.gcePersistentDisk:` uchraydi - bular in-tree plugin’lar. Ular so’nggi
relizlardan olib tashlangan; `CSIMigration` ishi ular olib tashlanayotgan
paytda eski maydon nomlarini shaffof tarzda CSI driver’iga yo’naltirgan edi.
Hozirgi klasterda CSI’ni (StorageClass orqali) yoki doim in-tree bo’lib
qoladigan asoslarni yozing: `hostPath`, `local`, `nfs`, `emptyDir`,
`configMap`, `secret`.

:::exam-tip
Imtihon sizdan CSI driver o’rnatishni so’ramaydi. U StorageClass’ning
`provisioner`i driver nomini berishini, `kubectl get sc` qaysilari borligini
ko’rsatishini va provisioner’i ishlamayotgan class bilan Pending qolgan PVC
shundayligicha qolishini bilishingizni kutadi - `kubectl describe pvc`
"waiting for a volume to be created, either by external provisioner ... or
manually" deydi.
:::

## O’zingizni tekshiring

1. Bir gapda: CSI nima va uni kim amalga oshiradi?
2. CSI driver’i klasterda qaysi ikki xil workload sifatida ishlaydi va nega
   ikkita?
3. PVC Pending va uning hodisalarida "external provisioner" tilga olingan. U
   nimani kutyapti?
