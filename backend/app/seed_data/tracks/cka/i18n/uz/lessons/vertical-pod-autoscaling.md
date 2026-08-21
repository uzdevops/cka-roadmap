## Ko’proq nusxa emas, to’g’ri o’lcham

HPA "nechta" degan savolga javob beradi; **Vertical Pod Autoscaler** esa
"qanchalik katta" degan savolga. U workload Pod’larining haqiqiy CPU va
memory sarfini kuzatadi, ularning request’lari (va proporsional ravishda
limitlari) uchun tavsiya hisoblaydi va - rejimiga qarab - uni qo’llaydi.

VPA **ichida kelmaydi**. U `kubernetes/autoscaler` repozitoriyasidan
o’rnatiladigan alohida loyiha:

```bash
git clone https://github.com/kubernetes/autoscaler.git
cd autoscaler/vertical-pod-autoscaler
./hack/vpa-up.sh
kubectl get pods -n kube-system | grep vpa
# vpa-admission-controller-...
# vpa-recommender-...
# vpa-updater-...
kubectl get crd | grep verticalpodautoscaler
```

## Uchta komponent

| Komponent | Nima qiladi |
|---|---|
| **Recommender** | metrikalarni kuzatadi (Metrics Server kerak), har konteyner uchun target/lower/upper chegaralarni hisoblaydi |
| **Updater** | `Auto`/`Recreate` rejimida request’lari tavsiyadan juda uzoq bo’lgan Pod’larni **evict qiladi**, shunda ular yangi qiymatlar bilan qayta yaratiladi |
| **Admission controller** | tavsiya etilgan request’larni Pod’lar *yaratilayotgan paytda* ularga yozadigan mutating webhook |

Mexanizmga e’tibor bering: klassik VPA Pod resurslarini uni **evict qilib**,
kontrollerga qayta yaratishga qo’yib berib o’zgartiradi, admission webhook
esa yangi raqamlarni kirish yo’lida kiritadi. Shuning uchun u uzilishga
sabab bo’ladi va shuning uchun yangiroq `InPlaceOrRecreate` rejimi (imkon
bo’lganda in-place resize’dan foydalanadigan) mavjud.

## Obyektning o’zi

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: hamster
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: hamster
  updatePolicy:
    updateMode: "Off"            # Off | Initial | Recreate | Auto | InPlaceOrRecreate
  resourcePolicy:
    containerPolicies:
      - containerName: "*"
        minAllowed: {cpu: 100m, memory: 50Mi}
        maxAllowed: {cpu: "2",  memory: 2Gi}
        controlledResources: ["cpu", "memory"]
```

| updateMode | Xatti-harakati |
|---|---|
| `Off` | faqat tavsiya qiladi - ularni o’qing va qo’lda qo’llang. Boshlash uchun xavfsiz yo’l. |
| `Initial` | tavsiyalarni faqat **yangi** Pod’larga qo’llaydi; hech qachon evict qilmaydi |
| `Recreate` | o’zgarishlarni qo’llash uchun Pod’larni evict qiladi |
| `Auto` | hozircha Recreate bilan bir xil; imkon paydo bo’lganda in-place’ni afzal ko’radi |
| `InPlaceOrRecreate` | avval in-place resize’ni sinaydi, faqat uddalay olmasa evict qiladi |

```bash
kubectl describe vpa hamster
#   Recommendation:
#     Container Recommendations:
#       Container Name:  hamster
#       Lower Bound:   Cpu: 100m  Memory: 262144k
#       Target:        Cpu: 587m  Memory: 262144k
#       Upper Bound:   Cpu: 1     Memory: 500Mi
kubectl get pods -l app=hamster -o jsonpath='{.items[*].spec.containers[0].resources.requests}'
```

## HPA va VPA birga

Ikkalasining bir xil metrika bo’yicha bitta Deployment’ga yozishi
chalkashlik keltiradi: CPU yuqori bo’lgani uchun HPA replika qo’shadi, VPA
request’ni oshiradi, natijada foiz tushadi, HPA replikalarni olib tashlaydi
va hokazo. Ishlaydigan kombinatsiyalar:

- CPU’da HPA, **faqat memory**da VPA (`controlledResources: ["memory"]`);
- custom/external metrikada (sekundiga so’rovlar) HPA, CPU va memory’da VPA;
- sof tavsiya paneli sifatida `Off` rejimidagi VPA, masshtablashni esa HPA
  bajaradi.

:::exam-tip
"VPA’ni o’rnating / X Deployment uchun faqat tavsiya beruvchi rejimda VPA
yarating / target tavsiyani o’qing" ko’rinishidagi savollarni kuting. CRD’ning
`apiVersion`i - `autoscaling.k8s.io/v1`, HPA’niki bo’lgan `autoscaling/v2`
emas - va Pod’larga hech qachon tegmaydigan rejim `"Off"` (qo’shtirnoqda,
u satr).
:::

## Qachon qaysi biri

- Stateless, gorizontal masshtablanadigan, yukka bog’liq → HPA.
- Bitta replika, yoki StatefulSet, yoki Job, savol esa "bu qancha so’rashi
  kerak" bo’lsa → VPA.
- To’g’ri request’lar qanaqaligini umuman bilmasangiz → bir hafta `Off`
  rejimida VPA, keyin tavsiyadan kelib chiqib ularni belgilang va yo’lda
  davom eting.

## O’zingizni tekshiring

1. VPA’ning uchta komponentini va har biri nima qilishini ayting.
2. `Recreate` rejimida VPA ishlab turgan Pod’ning request’larini qanday
   o’zgartiradi va nega bu uzilishga sabab bo’ladi?
3. VPA Pod’ga umuman tegmasdan tavsiya olish uchun qaysi `updateMode`ni
   tanlaysiz?
