## Namespace nima uchun kerak

Namespace - bu nomlar uchun soha va ustiga siyosat biriktiriladigan nuqta.
Ikkita Pod har xil namespace’da bo’lsa, ikkalasi ham `web` deb atalishi
mumkin. RBAC Role’lari, ResourceQuota, LimitRange va NetworkPolicy’lar
hammasi namespace bo’yicha qo’llanadi.

Namespace nima **emas**: u o’zicha xavfsizlik chegarasi emas.
NetworkPolicy’larsiz `dev` dagi Pod `prod` dagi Pod’ga to’g’ridan-to’g’ri IP
orqali yeta oladi.

```bash
kubectl get namespaces
# NAME              STATUS   AGE
# default           Active   10d
# kube-node-lease   Active   10d
# kube-public       Active   10d
# kube-system       Active   10d
```

- `default` - boshqacha aytmasangiz, obyektlaringiz shu yerga tushadi.
- `kube-system` - control plane addon’lari: CoreDNS, kube-proxy, CNI.
- `kube-public` - hamma o’qiy oladi; klaster bootstrap ma’lumotini saqlaydi.
- `kube-node-lease` - node holatini kuzatish uchun ishlatiladigan node
  heartbeat Lease obyektlari.

## Namespace yaratish va ishlatish

```bash
kubectl create namespace dev
kubectl create ns dev --dry-run=client -o yaml > ns.yaml
```

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dev
  labels:
    environment: development
```

```bash
kubectl get pods -n dev
kubectl get pods --all-namespaces        # yoki -A
kubectl apply -f app.yaml -n dev
```

:::warning
`kubectl delete namespace dev` **uning ichidagi hamma narsani** o’chiradi va
hech qanday tasdiqlash so’ralmaydi. Umumiy yoki imtihon klasterida avval
ichida nima borligini tekshiring:

```bash
kubectl get all -n dev
```
:::

## Context’lar: boshqa hech qachon -n yozmaslik

Context klaster, foydalanuvchi va sukut bo’yicha namespace’ni bog’laydi.

```bash
kubectl config get-contexts
kubectl config current-context
kubectl config use-context kind-cka
kubectl config set-context --current --namespace=dev
kubectl config view --minify | grep namespace
```

:::exam-tip
Imtihon savollari namespace’ni odamlar sezganidan ancha ko’p ko’rsatadi va
tekshiruvchi namespace’ni nazorat qiladi. Sizni ikkita odat himoya qiladi:
savol boshida context’da namespace’ni belgilang **va** shundan keyin ham
obyektni yaratadigan buyruqda `-n` ni aniq yozing. Ikki qavat ehtiyot uch
soniya turadi.
:::

## Klaster darajasidagi obyektlarda namespace bo’lmaydi

```bash
kubectl api-resources --namespaced=false
# NAME                  SHORTNAMES  APIVERSION  NAMESPACED  KIND
# namespaces            ns          v1          false       Namespace
# nodes                 no          v1          false       Node
# persistentvolumes     pv          v1          false       PersistentVolume
# storageclasses        sc          storage.k8s.io/v1  false  StorageClass
# clusterroles          ...         rbac.authorization.k8s.io/v1  false  ClusterRole
```

Odamlarni chalg’itadigan assimetriyaga e’tibor bering:
**PersistentVolume klaster darajasida, PersistentVolumeClaim esa namespace
darajasida.** `Role` (namespace’li) va `ClusterRole` (namespace’siz) ham
shunday.

## Namespace’lararo DNS

Service DNS nomlari namespace’ni o’zida saqlaydi:

```text
<service>.<namespace>.svc.cluster.local
```

`dev` dagi Pod’dan:

```bash
curl http://api                       # dev'dagi api (bir xil namespace)
curl http://api.prod                  # prod'dagi api
curl http://api.prod.svc.cluster.local
```

Qisqa shakl `/etc/resolv.conf` dagi qidiruv domenlari tufayli ishlaydi:

```bash
kubectl exec -it mypod -- cat /etc/resolv.conf
# search dev.svc.cluster.local svc.cluster.local cluster.local
# nameserver 10.96.0.10
```

## ResourceQuota

Namespace’dagi umumiy iste’molni cheklaydi.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dev-quota
  namespace: dev
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "20"
    persistentvolumeclaims: "5"
    services.loadbalancers: "1"
```

```bash
kubectl create quota dev-quota --hard=cpu=4,memory=8Gi,pods=20 -n dev
kubectl describe quota -n dev
```

:::warning
Namespace’da `requests.cpu` yoki `limits.memory` ni belgilaydigan
ResourceQuota paydo bo’lgach, u yerda yaratiladigan **har bir** Pod o’sha
maydonlarni belgilashi shart. Ularsiz Pod’lar butunlay rad etiladi:

`Error: failed quota: dev-quota: must specify limits.memory`

Bu imtihonning sevimli stsenariylaridan biri: birorta ham Pod yaratmaydigan
Deployment, sababi esa faqat ReplicaSet hodisalarida ko’rinadi, Deployment’da
emas.

```bash
kubectl describe rs <replicaset-name> -n dev
```
:::

## LimitRange

Har bir obyekt uchun sukut qiymatlar va chegaralar beradi - kvotani har bir
manifestni tahrirlamasdan ishlatib bo’ladigan qilish usuli shu.

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: dev-limits
  namespace: dev
spec:
  limits:
    - type: Container
      default:                 # yozilmaganda limits sifatida qo'llanadi
        cpu: 500m
        memory: 512Mi
      defaultRequest:          # yozilmaganda requests sifatida qo'llanadi
        cpu: 100m
        memory: 128Mi
      max:
        cpu: "2"
        memory: 2Gi
      min:
        cpu: 50m
        memory: 64Mi
```

Bu joyida turganda hech narsa belgilamagan Pod ham request va limit oladi,
demak kvotani qanoatlantiradi.

## Terminating holatida qotib qolgan namespace

```bash
kubectl get ns dev -o json | jq '.status'
# {"conditions": [...], "phase": "Terminating"}
```

Odatda ikkitasidan biri: yakunlana olmaydigan finalizer’li resurs yoki
discovery’ni to’sib turgan ishlamayotgan APIService.

```bash
kubectl api-resources --verbs=list --namespaced -o name \
  | xargs -n1 kubectl get -n dev --ignore-not-found

kubectl get apiservice | grep -v True    # sog'lom bo'lmagan agregatsiyalangan API
```

## O’zingizni tekshiring

1. Bulardan qaysilari namespace darajasida: PersistentVolume,
   PersistentVolumeClaim, Role, ClusterRole, StorageClass?
2. Kvota bilan cheklangan namespace’dagi Deployment birorta Pod yaratmayapti.
   Xato xabari qayerda?
3. `dev` dagi Pod’dan `prod` dagi `api` Service’iga qaysi DNS nom yetadi?
