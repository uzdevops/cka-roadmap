## Kontrollerga xos xatti-harakat qayerda yashaydi

Ingress resursi ataylab kichik: host’lar, path’lar, backend’lar, TLS. Haqiqiy
reverse proxy bundan tashqari qila oladigan hamma narsa - path’ni qayta
yozish, timeout belgilash, so’rov hajmini cheklash, HTTP’ni HTTPS’ga
yo’naltirish, header qo’shish, sticky session - kontrollerga xos, va Ingress
API’ning buning uchun zaxira yo’li - kontroller prefiksi bilan
**annotation**’lar:

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    nginx.ingress.kubernetes.io/proxy-body-size: 50m
    nginx.ingress.kubernetes.io/proxy-read-timeout: "120"
```

Boshqa kontroller nginx’ning annotation’larini e’tiborsiz qoldiradi (va o’z
prefiksi bor: `traefik.ingress.kubernetes.io/`, `haproxy.org/`). Keyingi
darsdagi Gateway API qisman shularni to’laqonli maydonlarga aylantirish uchun
ishlab chiqilgan.

## Sizga aslida kerak bo’ladigan yagona annotation: rewrite-target

So’rov - `http://shop.example.com/watch`. Ingress `/watch` ni
`video-service:8080` ga yo’naltiradi. Video ilovasi o’z sahifalarini `/` da
beradi - u `/watch` haqida hech qachon eshitmagan. Yordamsiz nginx so’rovni
Service’ga `GET /watch` sifatida uzatadi va ilova 404 qaytaradi.

```
client: GET /watch  ──▶ nginx ──▶ video-service: GET /watch   -> 404 (app only knows /)
```

`rewrite-target` uzatishdan oldin path’ni qayta yozadi:

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
    - http:
        paths:
          - path: /watch
            pathType: Prefix
            backend: {service: {name: video-service, port: {number: 8080}}}
```

```
client: GET /watch  ──▶ nginx ──▶ video-service: GET /   -> 200
```

`rewrite-target: /` bilan `/watch` ostidagi **hamma narsa** `/` ga aylanadi -
ya’ni `/watch/movies/1` ham `/` bo’lib qoladi, bu esa odatda siz xohlagan
narsa emas.

## Path’ning qolgan qismini saqlash: capture group’lar

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
spec:
  rules:
    - http:
        paths:
          - path: /watch(/|$)(.*)
            pathType: ImplementationSpecific
            backend: {service: {name: video-service, port: {number: 8080}}}
```

Bu yerda path - regex (shuning uchun ham `pathType` `ImplementationSpecific`
bo’lishi kerak - nginx’ning regex qo’llab-quvvatlashi implementatsiya
tafsiloti); `$2` - ikkinchi capture group, ya’ni `/watch/` dan keyin kelgan
narsa. `/watch/movies/1` → `/movies/1`; `/watch` → `/`. Bu ingress-nginx
hujjatlari "Rewrite" bo’limida ko’rsatadigan shakl.

:::exam-tip
Imtihon kerak bo’lganda annotation matnini o’zi beradi
("`nginx.ingress.kubernetes.io/rewrite-target: /` annotation’ini qo’shing").
Uni Service’ning yoki kontrollerning emas, **Ingress**’ning
`metadata.annotations` qismiga qo’ying. `kubectl create ingress` bilan bu -
`--annotation nginx.ingress.kubernetes.io/rewrite-target=/`.
:::

## Tanib olishga arziydigan boshqa annotation’lar

| Annotation | Ta’siri |
|---|---|
| `nginx.ingress.kubernetes.io/ssl-redirect: "false"` | HTTPS’ni majburlamaslik (sukut bo’yicha Ingress’da TLS bo’lsa yo’naltiriladi) |
| `nginx.ingress.kubernetes.io/force-ssl-redirect: "true"` | Ingress’da TLS bo’lmasa ham yo’naltirish (tashqi TLS terminatori ortida) |
| `nginx.ingress.kubernetes.io/proxy-body-size` | maksimal yuklash hajmi (sukut bo’yicha 1m - "413 Request Entity Too Large" ning sababi) |
| `nginx.ingress.kubernetes.io/affinity: cookie` | sticky session’lar |
| `nginx.ingress.kubernetes.io/backend-protocol: HTTPS` | backend bilan TLS orqali gaplashish |
| `nginx.ingress.kubernetes.io/whitelist-source-range` | klient CIDR’lari uchun ruxsat ro’yxati |
| `nginx.ingress.kubernetes.io/app-root` | `/` ni sub-path’ga yo’naltirish |

Qiymatlar YAML’da **string** bo’lishi shart: `"false"`, `"120"` - yalang’och
`false` "expected string" bilan rad etiladi.

## Shu yerda ekansiz, TLS haqida

```yaml
spec:
  tls:
    - hosts: [shop.example.com]
      secretName: shop-tls            # AYNAN SHU namespace dagi kubernetes.io/tls Secret
  rules:
    - host: shop.example.com
      http: ...
```

```bash
kubectl create secret tls shop-tls --cert=shop.crt --key=shop.key -n app-space
```

Kontroller TLS’ni o’sha sertifikat bilan tugatadi va Service’ga oddiy HTTP
uzatadi. Sertifikatlar uchun yagona joy - Ingress nega mavjudligining
ikkinchi yarmi.

## O’zingizni tekshiring

1. Nega `rewrite-target` bo’lmasa `/watch → video-service` 404 qaytaradi va
   `rewrite-target: /` `/watch/movies/1` ga nima qiladi?
2. `/watch(/|$)(.*)` path’i bilan `rewrite-target: /$2` `/watch/movies/1`
   uchun nimani uzatadi va buning uchun qaysi `pathType` kerak?
3. Annotation qayerga yoziladi va uni `kubectl create ingress` bilan qo’shishning
   bitta bayroqdan iborat usuli qanday?
