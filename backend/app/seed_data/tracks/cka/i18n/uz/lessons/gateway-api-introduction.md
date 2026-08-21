## Ingress ayta olmagan narsalar

Ingress bitta ishni qilardi - HTTP host/path yo’naltirish - qolgan hamma
narsa esa faqat bitta kontroller tushunadigan annotation edi. Yana bir
kamchiligi: bitta obyekt butunlay boshqa ikki toifa odam uchun edi - kirish
nuqtasini boshqaradigan platforma jamoasi va o’z path’larini yo’naltiradigan
ilova jamoasi. **Gateway API** - ana shu qayta loyihalash: rollarga
yo’naltirilgan resurslar to’plami, shu qadar ifodaliki, trafikni taqsimlash,
header bo’yicha moslashtirish, TCP/UDP/gRPC yo’naltirish va TLS -
annotation emas, **maydon**lar, va implementatsiyalar orasida ko’chma.

```
GatewayClass (cluster-scoped)  ─ "qaysi kontroller"          - infratuzilma provayderi
      │
Gateway (namespaced)           ─ "80/443 portdagi listener"  - platforma / klaster operatori
      │
HTTPRoute / TCPRoute / ...     ─ "shu host+path -> shu Service" - ilova dasturchisi
```

| Resurs | Egasi | O’xshashi |
|---|---|---|
| **GatewayClass** | implementatsiya qiluvchi (nginx, Istio, Envoy Gateway, cloud LB) | IngressClass |
| **Gateway** | klaster operatori | Ingress kontrollerining kirish nuqtasi, siz yaratadigan obyekt sifatida |
| **HTTPRoute** (GRPCRoute, TCPRoute, TLSRoute, UDPRoute) | ilova jamoasi | Ingress qoidalari |

Route’lar Gateway’ga (`parentRefs` orqali) **ulanadi**, Gateway esa qaysi
namespace’lardagi route’larni qabul qilishini hal qiladi. Ingress’da
yetishmagan rol bo’linishi ana shu.

## Obyektlar

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: nginx
spec:
  controllerName: gateway.nginx.org/nginx-gateway-controller
```

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
          from: All                # yoki Same, yoki Selector
    - name: https
      protocol: HTTPS
      port: 443
      tls:
        certificateRefs:
          - name: shop-tls         # Secret
```

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: web-route
  namespace: app-space
spec:
  parentRefs:
    - name: nginx-gateway
      namespace: nginx-gateway
  hostnames: ["shop.example.com"]
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /wear
      backendRefs:
        - name: wear-service
          port: 8080
    - matches:
        - path:
            type: PathPrefix
            value: /watch
      filters:
        - type: URLRewrite                  # rewrite-target, maydon sifatida
          urlRewrite:
            path:
              type: ReplacePrefixMatch
              replacePrefixMatch: /
      backendRefs:
        - name: video-service
          port: 8080
```

nginx annotation darsi bilan solishtiring: bu yerda qayta yozish -
`filters: [{type: URLRewrite, ...}]` - hamma joyda bir xil, hech qanday
vendor prefiksisiz.

## Ingress (annotation’siz) qila olmaydigan narsalar

```yaml
rules:
  - matches:
      - headers:
          - name: x-canary
            value: "true"                 # header bo'yicha yo'naltirish
    backendRefs:
      - name: web-v2
        port: 80
  - backendRefs:
      - name: web-v1
        port: 80
        weight: 90                          # trafikni taqsimlash
      - name: web-v2
        port: 80
        weight: 10
```

Header va method bo’yicha moslashtirish, vaznli backend’lar, so’rov/javob
header’larini o’zgartirish, redirect’lar, mirroring - hammasi tipli maydon
sifatida. Ustiga boshqa Route turlari orqali HTTP bo’lmagan protokollar.

## Status va tekshiriladigan narsalar

```bash
kubectl get gatewayclass                    # ACCEPTED True mi?
kubectl get gateway -A                      # PROGRAMMED True, ADDRESS berilganmi?
kubectl get httproute -A
kubectl describe httproute web-route -n app-space | grep -A10 Status
#   Conditions: Accepted True / ResolvedRefs True        <- ulangan, va backend'lar mavjud
```

`Accepted: False` bo’lgan route’ni Gateway rad etgan - odatda Gateway’ning
`allowedRoutes` i route’ning namespace’ini o’z ichiga olmaydi yoki
`parentRefs` uni noto’g’ri nomlaydi. `ResolvedRefs: False` esa `backendRefs`
dagi Service mavjud emasligini bildiradi (yoki u ReferenceGrant’siz boshqa
namespace’da).

:::exam-tip
2025-yilgi dastur "Gateway API’ni tushunish va undan foydalanish" deydi.
Kuting: berilgan manifest’dan CRD’lar va kontrollerni o’rnatish, HTTP
listener’li Gateway yaratish, path’ni Service’ga yuboradigan HTTPRoute
yaratish, `kubectl get gateway` ADDRESS ko’rsatayotgani va u orqali `curl`
ishlashini tasdiqlash. Uchta obyekt va ularning `status` shartlari - butun
ko’nikma shu.
:::

## O’zingizni tekshiring

1. Gateway API’ning uchta resursini va har birining egasini ayting.
2. HTTPRoute Gateway’ga qanday ulanadi va Gateway’dagi nima uni rad eta
   oladi?
3. Ingress’da faqat annotation sifatida bo’lgan, Gateway API’da esa maydon
   bo’lgan ikkita yo’naltirish imkoniyatini ayting.
