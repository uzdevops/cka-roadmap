## Har bir obyektda bir xil to’rtta yuqori darajali maydon bor

Pod bo’ladimi, NetworkPolicy yoki CustomResource - shakli bir xil:

```yaml
apiVersion: apps/v1        # qaysi API guruhi va versiyasi
kind: Deployment           # o'sha guruhdagi qaysi tur
metadata:                  # kimligi: nom, namespace, label'lar, annotation'lar
  name: web
  namespace: default
  labels:
    app: web
spec:                      # kutilgan holat - buni siz yozasiz
  replicas: 3
status:                    # kuzatilgan holat - buni tizim yozadi
  readyReplicas: 3
```

`status`’ni siz hech qachon yozmaysiz. Uni manifestga qo’shsangiz, e’tiborga
olinmaydi.

## apiVersion: guruh va versiyani o’qish

```text
apiVersion: v1              -> core group (no name), version v1
apiVersion: apps/v1         -> group "apps", version v1
apiVersion: batch/v1        -> group "batch", version v1
apiVersion: networking.k8s.io/v1
apiVersion: rbac.authorization.k8s.io/v1
```

Eng ko’p ahamiyatga egalari:

| Kind | apiVersion |
| --- | --- |
| Pod, Service, ConfigMap, Secret, Namespace, PersistentVolume(Claim), ServiceAccount | `v1` |
| Deployment, ReplicaSet, StatefulSet, DaemonSet | `apps/v1` |
| Job, CronJob | `batch/v1` |
| Ingress, NetworkPolicy | `networking.k8s.io/v1` |
| Role, RoleBinding, ClusterRole, ClusterRoleBinding | `rbac.authorization.k8s.io/v1` |
| HorizontalPodAutoscaler | `autoscaling/v2` |

:::tip
Bu jadvalni hech qachon yodlamang. `kubectl api-resources` uni sizning aniq
klasteringiz uchun chiqaradi - qisqa nomlar va tur namespaced’mi yoki yo’qmi,
shular bilan birga:

```bash
kubectl api-resources | grep -i ingress
# ingresses  ing  networking.k8s.io/v1  true  Ingress
```
:::

## metadata: nomdan ko’proq narsa

```yaml
metadata:
  name: web                       # (namespace, kind) ichida yagona
  namespace: production
  labels:                         # aniqlovchi, tanlash mumkin
    app: web
    tier: frontend
    environment: production
  annotations:                    # tavsiflovchi, tanlab bo'lmaydi
    kubernetes.io/change-cause: "upgrade to 1.28"
    owner: platform-team@example.com
```

Bu farqni imtihon tekshiradi: **label’lar - tanlash uchun, annotation’lar -
ma’lumot uchun.** Pod’larni label bo’yicha tanlay olasiz; annotation bo’yicha
tanlay olmaysiz.

## Namespaced va cluster-scoped

```bash
kubectl api-resources --namespaced=true    | head
kubectl api-resources --namespaced=false   | head
```

Cluster-scoped obyektlar (namespace’siz): Node, PersistentVolume, Namespace,
ClusterRole, ClusterRoleBinding, StorageClass, CustomResourceDefinition.

:::warning
Cluster-scoped obyektda `metadata.namespace`’ni ko’rsatish - xato; namespaced
obyektda esa uni tushirib qoldirish jimgina joriy kontekstingizning
namespace’ini ishlatadi - u savolda so’ralgani bo’lmasligi mumkin. Imtihonda
kontekstga tayanmasdan, har doim `-n`’ni aniq yozing.
:::

## Ishonsa bo’ladigan YAML yozish

YAML otstuplarga sezgir va kechirimsiz. Uchta qoida xatolarning ko’pchiligini
oldini oladi:

1. **Faqat bo’shliq, hech qachon tab emas.** Tab - parse xatosi.
2. **Har bir daraja uchun ikkita bo’shliq**, izchil ravishda.
3. **`-` ro’yxat elementini boshlaydi**, o’z kaliti ostida otstup bilan.

```yaml
spec:
  containers:           # ro'yxat
    - name: web         # birinchi element
      image: nginx:1.27
      ports:
        - containerPort: 80
      env:
        - name: LOG_LEVEL
          value: "debug"
    - name: sidecar     # ikkinchi element
      image: busybox
```

Tez-tez uchraydigan xato - `containerPort`’ni ro’yxat o’rniga map sifatida
yozish:

```yaml
# NOTO'G'RI
ports:
  containerPort: 80

# TO'G'RI
ports:
  - containerPort: 80
```

## Bitta faylda bir nechta hujjat

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: demo
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: settings
  namespace: demo
data:
  LOG_LEVEL: debug
```

`kubectl apply -f file.yaml` ikkalasini ham tartib bilan yaratadi.

## explain bilan maydonlarni topish

Bu - yodlashning o’rnini bosadigan ko’nikma.

```bash
kubectl explain pod
kubectl explain pod.spec.containers
kubectl explain pod.spec.containers.livenessProbe
kubectl explain pod.spec.securityContext --recursive
kubectl explain deployment.spec.strategy.rollingUpdate
```

Chiqish maydon turini va uning majburiy yoki majburiy emasligini aytadi:

```text
FIELD: containerPort <integer> -required-

DESCRIPTION:
    Number of port to expose on the pod's IP address.
```

## apply’dan oldin tekshiring

```bash
kubectl apply -f manifest.yaml --dry-run=server    # to'liq server tomonidagi tekshiruv
kubectl apply -f manifest.yaml --dry-run=client    # lokal, tezroq, kamroq puxta
kubectl diff -f manifest.yaml                      # nima o'zgarishini ko'rsatadi
```

:::exam-tip
`--dry-run=server` admission webhook rad etishlarini va klient tomonidagi
tekshiruv o’tkazib yuboradigan sxema xatolarini ushlaydi. Manifest "to’g’ri
ko’rinsa" ham imtihon topshirig’i baribir bajarilmasa, faylni qayta yozishga
kirishishdan oldin uni server tomonida ishga tushiring.
:::

## Label’lar haqiqiy selector bilan bog’langanda

Deployment’ning selector’i bilan uning Pod template’idagi label’lar orasidagi
bog’liqlik - odamlar qiladigan eng keng tarqalgan YAML xatosi:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  selector:
    matchLabels:
      app: web        # mana bunga ...
  template:
    metadata:
      labels:
        app: web      # ... aynan mos kelishi kerak
    spec:
      containers:
        - name: web
          image: nginx:1.27
```

Agar ular mos kelmasa, API server Deployment’ni `selector does not match
template labels` xabari bilan rad etadi. Selector yaratilgandan keyin
**o’zgarmas** bo’lib qoladi - uni o’zgartirish uchun Deployment’ni o’chirib,
qaytadan yaratishingiz kerak.

## O’zingizni tekshiring

1. Label va annotation orasidagi farq nima?
2. `Ingress` namespaced’mi va qaysi API guruhida ekanini qaysi buyruq aytadi?
3. Nega `spec.selector.matchLabels` `spec.template.metadata.labels`’ga mos
   kelmaganda Deployment yaratilmaydi?
