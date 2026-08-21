## Band bo’lganda ko’proq replika

HorizontalPodAutoscaler Deployment’ning (yoki ReplicaSet, StatefulSet)
Pod’laridagi metrikani kuzatadi va metrikani minimum bilan maksimum orasida
maqsadga yaqin ushlab turish uchun `spec.replicas`ni yozadi.

```bash
kubectl autoscale deployment php-apache --cpu-percent=50 --min=1 --max=10
kubectl get hpa
# NAME         REFERENCE               TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
# php-apache   Deployment/php-apache   12%/50%   1         10        1          30s
```

`12%/50%` - joriy va maqsad: Pod’lar bo’ylab o’rtacha CPU sarfi, ularning CPU
**request**ining foizi sifatida. Shuning uchun Pod’larda request bo’lishi
shart; ularsiz HPA foizni hisoblay olmaydi va `<unknown>` ko’rsatadi.

## Obyektning o’zi

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: php-apache
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: php-apache
  minReplicas: 1
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization       # request'ning foizi
          averageUtilization: 50
    - type: Resource
      resource:
        name: memory
        target:
          type: AverageValue      # har Pod uchun mutlaq miqdor
          averageValue: 500Mi
  behavior:                       # ixtiyoriy: u qanchalik tez harakat qilishi mumkin
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Pods
          value: 4
          periodSeconds: 15
```

Yoziladigan versiya - `autoscaling/v2`: u bir nechta metrikani (HPA natijadagi
**eng katta** replika sonini oladi), memory’ni, custom metrikalarni
(`type: Pods`, `type: Object`) va external metrikalarni (`type: External`),
shuningdek `behavior` blokini qo’llab-quvvatlaydi. `autoscaling/v1` faqat CPU
uchun; `kubectl autoscale` o’shani yaratadi va imtihon uchun bu yetarli.

## Algoritm

```
desiredReplicas = ceil( currentReplicas * currentMetric / targetMetric )
```

50 % maqsadga qarshi o’rtacha 80 % beradigan ikkita Pod: `ceil(2 * 80/50) = 4`.
U har 15 soniyada qayta baholaydi, 10 % tolerantlik ichidagi o’zgarishlarni
e’tiborsiz qoldiradi va sukut bo’yicha **pastga** masshtablashdan oldin yuk
past bo’lib turishini 5 daqiqa kutadi (`stabilizationWindowSeconds`) - ya’ni
yuqoriga tez, pastga ehtiyotkorlik bilan, sizga kerak bo’lgani ham shu.

## Uni ishda kuzatish

```bash
kubectl run load --rm -it --image=busybox:1.36 --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://php-apache; done"
# boshqa terminalda
kubectl get hpa php-apache -w
# php-apache   Deployment/php-apache   250%/50%   1   10   1
# php-apache   Deployment/php-apache   250%/50%   1   10   4
# php-apache   Deployment/php-apache    48%/50%   1   10   5
kubectl get deployment php-apache       # REPLICAS ortidan boradi
kubectl describe hpa php-apache         # Events: SuccessfulRescale ... New size: 4; reason: cpu resource utilization above target
```

Yukni to’xtating va besh daqiqadan keyin u yana 1 gacha tushib boradi.

## Nima noto’g’ri ketadi

| Alomat | Sabab |
|---|---|
| TARGETS `<unknown>/50%` | Metrics Server ishlamayapti yoki Pod’larda CPU `requests` yo’q |
| describe’da `FailedGetResourceMetric` | o’sha ikki sabab, ochiq yozilgani |
| hech qachon N dan oshmaydi | `maxReplicas`, yoki Deployment ko’proq Pod joylashtira olmaydi (joy yo’q - bu Cluster Autoscaler’ning ishi) |
| yuqoriga-pastga sakrayveradi | maqsad juda tor, yoki ilovaning CPU’si tepkili - `behavior` oynalarini kengaytiring |
| har `kubectl apply` da replikalar tiklanadi | Deployment faylingizda `replicas: 1` bor; HPA egalik qilganda `replicas`ni fayldan olib tashlang |

:::exam-tip
`kubectl autoscale deployment X --cpu-percent=50 --min=2 --max=8` - odatiy
topshiriqning to’liq javobi. Agar topshiriqda memory yoki ikkinchi metrika
tilga olinsa, sizga `autoscaling/v2` manifesti kerak - `kubectl autoscale
... $do` sizga yangilanadigan v1 skeletini beradi.
:::

## O’zingizni tekshiring

1. Uchta Pod 60 % maqsadga qarshi o’rtacha 90 % CPU ishlatyapti. HPA nechta
   replika so’raydi?
2. Nega HPA Pod’lar CPU request belgilashini talab qiladi?
3. Siz Deployment’ni `kubectl apply` qildingiz va HPA’ning masshtablashi
   bekor bo’ldi. Nega, va faylda nimani o’zgartirasiz?
