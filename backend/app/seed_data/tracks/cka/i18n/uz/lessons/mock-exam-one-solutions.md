## Mock imtihon 1 - yechimlar

Har biri uchun: tez yo’l, tekshiruv, tuzoq.

### 1. nginx-pod

```bash
k run nginx-pod --image=nginx:alpine
k get pod nginx-pod
```

Tuzoq: `nginx:alpine`, `nginx` emas. Baholovchi image satrini tekshiradi.

### 2. label bilan messaging

```bash
k run messaging --image=redis:alpine -l tier=msg
k get pod messaging --show-labels
```

Tuzoq: `--labels` ham ishlaydi; `run`’dagi `-l` label qo’yadi (`get`’da esa
filtrlaydi).

### 3. Namespace

```bash
k create ns apx-x9984574
```

Tuzoq: nomni nusxalab qo’ying; matn xatosi uchun qisman ball yo’q.

### 4. node’lar JSON sifatida faylga

```bash
k get nodes -o json > /opt/outputs/nodes-z3444kd9.json
cat /opt/outputs/nodes-z3444kd9.json | head
```

Tuzoq: katalog uchun avval `mkdir -p /opt/outputs` kerak bo’lishi mumkin;
fayl bo’sh emasligini tekshiring.

### 5. Pod uchun ClusterIP Service

```bash
k expose pod messaging --name=messaging-service --port=6379
k get svc messaging-service; k get ep messaging-service      # endpoint'lar bo'sh emas
```

Tuzoq: `expose pod` Pod’ning label’larini selektor sifatida avtomatik
oladi - Service’ni qo’lda yozishdan tezroq va xavfsizroq. `--target-port`
sukut bo’yicha `--port`’ga teng bo’ladi.

### 6. Deployment

```bash
k create deploy hr-web-app --image=kodekloud/webapp-color --replicas=2
k get deploy hr-web-app
```

### 7. Static Pod

```bash
k run static-busybox --image=busybox $do --command -- sleep 1000 > /etc/kubernetes/manifests/static-busybox.yaml
k get pod static-busybox-controlplane        # bir necha soniyada paydo bo'ladi, nomiga node qo'shiladi
```

Tuzoqlar: buyruqdan oldin `--command --` turishi kerak, aks holda
`sleep 1000` image’ning entrypoint’iga **args** bo’lib qoladi; fayl
**control plane node’ida**, **kubelet’ning staticPodPath**ida bo’lishi
shart (kubeadm’da `/etc/kubernetes/manifests` - ishonchingiz komil
bo’lmasa `/var/lib/kubelet/config.yaml`’ni ko’ring). Topshiriqda worker
nomlangan bo’lsa, avval o’sha yerga `ssh` qiling.

### 8. Namespace ichidagi Pod

```bash
k create ns finance            # agar mavjud bo'lmasa
k run temp-bus --image=redis:alpine -n finance
```

Tuzoq: `-n finance` `run`’da bo’lsin, faqat `get`’da emas.

### 9. Ishlamayotgan orange Pod’i

```bash
k describe pod orange            # Init:CrashLoopBackOff; init konteynerning exit kodi 127
k logs orange -c init-myservice  # sh: sleeeep: not found
k edit pod orange                # 'sleeeep' → 'sleep' ni tuzating; tahrir rad etiladi (init konteynerlar o'zgarmas) va /tmp/...yaml ga saqlanadi
k replace --force -f /tmp/kubectl-edit-xxxx.yaml
k get pod orange                 # Running 1/1
```

Tuzoq: Pod’ning joyida tahrirlanadigan maydonlari sanoqli; qolgan hamma
narsa uchun `edit` → rad etish → u yozgan vaqtinchalik fayl bilan
`replace --force`, yoki `get -o
yaml > f; vi f; replace --force -f f`. 127 exit kodi = buyruq topilmadi.

### 10. Belgilangan node porti bilan NodePort Service

```bash
k expose deploy hr-web-app --name=hr-web-app-service --type=NodePort --port=8080 $do > svc.yaml
vi svc.yaml          # ports[0] ostiga  nodePort: 30082  qo'shing
k apply -f svc.yaml
k get svc hr-web-app-service     # 8080:30082/TCP
```

Tuzoq: `expose`’da `--node-port` flagi yo’q - dry-run bilan YAML’ga
chiqaring, uni qo’shing, apply qiling. `--target-port` 8080 bo’ladi, chunki
ilova 8080 ni tinglaydi.

### 11. JSONPath osImage

```bash
k get nodes -o jsonpath='{.items[*].status.nodeInfo.osImage}' > /opt/outputs/nodes_os_x43kj56.txt
cat /opt/outputs/nodes_os_x43kj56.txt
```

Tuzoq: yo’lni eslay olmasangiz, `k get node <n> -o json | grep -i
osImage -B5` uni `status.nodeInfo` ostida ko’rsatadi.

### 12. PersistentVolume

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-analytics
spec:
  capacity:
    storage: 100Mi
  accessModes: [ReadWriteMany]
  hostPath:
    path: /pv/data-analytics
```

```bash
k apply -f pv.yaml; k get pv pv-analytics      # Available
```

Tuzoq: imperativ `create pv` yo’q; "Configure a Pod to Use a
PersistentVolume for Storage" hujjat sahifasida ko’chirib olish uchun
hostPath PV bor.

### 13. Qotib qolgan rollout’ni rollback qilish

```bash
k rollout status deploy web-front -n frontend        # qotgan: yangi ReplicaSet'ning Pod'lari ImagePullBackOff
k rollout history deploy web-front -n frontend
k rollout undo deploy web-front -n frontend
k rollout status deploy web-front -n frontend        # successfully rolled out
k get deploy web-front -n frontend                   # 3/3 AVAILABLE
```

Tuzoq: `undo` oldingi revision’ga qaytaradi; muayyan biri uchun
`--to-revision=N`. Buyruq qaytganini emas, `AVAILABLE`’ni tekshiring.

## Baholash va u nimani ko’rsatadi

| Vazifalar | Domen |
|---|---|
| 1, 2, 3, 6, 8, 10, 13 | Workload’lar va rejalashtirish - imperativ buyruqlar, Service’lar, rollout’lar |
| 7 | Klaster arxitekturasi - static Pod’lar |
| 9 | Nosozliklarni bartaraf etish - describe/loglarni o’qish, Pod’ni almashtirish |
| 4, 11 | Nosozliklarni bartaraf etish - JSONPath |
| 5, 10 | Service’lar va tarmoq |
| 12 | Saqlash |

Qatorda to’liq balldan past bo’lgan har bir narsa: shu hafta o’sha
domenning darslari va lablari.

:::exam-tip
O’n uchtasining barchasidagi naqsh: **avval imperativ, YAML faqat
maydonning flagi bo’lmaganda** (nodePort, PV, static Pod’ning buyrug’i) va
har biridan keyin **`get` bilan tekshirish**. Butun tezlik strategiyasi
shundan iborat.
:::

## O’zingizni tekshiring

1. Static Pod buyrug’ida `sleep 1000` uchun nega `--command --` kerak?
2. `expose`’da buning flagi yo’qligini hisobga olsak, muayyan nodePort’ni
   qanday qo’yasiz?
3. Init konteynerdagi 127 exit kodi sizga nima deydi?
