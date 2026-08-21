## Noldan yo’naltirilgan trafikkacha

Gateway API sozlamasi - to’rt qadam. Ularni lab klasterida bir marta
bajaring, imtihondagi varianti xuddi shu qadamlar, faqat fayllar sizga
beriladi.

### 1. CRD’larni o’rnatish

Gateway API resurslari Kubernetes ichiga **qurilmagan**; ular CRD’lar va
alohida versiyalanadi:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.1.0/standard-install.yaml
kubectl get crd | grep gateway.networking.k8s.io
# gatewayclasses.gateway.networking.k8s.io
# gateways.gateway.networking.k8s.io
# httproutes.gateway.networking.k8s.io
# grpcroutes..., referencegrants...
```

`standard-install.yaml` - barqaror to’plam; `experimental-install.yaml`
ustiga TCPRoute/UDPRoute/TLSRoute qo’shadi.

### 2. Kontroller o’rnatish

CRD’lar API’ni belgilaydi; uni kimdir amalga oshirishi kerak. NGINX Gateway
Fabric, Envoy Gateway, Istio, Contour, Cilium va cloud provayderlarining
kontrollerlari - hammasi shuni qiladi. Lab uchun:

```bash
kubectl apply -f https://raw.githubusercontent.com/nginxinc/nginx-gateway-fabric/v1.3.0/deploy/crds.yaml
kubectl apply -f https://raw.githubusercontent.com/nginxinc/nginx-gateway-fabric/v1.3.0/deploy/default/deploy.yaml
kubectl get pods -n nginx-gateway
kubectl get gatewayclass
# NAME    CONTROLLER                                   ACCEPTED   AGE
# nginx   gateway.nginx.org/nginx-gateway-controller   True       30s
```

Kontrollerning manifest’i odatda GatewayClass’ni siz uchun yaratadi. Agar
yaratmagan bo’lsa, uni kontrollerning `controllerName` i bilan o’zingiz
yozasiz.

### 3. Gateway yaratish

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: nginx-gateway
  namespace: nginx-gateway
spec:
  gatewayClassName: nginx
  listeners:
    - name: http
      protocol: HTTP
      port: 80
      allowedRoutes:
        namespaces:
          from: All
```

```bash
kubectl apply -f gateway.yaml
kubectl get gateway -n nginx-gateway
# NAME            CLASS   ADDRESS         PROGRAMMED   AGE
# nginx-gateway   nginx   192.168.1.240   True         20s
kubectl get svc -n nginx-gateway         # kontrollerning Service'i: LoadBalancer yoki NodePort - trafik shu yerdan kiradi
```

`PROGRAMMED True` - kontroller o’zini shu Gateway uchun sozlagani. Yuk
muvozanatlagichi yo’q klasterda ADDRESS NodePort Service’ining node IP’si
bo’lishi mumkin, yoki bo’sh bo’ladi-yu, Service hamon o’z NodePort’ida
yetib boriladigan bo’ladi - kontroller namespace’ida `kubectl get svc` ni
o’qing.

### 4. HTTPRoute yaratish

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: web
  namespace: default
spec:
  parentRefs:
    - name: nginx-gateway
      namespace: nginx-gateway
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /web
      backendRefs:
        - name: web-service
          port: 80
```

```bash
kubectl apply -f route.yaml
kubectl get httproute
kubectl describe httproute web | grep -A8 "Conditions"
#   Reason: Accepted ... Status: True
#   Reason: ResolvedRefs ... Status: True
curl http://<gateway-address>/web
```

### 5. Yo’naltirmay qolganda

| Tekshiruv | Nimani anglatadi |
|---|---|
| `kubectl get gatewayclass` → ACCEPTED False | bu class’ni hech bir kontroller amalga oshirmaydi - kontroller ishlayaptimi? |
| `kubectl get gateway` → PROGRAMMED False | kontroller listener’ni rad etdi (port band, TLS ref noto’g’ri) - `describe gateway` |
| `describe httproute` → Accepted False | Gateway’ning `allowedRoutes` i bu namespace’ni chiqarib tashlagan yoki `parentRefs` xato |
| `describe httproute` → ResolvedRefs False | backend Service mavjud emas / port noto’g’ri / boshqa namespace’da |
| hammasi True, lekin curl ishlamaydi | kontrollerga kiradigan yo’l: uning Service’ining NodePort’i, firewall yoki `hostnames` qo’yilgan bo’lsa `Host` header |

```bash
curl -H "Host: shop.example.com" http://<node>:<nodeport>/web    # agar route'da hostnames bo'lsa
kubectl logs -n nginx-gateway deploy/nginx-gateway | tail
```

:::exam-tip
To’rt obyekt, to’rt tekshiruv: GatewayClass **Accepted**, Gateway
**Programmed** (manzil bilan), HTTPRoute **Accepted** va **ResolvedRefs**.
Topshiriqdagi `curl` ishlamasa, ularni shu tartibda bosib chiqing; har
birining `describe` i nima noto’g’riligini aytadi. Va yodda tuting: Route
**ilova** namespace’iga, Gateway esa **kontroller** namespace’iga tushadi -
`parentRefs` namespace’ni ular orasida olib o’tadi.
:::

## Ingress’ni migratsiya qilish

| Ingress | Gateway API |
|---|---|
| `ingressClassName` | Gateway’ning `gatewayClassName` i (bir marta, operator tomonidan qo’yiladi) |
| kontrollerning kirish Service’i | Gateway obyekti |
| `spec.rules[].host` | `HTTPRoute.spec.hostnames` |
| `paths[].path` + `pathType` | `rules[].matches[].path` (`PathPrefix`, `Exact`, `RegularExpression`) |
| `backend.service` | `backendRefs` |
| `rewrite-target` annotation | `filters: URLRewrite` |
| `spec.tls` | Gateway’ning HTTPS listener’idagi `tls.certificateRefs` |

`ingress2gateway` (kubernetes-sigs vositasi) nginx va yana bir nechta
kontroller uchun bu tarjimani bajarib beradi; bitta Ingress uchun qo’lda
qilgan tezroq.

## O’zingizni tekshiring

1. `kind: Gateway` manifest’i umuman apply bo’lishi uchun nima o’rnatilgan
   bo’lishi kerak, keyin esa u Programmed bo’lishi uchun nima kerak?
2. HTTPRoute qaysi namespace’ga tushadi va boshqa namespace’dagi Gateway’ni
   qanday nomlaydi?
3. Gateway’ga `curl` ishlamayapti; to’rtala shart ham True. Muammo qayerda?
