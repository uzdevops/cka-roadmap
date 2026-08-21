## Where the controller-specific behaviour lives

The Ingress resource is deliberately small: hosts, paths, backends, TLS.
Everything a real reverse proxy can do beyond that - rewrite the path, set
timeouts, limit request size, redirect HTTP to HTTPS, add headers, sticky
sessions - is controller-specific, and the Ingress API's escape hatch for it
is **annotations** with the controller's prefix:

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    nginx.ingress.kubernetes.io/proxy-body-size: 50m
    nginx.ingress.kubernetes.io/proxy-read-timeout: "120"
```

Another controller ignores nginx's annotations (and has its own prefix:
`traefik.ingress.kubernetes.io/`, `haproxy.org/`). The Gateway API, next
lesson, was designed partly to make these first-class fields instead.

## The one annotation you will actually need: rewrite-target

The request is `http://shop.example.com/watch`. The Ingress routes `/watch`
to `video-service:8080`. The video application serves its pages at `/` -
it has never heard of `/watch`. Without help, nginx forwards the request as
`GET /watch` to the Service, and the app answers 404.

```
client: GET /watch  ──▶ nginx ──▶ video-service: GET /watch   -> 404 (app only knows /)
```

`rewrite-target` rewrites the path before forwarding:

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

With `rewrite-target: /`, **everything** under `/watch` becomes `/` - so
`/watch/movies/1` also becomes `/`, which is usually not what you want.

## Keeping the rest of the path: capture groups

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

The path is a regex (which is why `pathType` must be
`ImplementationSpecific` - nginx's regex support is an implementation
detail); `$2` is the second capture group - whatever followed `/watch/`.
`/watch/movies/1` → `/movies/1`; `/watch` → `/`. This is the form the
ingress-nginx documentation shows under "Rewrite".

:::exam-tip
The exam gives you the annotation text when it wants it ("add the
annotation `nginx.ingress.kubernetes.io/rewrite-target: /`"). Put it under
`metadata.annotations` of the **Ingress**, not the Service, not the
controller. With `kubectl create ingress` it is
`--annotation nginx.ingress.kubernetes.io/rewrite-target=/`.
:::

## Other annotations worth recognising

| Annotation | Effect |
|---|---|
| `nginx.ingress.kubernetes.io/ssl-redirect: "false"` | do not force HTTPS (the default is to redirect when the Ingress has TLS) |
| `nginx.ingress.kubernetes.io/force-ssl-redirect: "true"` | redirect even without TLS on the Ingress (behind an external TLS terminator) |
| `nginx.ingress.kubernetes.io/proxy-body-size` | max upload size (default 1m - the cause of "413 Request Entity Too Large") |
| `nginx.ingress.kubernetes.io/affinity: cookie` | sticky sessions |
| `nginx.ingress.kubernetes.io/backend-protocol: HTTPS` | talk TLS to the backend |
| `nginx.ingress.kubernetes.io/whitelist-source-range` | allow-list client CIDRs |
| `nginx.ingress.kubernetes.io/app-root` | redirect `/` to a sub-path |

Values must be **strings** in YAML: `"false"`, `"120"` - a bare `false` is
rejected with "expected string".

## TLS, since you are here

```yaml
spec:
  tls:
    - hosts: [shop.example.com]
      secretName: shop-tls            # a kubernetes.io/tls Secret in the SAME namespace
  rules:
    - host: shop.example.com
      http: ...
```

```bash
kubectl create secret tls shop-tls --cert=shop.crt --key=shop.key -n app-space
```

The controller terminates TLS with that certificate and forwards plain HTTP
to the Service. One place for certificates - the other half of why Ingress
exists.

## Check yourself

1. Why does `/watch → video-service` return 404 without `rewrite-target`,
   and what does `rewrite-target: /` do to `/watch/movies/1`?
2. What does `rewrite-target: /$2` with path `/watch(/|$)(.*)` forward for
   `/watch/movies/1`, and which `pathType` does that need?
3. Where does the annotation go, and what is the one-flag way to add it with
   `kubectl create ingress`?
