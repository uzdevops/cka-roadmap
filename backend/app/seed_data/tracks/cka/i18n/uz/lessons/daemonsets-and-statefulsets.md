## Har bir node’da bitta nusxa

Ba’zi narsalar har bir node’da ishlashi shart, ko’p ham emas, kam ham emas:
CNI plugin, kube-proxy, log yig’uvchi, metrikalar uchun node-exporter, storage
driver’i. Deployment buni va’da qila olmaydi - u *son*ni va’da qiladi.
**DaemonSet** esa *har node’ga bitta Pod*ni va’da qiladi va klasterga yangi
node qo’shilganda yana bittasini avtomatik qo’shadi.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
      containers:
        - name: fluentd
          image: fluentd:v1.16
```

ReplicaSet bilan bir xil shakl - selector va shablon - lekin **`replicas`
yo’q**: node soni *aynan* replika soni bo’ladi.

```bash
kubectl get ds -A
# NAMESPACE     NAME         DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR
# kube-system   kube-proxy   3         3         3       3            3           kubernetes.io/os=linux
# kube-flannel  kube-flannel 3         3         3       3            3           <none>
kubectl describe ds kube-proxy -n kube-system
```

## U qanday rejalashtiriladi

Kubernetes 1.12 dan beri DaemonSet Pod’lari hammaday **default scheduler**
orqali o’tadi - DaemonSet kontrolleri shunchaki har bir node uchun bittadan
Pod yaratadi va unga `kubernetes.io/hostname=<that node>` uchun majburiy node
affinity qo’yadi. Bu shuni anglatadi:

- taint’lar amal qiladi: control plane node’larida ishlashi shart bo’lgan
  DaemonSet yuqoridagi toleration’ga muhtoj (kube-proxy va CNI DaemonSet’lari
  uni olib yuradi);
- shablondagi `nodeSelector` va node affinity qaysi node’lar nusxa olishini
  cheklaydi ("faqat Linux node’lar", "faqat `monitoring=true` bo’lgan
  node’lar");
- resurs request’lari hisobga olinadi - Pod sig’maydigan darajada to’lgan node
  Pending DaemonSet Pod’ini ko’rsatadi, bu esa foydali signal.

## Uni tez yozish

`kubectl create daemonset` degan buyruq yo’q. Deployment generatsiya qiling va
uni tuzating:

```bash
kubectl create deployment fluentd --image=fluentd:v1.16 -n kube-system $do > ds.yaml
# ds.yaml da: kind: DaemonSet ; replicas: va strategy: qatorlarini o'chiring
kubectl apply -f ds.yaml
```

:::exam-tip
Uchta tahrir - `kind`, `replicas`ni olib tashlash, `strategy`ni olib tashlash -
yigirma soniya oladi. `replicas`ni unutsangiz, validatsiya xatosi aynan shu
maydonni nomlab beradi, ya’ni xatoning ham narxi arzon.
:::

## Yangilash

`updateStrategy` sukut bo’yicha `RollingUpdate` (bir vaqtda bitta node,
`maxUnavailable: 1`) yoki `OnDelete` (yangi Pod’lar faqat siz eskilarini
o’chirganingizda) bo’ladi. `kubectl rollout status ds/fluentd -n kube-system`
Deployment’lardagidek ishlaydi.

## Va taqqoslash uchun StatefulSet’lar

**StatefulSet** - "Deployment emas" toifasidagi ikkinchi workload: tartiblangan,
nomlangan replikalar (`db-0`, `db-1`, `db-2`), ularning har biri o’z
PersistentVolume’ini va headless Service orqali o’z barqaror DNS nomini
saqlaydi. Ma’lumotlar bazalari, broker’lar, replika identifikatsiyasi muhim
bo’lgan hamma narsa. Batafsili - storage bosqichining mavzusi; hozircha esda
tutiladigan bir qatorli farq:

| | Deployment | DaemonSet | StatefulSet |
|---|---|---|---|
| nechta | `replicas` | har node’ga bitta | `replicas`, tartiblangan |
| Pod nomlari | tasodifiy suffiks | tasodifiy suffiks | `name-0`, `name-1`, ... |
| storage | umumiy yoki yo’q | odatda hostPath | har replikaga bitta PVC, saqlanadi |
| tipik qo’llanish | stateless ilovalar | node agentlari | ma’lumotlar bazalari |

## O’zingizni tekshiring

1. Nega DaemonSet’da `replicas` maydoni yo’q va klasterga yangi node
   qo’shilganda nima bo’ladi?
2. DaemonSet’ingiz worker’larda ishlayapti, lekin control plane node’ida
   ishlamayapti. Shablonda nima yetishmayapti?
3. `kubectl create deployment ... $do` dan boshlab, natijani yaroqli
   DaemonSet’ga aylantirish uchun qaysi uchta tahrir kerak?
