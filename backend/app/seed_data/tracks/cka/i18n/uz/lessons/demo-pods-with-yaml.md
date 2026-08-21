## Yo’riqnoma: Pod noldan Running holatiga va tuzatilgunicha

Bu dars - bitta to’liq ishlangan misol. Uni o’z klasteringizda takrorlang; har
bir qadam - imtihonda o’nlab marta yozadigan buyruq.

### 1. Skeletni generatsiya qiling

```bash
kubectl run web --image=nginx:1.27 --port=80 --labels=app=web,tier=frontend \
  --dry-run=client -o yaml > web.yaml
cat web.yaml
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  creationTimestamp: null
  labels:
    app: web
    tier: frontend
  name: web
spec:
  containers:
  - image: nginx:1.27
    name: web
    ports:
    - containerPort: 80
    resources: {}
  dnsPolicy: ClusterFirst
  restartPolicy: Always
status: {}
```

`creationTimestamp: null`, `resources: {}` va `status: {}`’ga e’tibor bering -
bular generator qoldirib ketadigan zararsiz shovqin. Ularni o’chirsangiz ham,
e’tiborsiz qoldirsangiz ham bo’ladi.

### 2. Uni yarating va ko’tarilishini kuzating

```bash
kubectl apply -f web.yaml
kubectl get pod web -w         # Pending -> ContainerCreating -> Running
```

```bash
kubectl get pod web -o wide    # qaysi node, qaysi IP
kubectl describe pod web       # pastdagi hodisalar: Scheduled, Pulling, Pulled, Created, Started
```

Events bo’limini bir marta sekin o’qing. O’sha besh qator - muvaffaqiyatli
yo’l; siz keyinchalik tekshiradigan har qanday Pod muammosi - shulardan
birining ishlamasligi.

### 3. Uni ataylab buzing

```bash
kubectl set image pod/web web=nginx:1.27-doesnotexist
kubectl get pod web            # STATUS: ErrImagePull, keyin ImagePullBackOff
kubectl describe pod web | tail -6
#   Warning  Failed   ...  Failed to pull image "nginx:1.27-doesnotexist": ... not found
```

`ImagePullBackOff` - o’z alohida yechimi bor xato holati emas - u "urinib
ko’rdim, bo’lmadi, qayta urinishdan oldin uzoqroq kutyapman" degani. Undan
yuqoridagi xabar - haqiqiy xato: bunday teg mavjud emas.

### 4. Uni tuzating - ikki yo’l

```bash
# a) joyida: image - Pod'ning sanoqli o'zgaruvchan maydonlaridan biri
kubectl set image pod/web web=nginx:1.27

# b) fayldan: web.yaml'ni tahrirlang, keyin
kubectl apply -f web.yaml
```

```bash
kubectl get pod web            # yana Running, RESTARTS o'zgarmagan
```

### 5. Ichiga qarang

```bash
kubectl logs web                       # nginx access/error log
kubectl exec web -- nginx -v           # konteyner ichida buyruq bajarish
kubectl exec -it web -- sh             # shell, agar image'da bo'lsa
kubectl port-forward pod/web 8080:80   # keyin o'z mashinangizdan curl localhost:8080
```

### 6. O’zgarmas narsani o’zgartiring

```bash
# jonli obyektni tahrirlab ikkinchi konteyner qo'shishga urinib ko'ring
kubectl edit pod web      # containers ostiga yana bitta yozuv qo'shing, saqlang
# error: Pod "web" is invalid: spec.containers: Forbidden: pod updates may not add or remove containers
```

Halol yechim:

```bash
kubectl get pod web -o yaml > web-full.yaml    # yoki o'z web.yaml'ingizni tahrirlang
# konteynerni faylga qo'shing
kubectl replace --force -f web-full.yaml       # bitta buyruqda o'chiradi va qayta yaratadi
```

:::exam-tip
Pod ustida `kubectl edit` - image, label’lar va bir nechta annotatsiyadan
boshqa hamma narsa uchun tuzoq: u rad etadi, ammo tahriringizni yo’lini chop
etadigan vaqtinchalik faylga saqlab qo’ygan bo’ladi.
`kubectl replace --force -f /tmp/kubectl-edit-xxxx.yaml` o’sha tahrirni oladi -
uni qaytadan qilishdan tezroq.
:::

### 7. Tozalang

```bash
kubectl delete pod web --grace-period=0 --force   # nginx to'xtashini 30 s kutmang
```

:::tip
Imtihonda har bir delete’da `--force --grace-period=0` ishlatish seans
davomida haqiqiy daqiqalarni tejaydi. Unga alias qo’ying.
:::

## O’zingizni tekshiring

1. Sog’lom Pod ishga tushishining beshta hodisasini tartibi bilan sanang.
2. `ImagePullBackOff` sizga nima deydi va haqiqiy xato qayerda turadi?
3. Ishlab turgan Podga ikkinchi konteyner qo’shishingiz kerak. Eng qisqa
   to’g’ri buyruqlar ketma-ketligi qanday?
