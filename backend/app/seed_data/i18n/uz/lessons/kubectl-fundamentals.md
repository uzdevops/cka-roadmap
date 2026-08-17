## Ming marta yozadigan buyruq

`kubectl` izchil grammatikaga amal qiladi. Buyruqlar ro'yxatini emas,
grammatikani o'rganing.

```text
kubectl <fe'l> <resurs-turi> <nom> [bayroqlar]
        get     pods           web    -n prod -o wide
```

## Holatni o'qish

```bash
kubectl get pods                          # joriy namespace
kubectl get pods -A                       # barcha namespace'lar
kubectl get pods -o wide                  # + node, pod IP, nominated node
kubectl get pods -w                       # o'zgarishlarni jonli kuzatish
kubectl get pods --show-labels
kubectl get pods -l app=web,tier!=cache   # label selector
kubectl get pods --field-selector status.phase=Running
kubectl get all -n kube-system            # keng tarqalgan turlar birdaniga
```

Saralash va maxsus ustunlar `get`ni hisobot vositasiga aylantiradi:

```bash
kubectl get pods --sort-by=.status.startTime
kubectl get nodes --sort-by=.metadata.name

kubectl get pods -o custom-columns=\
'NAME:.metadata.name,NODE:.spec.nodeName,IMAGE:.spec.containers[*].image'

# Skriptlash uchun JSONPath
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.podIP}{"\n"}{end}'
```

:::exam-tip
Savollarda ko'pincha "natijani `/opt/answer.txt` faylga yozing" deyiladi.
Buyruqni tuzing, chiqishni ekranda tekshiring, **keyin** `> /opt/answer.txt`
qo'shing. Ballar noto'g'ri buyruqdan ko'ra ko'proq xato xabari yozilgan
fayllar tufayli yo'qoladi.
:::

## Describe: nosozlik aniqlashning birinchi qadami

`kubectl get` sizga maydonlarni ko'rsatadi. `kubectl describe` maydonlarni
**va hodisalarni** ko'rsatadi - nosozlik sababi aynan o'sha yerda yashaydi.

```bash
kubectl describe pod web-5d4f8b6c9-abcde
kubectl describe node cka-worker
kubectl describe svc web
```

Chiqishning eng pastki qismi - eng muhimi:

```text
Events:
  Type     Reason     Age   From               Message
  ----     ------     ----  ----               -------
  Normal   Scheduled  2m    default-scheduler  Successfully assigned default/web to cka-worker
  Normal   Pulling    2m    kubelet            Pulling image "nginx:1.27"
  Warning  Failed     1m    kubelet            Failed to pull image: not found
  Warning  BackOff    30s   kubelet            Back-off pulling image "nginx:1.27"
```

## Loglar

```bash
kubectl logs web-5d4f8b6c9-abcde
kubectl logs web-5d4f8b6c9-abcde -c sidecar      # aniq konteyner
kubectl logs -f deployment/web                   # Deployment orqali kuzatish
kubectl logs --previous web-5d4f8b6c9-abcde      # endigina qulagan konteyner
kubectl logs -l app=web --tail=50 --all-containers
kubectl logs --since=10m web-5d4f8b6c9-abcde
```

:::tip
`--previous` - CrashLoopBackOff'ni hal qiladigan bayroq. Joriy konteyner
endigina ishga tushgan va foydali chiqish bermagan; *oldingisi* esa o'lgan va
xato izini chop etgan.
:::

## Exec va port-forward

```bash
kubectl exec -it web-5d4f8b6c9-abcde -- sh
kubectl exec web-5d4f8b6c9-abcde -- env
kubectl exec web-5d4f8b6c9-abcde -c sidecar -- cat /etc/config/app.conf

kubectl port-forward svc/web 8080:80
kubectl port-forward pod/web-5d4f8b6c9-abcde 8080:80
```

Shell'i yo'q image'lar uchun (distroless, scratch) vaqtinchalik debug
konteyneridan foydalaning:

```bash
kubectl debug -it web-5d4f8b6c9-abcde --image=busybox --target=web
```

## Yaratish: avval imperativ

Imtihonda `--dry-run=client -o yaml` bilan imperativ buyruqlar YAML'ni yoddan
yozishdan sezilarli darajada tezroq.

```bash
kubectl run nginx --image=nginx --restart=Never
kubectl create deployment web --image=nginx:1.27 --replicas=3
kubectl expose deployment web --port=80 --target-port=8080 --name=web-svc
kubectl create configmap app-config --from-literal=LOG_LEVEL=debug
kubectl create secret generic db-pass --from-literal=password=s3cret
kubectl create job backup --image=busybox -- /bin/sh -c 'echo backing up'
kubectl create cronjob nightly --image=busybox --schedule='0 2 * * *' -- /bin/sh -c 'echo hi'
kubectl create serviceaccount deploy-bot
kubectl create role reader --verb=get,list --resource=pods
kubectl create rolebinding reader-bind --role=reader --serviceaccount=default:deploy-bot
```

Har qanday manifestni tayyorlaydigan usul:

```bash
kubectl create deployment web --image=nginx --dry-run=client -o yaml > web.yaml
vim web.yaml          # generator chiqara olmaydigan maydonlarni qo'shing
kubectl apply -f web.yaml
```

## O'zgartirish

```bash
kubectl apply -f manifest.yaml            # deklarativ, idempotent, afzal
kubectl edit deployment web               # $EDITOR ochadi, saqlaganda qo'llaydi
kubectl scale deployment web --replicas=5
kubectl set image deployment/web nginx=nginx:1.28
kubectl label pod web env=prod
kubectl annotate deployment web kubernetes.io/change-cause="1.28 ga o'tish"
kubectl patch deployment web -p '{"spec":{"replicas":4}}'
kubectl rollout status deployment/web
kubectl rollout undo deployment/web
```

## O'chirish

```bash
kubectl delete pod web-5d4f8b6c9-abcde
kubectl delete -f manifest.yaml
kubectl delete pods -l app=web
kubectl delete pod web --force --grace-period=0     # faqat haqiqatan qotib qolganda
```

:::warning
Deployment'ga tegishli Pod'ni o'chirish uni yo'q qilmaydi - ReplicaSet
kontrolleri bir necha soniyada o'rniga yangisini yaratadi. Workload'ni haqiqatan
olib tashlash uchun Deployment'ni o'chiring. Bu doim adashtiradigan joy.
:::

## kubectl explain: imtihon ichidagi hujjatingiz

Imtihon paytida rasmiy hujjatlardan foydalanish mumkin, lekin `explain` sayt
bo'ylab qidirishdan tezroq.

```bash
kubectl explain pod.spec
kubectl explain pod.spec.containers.resources
kubectl explain deployment.spec.strategy --recursive | head -30
kubectl api-resources                    # har bir tur, qisqa nomi va apiVersion
kubectl api-versions
```

:::exam-tip
`kubectl explain <tur> --recursive` butun maydon daraxtini chop etadi.
`securityContext.runAsUser` mi yoki `securityContext.runAsUserName` mi degan
savolga terminalni tark etmasdan ikki soniyada javob beradi.
:::

## Foydali qisqartmalar

| To'liq | Qisqa |
| --- | --- |
| pods | po |
| deployments | deploy |
| services | svc |
| namespaces | ns |
| configmaps | cm |
| persistentvolumeclaims | pvc |
| statefulsets | sts |
| daemonsets | ds |
| replicasets | rs |
| serviceaccounts | sa |

## O'zingizni tekshiring

1. Pod nega rejalashtirilmaganini qaysi buyruq ko'rsatadi?
2. Allaqachon qulab qayta ishga tushgan konteynerning loglarini qanday o'qiysiz?
3. 3 replikali nginx Deployment YAML'ini uni yaratmasdan generatsiya qiling.
