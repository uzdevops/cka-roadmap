## Lug’ati bor nodeSelector

Node affinity `nodeSelector` qiladigan ishni qiladi - node label’lari orqali
Pod qaysi node’larga tusha olishini cheklaydi - lekin ustiga operatorlar, OR
va talab qilish o’rniga *afzal ko’rish* imkonini qo’shadi.

```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: size
                operator: In
                values: [large, medium]
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 80
          preference:
            matchExpressions:
              - key: disktype
                operator: In
                values: [ssd]
  containers:
    - name: app
      image: data-processor:2.1
```

Ikkita uzun nomni so’zma-so’z o’qing:

| Maydon | Rejalashtirish paytida | Ishlab turganda |
|---|---|---|
| `requiredDuringSchedulingIgnoredDuringExecution` | mos kelishi shart, aks holda Pod Pending bo’lib qoladi | node’dagi label o’zgarishi uni chiqarib yubormaydi |
| `preferredDuringSchedulingIgnoredDuringExecution` | mos kelishga urinadi; bo’lmasa istalgan node’ga tushadi | xuddi shunday |

Bugun mavjud yagona variant - "IgnoredDuringExecution": affinity rejalashtirish
paytida tekshiriladi va boshqa hech qachon. (Label’lar o’zgarganda Pod’larni
chiqarib yuboradigan `RequiredDuringExecution` versiyasi yillardan beri
rejalashtirilgan.)

## Operatorlar

| Operator | Ma’nosi | `values` |
|---|---|---|
| `In` | label qiymati shulardan biri | shart |
| `NotIn` | label qiymati shulardan hech biri emas | shart |
| `Exists` | label kaliti mavjud | yozilmaydi |
| `DoesNotExist` | label kaliti yo’q | yozilmaydi |
| `Gt` / `Lt` | sonli solishtirish | bitta qiymat |

`NotIn` va `DoesNotExist` sizga **node anti-affinity** beradi - "kichik
node’larda emas", "control plane node’larida emas" - buni `nodeSelector`
ayta olmaydi.

## AND, OR va blokning shakli

- **Bitta** `nodeSelectorTerms` yozuvidagi bir nechta `matchExpressions` AND
  bilan bog’lanadi.
- `nodeSelectorTerms` ichidagi bir nechta yozuv OR bilan bog’lanadi.
- Preferred qoidalarda 1-100 oralig’idagi `weight` bo’ladi; scheduler node
  qanoatlantirgan qoidalarning og’irliklarini qo’shadi va eng katta yig’indi
  ball berish bosqichida yutadi.

```yaml
nodeSelectorTerms:
  - matchExpressions:                    # (size=large AND disktype=ssd)
      - {key: size, operator: In, values: [large]}
      - {key: disktype, operator: In, values: [ssd]}
  - matchExpressions:                    # OR (zone=b)
      - {key: topology.kubernetes.io/zone, operator: In, values: [b]}
```

:::exam-tip
Qiyin joyi g’oya emas, ichma-ich joylashuv. `kubectl explain
pod.spec.affinity.nodeAffinity --recursive` aniq daraxtni chiqaradi. Maydon
nomlarini yoddan emas, o’sha yerdan ko’chiring - `nodeSelectorTerms` ro’yxat,
`matchExpressions` ro’yxat, `values` ro’yxat.
:::

## Uchraydigan ikkita topshiriq

**"blue Deployment’ining Pod’lari faqat color=blue label’i qo’yilgan
node’larda ishlashi kerak":**

```bash
kubectl label node node01 color=blue
kubectl create deployment blue --image=nginx --replicas=3 $do > blue.yaml
```
keyin `spec.template.spec` ostiga qo’shing:
```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: color
              operator: In
              values: [blue]
```

**"red Deployment faqat control plane node’larida ishlashi kerak":** label -
bo’sh qiymatli `node-role.kubernetes.io/control-plane`, shuning uchun operator
`Exists` bo’ladi - va control plane taint qilingani uchun sizga **yana**
toleration ham kerak:

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: node-role.kubernetes.io/control-plane
              operator: Exists
tolerations:
  - key: node-role.kubernetes.io/control-plane
    operator: Exists
    effect: NoSchedule
```

## Pod affinity, qisqacha

Xuddi shu blok shakli `podAffinity` va `podAntiAffinity` sifatida ham mavjud:
u node’lar o’rniga **boshqa Pod’lar**ning label’lariga `topologyKey` doirasida
mos keladi (`kubernetes.io/hostname` = bir xil node,
`topology.kubernetes.io/zone` = bir xil zona). "Replikalarimni node’lar
bo’ylab tarqat" - bu ilovaning o’z label’i ustidagi, `topologyKey:
kubernetes.io/hostname` bilan yozilgan podAntiAffinity. Imtihonda kam
uchraydi; uning borligini va `topologyKey` majburiyligini bilib qo’ying.

## O’zingizni tekshiring

1. Node’ning label’i olib tashlanganda "IgnoredDuringExecution" amalda nimani
   anglatadi?
2. "Node’da `size=small` label’i **yo’q**" degani uchun matchExpression yozing.
3. Deployment faqat control plane node’larida ishlashi kerak. Pod shabloniga
   qaysi ikkita blok kerak va nega ikkitasi?
