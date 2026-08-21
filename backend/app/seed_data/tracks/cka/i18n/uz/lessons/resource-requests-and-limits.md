## Har bir konteyner uchun ikkita raqam

```yaml
spec:
  containers:
    - name: app
      image: myapp:1.0
      resources:
        requests:
          cpu: 250m
          memory: 128Mi
        limits:
          cpu: "1"
          memory: 256Mi
```

- **requests** - Pod uchun *kafolatlangan* miqdor. Scheduler Pod’ni faqat
  shuncha bo’sh (so’ralmagan) sig’imi bor node’ga joylashtiradi.
  Rejalashtirish uchun ishlatiladi, ishlash vaqtida majburlanmaydi.
- **limits** - konteyner *hech qachon oshirmasligi* kerak bo’lgan miqdor.
  Buni kubelet va yadro majburlaydi.

Birliklar: CPU yadrolarda yoki millicore’larda (`1` = `1000m`); memory
baytlarda, `Ki/Mi/Gi` (1024 darajalari) yoki `K/M/G` (1000 darajalari) bilan.
Sizga keragi - `Mi`.

## Limitga yetganda nima bo’ladi - CPU va memory har xil

| Resurs | Limitdan oshish nimani anglatadi |
|---|---|
| **CPU** | konteyner **throttle** qilinadi - unga kamroq vaqt tegadi, sekinlashadi, lekin o’lmaydi |
| **Memory** | konteyner **OOMKilled** bo’ladi - yadro jarayonni o’ldiradi, kubelet uni qayta ishga tushiradi, `RESTARTS` o’sib boradi |

```bash
kubectl describe pod elephant | grep -A5 "Last State"
#   Last State:     Terminated
#     Reason:       OOMKilled
#     Exit Code:    137
```

137 chiqish kodi = 128 + 9 (SIGKILL) - bu barmoq izi. Yechim - memory
limitini oshirish (yoki kamroq ochko’z ilova) - va ishlab turgan Pod’da
`resources` o’zgarmas bo’lgani uchun, tahrirdan keyin `kubectl replace
--force` qilinadi yoki Deployment’ning shabloni tahrirlanadi.

## Request va limit bo’lmasa nima bo’ladi

**request** bo’lmasa, scheduler Pod’ga hech narsa kerak emas deb hisoblaydi
va uni istalgan joyga tiqadi - node haddan tashqari band bo’lib qolmaguncha
bu yaxshi. **limit** bo’lmasa, konteyner node’dagi hamma narsani ishlatib,
qo’shnilarini och qoldirishi mumkin. Pod oladigan quality-of-service klassi
kubelet’ga bosim ostida kimni birinchi bo’lib chiqarib yuborishni aytadi:

| Request / limit | QoS klassi | Chiqarib yuboriladi |
|---|---|---|
| har bir konteyner uchun limit == request | `Guaranteed` | oxirgi |
| ba’zi request yoki limit belgilangan | `Burstable` | o’rtada |
| hech narsa belgilanmagan | `BestEffort` | birinchi |

```bash
kubectl get pod app -o jsonpath='{.status.qosClass}'
```

## Namespace uchun sukut qiymatlari: LimitRange

**LimitRange** o’zi request va limit belgilamagan konteynerlar uchun ularni
to’ldiradi va kim nima so’rashi mumkinligiga chegara qo’ya oladi:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: cpu-defaults
  namespace: dev
spec:
  limits:
    - type: Container
      default:            # hech narsa belgilanmaganda qo'llanadigan limit
        cpu: 500m
        memory: 256Mi
      defaultRequest:     # hech narsa belgilanmaganda qo'llanadigan request
        cpu: 100m
        memory: 128Mi
      max:
        cpu: "2"
      min:
        cpu: 50m
```

U o’zi mavjud bo’lgandan **keyin yaratilgan** Pod’larga qo’llanadi; mavjud
Pod’larga tegmaydi.

## Namespace uchun byudjet: ResourceQuota

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
```

```bash
kubectl create quota dev-quota --hard=pods=20,requests.cpu=4 -n dev
kubectl describe quota -n dev
```

:::warning
Namespace’da `requests.cpu` bo’yicha kvota paydo bo’lishi bilan undagi har bir
Pod CPU request belgilashi **shart** - aks holda API server uni `must specify
requests.cpu` deb rad etadi. Odatdagi juftlik - ResourceQuota va sukut
qiymatlarini beradigan LimitRange, shunda oddiy Pod’lar ishlashda davom etadi.
:::

## Ularni tez o’qish va o’rnatish

```bash
kubectl get pod app -o jsonpath='{.spec.containers[0].resources}'
kubectl top pod app                                   # haqiqiy sarf (metrics-server kerak)
kubectl set resources deployment app --requests=cpu=200m,memory=256Mi --limits=cpu=1,memory=512Mi
kubectl describe node node01 | grep -A8 "Allocated resources"   # node request bo'yicha qanchalik to'la
```

:::exam-tip
"Pod Pending’da qotib qolgan, event `Insufficient memory` deydi" - bu limit
emas, request muammosi: hech bir node’da shuncha *so’ralmagan* memory
qolmagan. Yo request’ni kamaytiring, yo node bo’shating. "Pod qayta ishga
tushyapti, OOMKilled" - bu limit muammosi. Ikki xil raqam, ikki xil yechim.
:::

## O’zingizni tekshiring

1. Bitta konteyner CPU limitidan oshib ketdi; ikkinchisi memory limitidan
   oshib ketdi. Har biriga nima bo’ladi?
2. Umuman `resources` yo’q Pod qanday QoS klassini oladi va node’da memory
   tugaganda bu nimani anglatadi?
3. Namespace’ga `requests.cpu` kvotasini qo’shdingiz va oddiy `kubectl run
   nginx --image=nginx` ishlamay qoldi. Nega, va buni qaysi obyekt tuzatadi?
