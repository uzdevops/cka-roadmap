## Tashqi trafikni ichkariga kiritish, cloud usuli

NodePort dunyoga har bir node’da bitta port beradi - lekin "har bir node" bu
o’zgarib turadigan IP’lar ro’yxati va 31234 porti mijoz teradigan narsa emas.
Cloud’da yechim - `type: LoadBalancer` Service’i: Kubernetes cloud’dan haqiqiy
yuk muvozanatlagich so’raydi, cloud tashqi IP yoki hostname qaytaradi va unga
kelgan trafik NodePort’lar bo’ylab taqsimlanadi.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 8080
```

```bash
kubectl get svc web
# NAME   TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)        AGE
# web    LoadBalancer   10.96.33.12    203.0.113.45     80:31907/TCP   40s
```

Qatorga qarang: ClusterIP, NodePort (`31907`) va EXTERNAL-IP. Uchta tur
haqiqatan ham ichma-ich joylashgan. LoadBalancer Service’i **aslida** NodePort
Service’i bo’lib, qo’shimcha ravishda **cloud controller**’dan oldiga biror
narsa o’rnatib berishni so’raydi.

## Uni kim yaratadi

**cloud-controller-manager** - faqat cloud bilan integratsiyalangan
klasterlarda (EKS, GKE, AKS va cloud provider plagini bor on-prem
o’rnatmalarda) mavjud bo’ladigan control plane komponenti. U LoadBalancer
Service’larni kuzatib turadi va cloud API’sini chaqiradi.

Shuning uchun ham yalang’och klasterda (kind, minikube, oddiy VM’lardagi
kubeadm) bunday bo’ladi:

```bash
kubectl get svc web
# NAME   TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
# web    LoadBalancer   10.96.33.12   <pending>     80:31907/TCP   5m
```

Abadiy `<pending>` - bu xato emas. So’rovni bajaradigan hech narsa yo’q.
NodePort qismi avvalgidek ishlayveradi; faqat tashqi IP hech qachon
kelmaydi.

:::exam-tip
Imtihon klasterlarida cloud provider yo’q. Topshiriqda "LoadBalancer sifatida
oching" deyilsa, uni yarating va davom eting - `<pending>` to’g’ri yakuniy
holat va sizni IP paydo bo’lishi bo’yicha emas, Service obyekti bo’yicha
baholashadi.
:::

## On-prem’da bo’shliqni to’ldirish

Cloud’siz LoadBalancer Service’lari kerak bo’lganda ikkita keng tarqalgan
javob bor:

- **MetalLB** - siz bergan oraliqdan IP’larni tarqatadigan va ularni ARP yoki
  BGP orqali e’lon qiladigan kontroller. Service nuqtai nazaridan uni
  cloud’dan farqlab bo’lmaydi.
- ClusterIP Service’lar oldida turadigan **Ingress / Gateway** - ko’plab HTTP
  ilovalari uchun bitta kirish nuqtasi, odatda sizga kerak bo’lgan narsa ham
  shu. Bu - tarmoq bosqichidagi Ingress va Gateway API darslari.

## Bilishga arziydigan bir nechta maydon

```yaml
spec:
  type: LoadBalancer
  loadBalancerIP: 203.0.113.45          # aniq IP so'rash (cloud/MetalLB'ga bog'liq)
  externalTrafficPolicy: Local          # faqat paketni qabul qilgan node'dagi Pod'larga yo'naltirish
  loadBalancerSourceRanges:
    - 198.51.100.0/24                   # yuk muvozanatlagich darajasidagi ruxsat ro'yxati
```

`externalTrafficPolicy: Local` klientning manba IP’sini saqlaydi va ortiqcha
sakrashning oldini oladi, buning evaziga Pod’lar tekis taqsimlanmagan bo’lsa
yuk notekis bo’ladi; sukut bo’yicha `Cluster` teskari kelishuvni tanlaydi.

## Uchtasidan qaysi birini tanlash

| Sizga kerak | Foydalaning |
|---|---|
| faqat ichki | ClusterIP |
| test uchun tez tashqi kirish yoki o’z LB’ngiz ortidagi port | NodePort |
| cloud’da haqiqiy ommaviy endpoint | LoadBalancer |
| bitta ommaviy endpoint ortida ko’plab HTTP ilovalari | ClusterIP’lar ustida Ingress yoki Gateway |

## O’zingizni tekshiring

1. LoadBalancer Service’ida NodePort’da yo’q nima bor va uni qaysi komponent
   ta’minlaydi?
2. Imtihon klasterida `EXTERNAL-IP` `<pending>` ko’rsatmoqda. Nima qilasiz?
3. `externalTrafficPolicy: Local` sizga nima beradi va nima evaziga?
