## Uchta obyekt, bitta workload

```text
Deployment          buni siz yozasiz - rollout strategiyasi va shablonni e'lon qiladi
    |  yaratadi va egalik qiladi
    v
ReplicaSet          har versiyaga bittadan - shablonga mos N ta Pod ushlab turadi
    |  yaratadi va egalik qiladi
    v
Pod  Pod  Pod       haqiqiy konteynerlar
```

Deployment Pod’larni boshqarmaydi. U ReplicaSet’larni boshqaradi. Siz Pod
shablonini har o’zgartirganingizda, u **yangi** ReplicaSet yaratadi va eskisini
kamaytira borib yangisini oshiradi. Rollback’ni shu qadar oson qiladigan narsa
ham shu: eski ReplicaSet nol replika bilan hamon joyida turadi.

```bash
kubectl get deploy,rs,pods -l app=web
# deployment.apps/web           3/3     3            3
# replicaset.apps/web-6f4c9d8   3       3            3     <- joriy
# replicaset.apps/web-5b8a7c2   0       0            0     <- oldingi versiya
# pod/web-6f4c9d8-abc12  1/1  Running
```

## To’liq Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  labels:
    app: web
spec:
  replicas: 3
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      app: web             # yaratilgandan keyin o'zgarmas
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%        # replicas ustiga ruxsat etilgan qo'shimcha Pod'lar
      maxUnavailable: 25%  # roll paytida yetishmasligi mumkin bo'lgan Pod'lar
  template:
    metadata:
      labels:
        app: web           # yuqoridagi selector'ni qanoatlantirishi shart
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          ports:
            - containerPort: 80
          readinessProbe:
            httpGet: {path: /, port: 80}
            periodSeconds: 5
          resources:
            requests: {cpu: 100m, memory: 64Mi}
            limits:   {cpu: 500m, memory: 128Mi}
```

:::warning
Deployment mavjud bo’lgandan keyin `spec.selector`’ni o’zgartirib bo’lmaydi.
Agar topshiriqda boshqa selector label’lari talab qilinsa, o’chirib qayta
yarating. `kubectl edit` urinishi `field is immutable` qaytaradi.
:::

## Rollout’lar

```bash
# Shablonni o'zgartirib rollout'ni ishga tushirish
kubectl set image deployment/web nginx=nginx:1.28
kubectl annotate deployment/web kubernetes.io/change-cause="nginx 1.28"

kubectl rollout status deployment/web        # tugagunicha yoki qotguncha bloklaydi
kubectl rollout history deployment/web
kubectl rollout history deployment/web --revision=2

kubectl rollout pause deployment/web         # bir nechta tahrirni jamlash
kubectl set resources deployment/web -c=nginx --limits=cpu=1
kubectl rollout resume deployment/web

kubectl rollout undo deployment/web          # bir versiya orqaga
kubectl rollout undo deployment/web --to-revision=2
kubectl rollout restart deployment/web       # Pod'larni qayta yaratadi, shablon o'sha
```

`kubectl rollout restart`’ni alohida eslab qolishga arziydi: u image’ni
o’zgartirmasdan yangi Pod’larni majburan yaratadi - environment variable
sifatida ulangan ConfigMap yoki Secret o’zgarganda uni shu yo’l bilan olasiz.

## RollingUpdate matematikasi

`replicas: 10`, `maxSurge: 25%`, `maxUnavailable: 25%` bo’lganda:

- maxSurge = 2 (2.5 dan pastga yaxlitlangan) -> bir vaqtning o’zida ko’pi bilan
  12 Pod mavjud bo’ladi
- maxUnavailable = 2 -> jarayon davomida kamida 8 Pod mavjud bo’lishi shart

Ikkita maxsus konfiguratsiya:

```yaml
# Nol uzilish, zaxira sig'im talab qiladi
rollingUpdate:
  maxSurge: 1
  maxUnavailable: 0

# Qat'iy sig'im, qisqa muddatli kamaygan quvvatga rozi
rollingUpdate:
  maxSurge: 0
  maxUnavailable: 1
```

`maxSurge: 0` **va** `maxUnavailable: 0` birgalikda rad etiladi - bunday
rollout hech qachon oldinga siljiy olmasdi.

## Recreate strategiyasi

```yaml
strategy:
  type: Recreate
```

Bironta yangi Pod yaratilishidan oldin barcha eski Pod’larni tugatadi.
Uzilishni kafolatlaydi. Uni ikki versiya haqiqatan bir vaqtda ishlay olmaganda
ishlating - sxema migratsiyasi yoki faqat bitta Pod mount qila oladigan
`ReadWriteOnce` volume.

## Rollout’ni xavfsiz qiladigan narsa - readiness probe’lar

Rollout yangi Pod’ni faqat uning readiness probe’i o’tgandagina mavjud deb
hisoblaydi. Readiness probe bo’lmasa, "mavjud" degani "konteyner jarayoni ishga
tushdi" degani bo’lib qoladi, shuning uchun Deployment har bir ishlayotgan
Pod’ni buzuqi bilan bemalol almashtiraveradi.

:::exam-tip
"Rollout tugadi, lekin sayt ishlamayapti" degani deyarli har doim readiness
probe yo’qligini bildiradi. "Rollout 1/3 yangilangan holatda qotib qoldi" esa
odatda yangi Pod’larda readiness probe *bor* va ular undan o’ta olmayapti
degani - to’g’ridan-to’g’ri yangi Pod ustida `kubectl describe pod` qiling va
probe nosozligi hodisalarini o’qing.
:::

## Qotib qolgan rollout’ni tashxislash

```bash
kubectl rollout status deployment/web --timeout=60s
kubectl get rs -l app=web                       # qaysi RS masshtablanmayapti
kubectl describe deployment web | tail -20      # condition'lar
kubectl describe pod <new-pod>                  # haqiqiy sabab
```

Javobni Deployment’ning ikkita condition’i olib yuradi:

```text
Type           Status  Reason
Available      False   MinimumReplicasUnavailable
Progressing    False   ProgressDeadlineExceeded
```

`ProgressDeadlineExceeded` - `spec.progressDeadlineSeconds` (sukut bo’yicha
600) davomida hech qanday siljish bo’lmagani. Deployment taslim bo’ladi; u
avtomatik rollback **qilmaydi**.

Keng tarqalgan sabablar: image tortishdagi nosozlik, o’tmayotgan readiness
probe, surge Pod’lari uchun klasterda resurs yetishmasligi yoki ikki marta
mount qilib bo’lmaydigan PVC.

## Masshtablash

```bash
kubectl scale deployment web --replicas=5
kubectl scale deployment web --current-replicas=3 --replicas=5   # shartli
```

Masshtablash yangi versiya yaratmaydi - u mavjud ReplicaSet’ni tahrirlaydi.

## To’g’ridan-to’g’ri ReplicaSet’lar

Siz uni kamdan-kam yaratasiz, lekin uni o’qiy olishingiz shart.

```bash
kubectl get rs
kubectl describe rs web-6f4c9d8
```

Egalik zanjiri Pod’ning o’zida ko’rinadi:

```bash
kubectl get pod web-6f4c9d8-abc12 -o jsonpath='{.metadata.ownerReferences}'
# [{"apiVersion":"apps/v1","kind":"ReplicaSet","name":"web-6f4c9d8",...}]
```

Pod’ni o’chiring - ReplicaSet uni qayta yaratadi. ReplicaSet’ni o’chiring -
Deployment uni qayta yaratadi. Workload’ni haqiqatan olib tashlash uchun
Deployment’ni o’chiring.

## O’zingizni tekshiring

1. Deployment’ning image’ini o’zgartirdingiz. Shundan keyin nechta ReplicaSet
   mavjud bo’ladi va ularning replika sonlari qanday?
2. `ProgressDeadlineExceeded` nimani anglatadi va Kubernetes avtomatik
   rollback qiladimi?
3. Mount qilingan ConfigMap o’zgardi, lekin Pod’lar hamon eski qiymatlarni
   ishlatmoqda. Buni qaysi bitta buyruq tuzatadi?
