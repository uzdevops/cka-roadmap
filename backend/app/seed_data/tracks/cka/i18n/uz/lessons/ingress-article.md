## API ko’chdi; eski misollar esa qolib ketdi

Ingress yillar davomida `extensions/v1beta1`’da, so’ng
`networking.k8s.io/v1beta1`’da turdi va internetdagi misollarning aksariyati
o’sha paytda yozilgan. Kubernetes 1.19 dan beri xizmat ko’rsatiladigan yagona
versiya - **`networking.k8s.io/v1`** va uning shakli o’zgargan. Bu eslatma -
o’sha o’tkazish jadvali: ko’chirib olingan manifest
`no matches for kind "Ingress" in version "extensions/v1beta1"` xatosi bilan
tugamasligi uchun.

## Nima o’zgardi

| v1beta1 (eski) | v1 (hozir) |
|---|---|
| `apiVersion: extensions/v1beta1` yoki `networking.k8s.io/v1beta1` | `apiVersion: networking.k8s.io/v1` |
| `backend: {serviceName: x, servicePort: 80}` | `backend: {service: {name: x, port: {number: 80}}}` |
| `kubernetes.io/ingress.class: nginx` annotatsiyasi | `spec.ingressClassName: nginx` (annotatsiyani nginx hali ham qabul qiladi, lekin u eskirgan) |
| `pathType` ixtiyoriy / yo’q | `pathType` **majburiy**: `Prefix`, `Exact` yoki `ImplementationSpecific` |
| `spec.backend` (sukut bo’yicha) | `spec.defaultBackend` |
| faqat `port: {number: 80}` | `port: {number: 80}` **yoki** `port: {name: http}` (nomlangan Service porti) |

```yaml
# eski
backend:
  serviceName: wear-service
  servicePort: 8080

# yangi
backend:
  service:
    name: wear-service
    port:
      number: 8080
```

```bash
kubectl convert -f old-ingress.yaml --output-version networking.k8s.io/v1   # kubectl-convert plugin'i uni qayta yozadi
kubectl explain ingress.spec.rules.http.paths.backend --recursive            # v1 shakli, server'dan olingan
```

## pathType, aniqrog’i

| pathType | `/wear` nimaga mos keladi |
|---|---|
| `Exact` | faqat `/wear` |
| `Prefix` | `/wear`, `/wear/`, `/wear/anything` - `/` bo’yicha bo’linadi, shuning uchun `/wearable` **emas** |
| `ImplementationSpecific` | kontroller nimani qaror qilsa (nginx: Prefix kabi, annotatsiya so’rasa regex ham) |

Deyarli har doim sizga `Prefix` kerak bo’ladi. `pathType`’ni unutish - v1 da
eng ko’p uchraydigan xato:
`spec.rules[0].http.paths[0].pathType: Required value`.

## IngressClass

v1 klassni haqiqiy obyektga aylantirdi, shuning uchun klaster ikkita
kontroller ishlata oladi (ichki uchun nginx, chekka uchun Traefik) va har bir
Ingress o’zi qaysi biri uchun ekanini aytadi:

```yaml
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: nginx
  annotations:
    ingressclass.kubernetes.io/is-default-class: "true"    # klassi yo'q Ingress'lar shuni oladi
spec:
  controller: k8s.io/ingress-nginx
```

```bash
kubectl get ingressclass
```

**Hech qanday** `ingressClassName`’ga ega bo’lmagan va sukut bo’yicha klassi
ham **yo’q** Ingress’ni hech kim qayta ishlamaydi. Kontroller "hech narsa
qilmayotganda" tekshiriladigan narsa ana shu.

:::exam-tip
Imtihon klasterlari zamonaviy: `networking.k8s.io/v1` deb yozing,
`pathType`’ni qo’shing, `ingressClassName`’dan foydalaning. `kubectl create ingress`
uchalasini ham siz uchun bajaradi - bu yozish o’rniga generatsiya qilishning
yana bir sababi.
:::

## Ingress’ni qayta o’qish

```bash
kubectl get ingress -A
kubectl describe ingress ingress-wear-watch -n app-space
# Rules:
#   Host              Path  Backends
#   shop.example.com  /wear   wear-service:8080 (10.244.1.5:8080,10.244.2.7:8080)
#                     /watch  video-service:8080 (<none>)        <- endpoint yo'q: bu yo'l 503 qaytaradi
```

`describe` har bir backend’ni uning endpoint’lariga yechib beradi; backend
yonidagi `<none>` - qaysi Service uzilgan halqa ekanini ko’rishning eng tez
yo’li.

## O’zingizni tekshiring

1. `backend: {serviceName: api, servicePort: 80}`’ni v1 shaklida qayta yozing.
2. v1 da qaysi maydon majburiy bo’ldi va uning uchta qiymati qanday?
3. Ingress’da `ingressClassName` yo’q va klasterda sukut bo’yicha IngressClass
   ham yo’q. Nima bo’ladi?
