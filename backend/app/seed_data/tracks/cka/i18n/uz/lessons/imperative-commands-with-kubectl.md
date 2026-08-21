## Imtihonni yutadigan cheat sheet

Imtihonda YAML’ni qo’lda yozishga sarflagan har bir daqiqangiz - ballarning
30 % ini beradigan nosozlikni bartaraf etish qismidan yutqazgan daqiqa. Bu
sahifadagi buyruqlar to’g’ri obyektlarni bitta qatorda yaratadi. Ularni
refleksga aylanguncha o’rganing.

### Avval shell’ni sozlang

```bash
alias k=kubectl
export do="--dry-run=client -o yaml"      # k run x --image=nginx $do > x.yaml
export now="--force --grace-period 0"     # k delete pod x $now
source <(kubectl completion bash); complete -o default -F __start_kubectl k
```

### Pod’lar

```bash
k run nginx --image=nginx                                    # Deployment emas, Pod
k run nginx --image=nginx --port=80 --expose                 # Pod + ClusterIP Service
k run redis --image=redis:alpine -l tier=db                  # label'lar bilan
k run busy --image=busybox --command -- sleep 3600           # buyruqni almashtirish
k run busy --image=busybox -- --color=green                  # faqat argument uzatish
k run tmp --rm -it --image=busybox -- sh                     # bir martalik shell, chiqishda o'chadi
k run tmp --rm -it --image=busybox --restart=Never -- wget -qO- http://web   # bir martalik test
k run nginx --image=nginx $do > pod.yaml                     # generatsiya qiling, keyin tahrirlang
```

### Deployment’lar

```bash
k create deployment web --image=nginx --replicas=3
k create deployment web --image=nginx --replicas=3 --port=80 $do > deploy.yaml
k scale deployment web --replicas=5
k set image deployment/web nginx=nginx:1.27
k rollout status deployment/web
k rollout history deployment/web
k rollout undo deployment/web
k rollout undo deployment/web --to-revision=2
```

### Service’lar

```bash
k expose deployment web --port=80 --target-port=8080                       # ClusterIP
k expose deployment web --name=web-np --type=NodePort --port=80            # NodePort, tasodifiy port
k expose pod redis --name=redis-service --port=6379                        # Pod'dan
k create service clusterip web --tcp=80:8080 $do                           # maqsad obyektsiz
k create service nodeport web --tcp=80:8080 --node-port=30080 $do          # bayroq bilan nodePort qo'yishning yagona yo'li
```

### Namespace’lar, ConfigMap’lar, Secret’lar, ServiceAccount’lar

```bash
k create namespace dev
k create configmap app-cfg --from-literal=COLOR=blue --from-literal=MODE=prod
k create configmap app-cfg --from-file=config.properties
k create secret generic db --from-literal=password=hunter2
k create secret docker-registry regcred --docker-server=reg.io --docker-username=u --docker-password=p
k create secret tls web-tls --cert=tls.crt --key=tls.key
k create serviceaccount builder
k create token builder
```

### RBAC

```bash
k create role dev --verb=get,list,create --resource=pods,deployments -n dev
k create rolebinding dev-binding --role=dev --user=ahmad -n dev
k create clusterrole node-reader --verb=get,list,watch --resource=nodes
k create clusterrolebinding node-reader-b --clusterrole=node-reader --user=ahmad
k auth can-i create pods --as ahmad -n dev
```

### Job’lar, CronJob’lar, Ingress, kvotalar

```bash
k create job hello --image=busybox -- echo hello
k create cronjob hello --image=busybox --schedule="*/5 * * * *" -- echo hello
k create ingress web --rule="shop.example.com/=web:80" --rule="/api=api:8080"
k create quota dev-quota --hard=pods=10,requests.cpu=4 -n dev
k create priorityclass high --value=100000
```

### Namespace’lar va context’lar

```bash
k config get-contexts
k config use-context cluster2
k config set-context --current --namespace=dev        # -n yozishni bas qiling
k get pods -A                                         # barcha namespace'lar
```

### Ma’lumotni tez olish

```bash
k get pods -o wide
k get pod web -o yaml
k get pods --show-labels
k get pods -l app=web,tier=frontend
k get pods --field-selector=status.phase=Pending
k get events --sort-by=.lastTimestamp | tail
k describe pod web | tail -20
k explain pod.spec.containers.livenessProbe
k api-resources | grep -i netpol
k get pods -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName
k get pods --sort-by=.metadata.creationTimestamp
```

:::exam-tip
`kubectl create/run/expose` bayroqlar orqali **qila olmaydigan** narsalar -
`expose`’da nodePort qo’yish, volume, probe, resources, toleration, ikkinchi
konteyner, init konteyner qo’shish. Bularning hammasi uchun: `$do` bilan
generatsiya qiling, faylni tahrirlang, apply qiling. Topshiriq shu chiziqning
qaysi tomonida ekanini bilish qaror qabul qilish vaqtini tejaydi.
:::

:::tip
`k create <kind> --help` har bir bayroqni misol bilan ko’rsatadi. Imperativ
buyruqlar uchun u hujjatlardan tezroq va doim shu yerda turadi.
:::

## O’zingizni tekshiring

1. Pod **va** unga ClusterIP Service yaratadigan bir qatorli buyruqni yoddan
   yozing.
2. YAML tahrirlamasdan *aniq* node port bilan NodePort Service’ni qaysi
   buyruq yaratadi?
3. `kubectl run` bayroq orqali qo’ya olmaydigan uchta narsani ayting va
   o’rniga nima qilishingizni tushuntiring.
