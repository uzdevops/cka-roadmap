## Har bir Service uchun alohida LoadBalancer keltirib chiqaradigan muammo

Bitta ilova, tashqariga ochilgan: `LoadBalancer` Service, cloud yuk
muvozanatlagichi, tashqi IP va unga qaratilgan DNS. Yaxshi. Endi o’n ikkita
ilova bor: o’n ikkita yuk muvozanatlagich, o’n ikkita IP, o’n ikkita hisob va
TLS yoki yo’l bo’yicha marshrutlash uchun yagona joy yo’q. Bare metalda esa
bu yuk muvozanatlagichlarni yaratadigan cloud umuman yo’q.

**Ingress** oldinga bitta narsani qo’yadi: **bitta** tashqi kirish nuqtasiga
ega **Ingress kontrolleri** (Pod sifatida ishlaydigan teskari proksi - nginx,
HAProxy, Traefik) va unga "X host, Y yo’l → mana bu Service" deb aytadigan
**Ingress resurslari**. O’n ikkita ilova, bitta yuk muvozanatlagich, host va
yo’l bo’yicha marshrutlash, bitta joyda TLS tugatish.

```
internet ─▶ one LB / NodePort ─▶ Ingress controller Pods ─▶ Service wear:8080 (for /wear)
                                                         ─▶ Service video:8080 (for /watch)
```

Kubernetes Ingress **resurs turini** beradi, lekin **kontrollerni bermaydi**:
CNI kabi, uni siz o’rnatasiz. Imtihonda nginx Ingress kontrolleri bo’ladi (va
uning hujjatlarini o’qishga ruxsat beradi).

## Kontroller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.1/deploy/static/provider/baremetal/deploy.yaml
kubectl get all -n ingress-nginx
# deployment.apps/ingress-nginx-controller
# service/ingress-nginx-controller   NodePort   ...  80:30080/TCP,443:30443/TCP
kubectl get ingressclass
# NAME    CONTROLLER             PARAMETERS   AGE
# nginx   k8s.io/ingress-nginx   <none>       1m
```

Ichkarida kontroller manifesti quyidagilardan iborat: Ingress obyektlarini
kuzatib, nginx konfiguratsiyasini qayta yozadigan kontroller jarayoni bilan
nginx ishlatadigan Deployment; unga yetib borish uchun Service (NodePort yoki
LoadBalancer); nginx sozlamalari uchun ConfigMap; Ingress, Service va
EndpointSlice’larni kuzatish uchun RBAC’ga ega ServiceAccount; va Ingress
resurslari o’zi qaysi kontroller uchun ekanini ayta olishi uchun
**IngressClass**.

## Resurs

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-wear-watch
  namespace: app-space
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: shop.example.com              # ixtiyoriy; host bo'lmasa - istalgan host
      http:
        paths:
          - path: /wear
            pathType: Prefix              # Prefix | Exact | ImplementationSpecific
            backend:
              service:
                name: wear-service
                port:
                  number: 8080
          - path: /watch
            pathType: Prefix
            backend:
              service:
                name: video-service
                port:
                  number: 8080
  defaultBackend:                          # ixtiyoriy: mos kelmagan hamma narsa qayerga ketadi
    service:
      name: default-http-backend
      port:
        number: 80
```

```bash
kubectl create ingress ingress-wear-watch -n app-space --class=nginx \
  --rule="shop.example.com/wear=wear-service:8080" \
  --rule="shop.example.com/watch=video-service:8080"
kubectl create ingress ingress-wear-watch -n app-space --rule="/wear=wear-service:8080" --rule="/watch=video-service:8080" $do > ing.yaml
kubectl get ingress -n app-space
# NAME                 CLASS   HOSTS              ADDRESS        PORTS   AGE
# ingress-wear-watch   nginx   shop.example.com   192.168.1.11   80      10s
kubectl describe ingress ingress-wear-watch -n app-space      # qoidalar jadval ko'rinishida, ustiga kontroller hodisalari
```

Ball yo’qotadigan, to’g’ri qilinishi kerak bo’lgan ikki narsa:

- Ingress **o’zi marshrutlaydigan Service’lar bilan bir xil namespace’da**
  turadi. `default`’dagi Ingress `app-space`’dagi `wear-service`’ga
  ko’rsata olmaydi.
- `ingressClassName` (yoki eskiroq `kubernetes.io/ingress.class: nginx`
  annotatsiyasi) mavjud IngressClass’ni nomlashi kerak, aks holda kontroller
  resursni e’tiborsiz qoldiradi va ADDRESS bo’sh qolaveradi.

:::exam-tip
`kubectl create ingress` - tez yo’l va u `--rule`
(`host/path=service:port`), `--class`, `--annotation` hamda
`--default-backend`’ni qo’llab-quvvatlaydi. Undan foydalaning, keyin `$do`
qiling va faqat `pathType: Exact` yoki TLS kerak bo’lsagina tahrirlang.
:::

## Sinash

```bash
curl -H "Host: shop.example.com" http://<node-ip>:30080/wear
kubectl get svc -n ingress-nginx        # kontrollerda qaysi NodePort / tashqi IP bor
kubectl logs -n ingress-nginx deploy/ingress-nginx-controller | tail   # nginx access log: o'z so'rovingizni va 404'larni ko'rasiz
```

nginx’dan kelgan `404` - so’rov kontrollerga yetib borgan, lekin hech qanday
qoida mos kelmagan degani (noto’g’ri host, noto’g’ri yo’l, noto’g’ri
namespace); `503` - qoida mos keldi, lekin Service’ning endpoint’lari yo’q
degani; connection refused - kontrollerning portini noto’g’ri olgansiz degani.

## O’zingizni tekshiring

1. Ingress uchun Kubernetes nimani beradi va siz nimani o’rnatishingiz kerak?
2. Nega Ingress o’zining backend Service’lari bilan bir xil namespace’da
   bo’lishi kerak?
3. Ingress’ingizda ADDRESS ko’rinmayapti va kontroller uni e’tiborsiz
   qoldirmoqda. Qaysi maydonni birinchi bo’lib tekshirasiz?
