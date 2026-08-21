## The API moved; the old examples did not

Ingress spent years in `extensions/v1beta1` and then `networking.k8s.io/v1beta1`,
and most of the internet's examples were written then. Since Kubernetes
1.19 the only served version is **`networking.k8s.io/v1`**, and the shape
changed. This note is the translation table, so that a copied manifest does
not fail with `no matches for kind "Ingress" in version "extensions/v1beta1"`.

## What changed

| v1beta1 (old) | v1 (now) |
|---|---|
| `apiVersion: extensions/v1beta1` or `networking.k8s.io/v1beta1` | `apiVersion: networking.k8s.io/v1` |
| `backend: {serviceName: x, servicePort: 80}` | `backend: {service: {name: x, port: {number: 80}}}` |
| `kubernetes.io/ingress.class: nginx` annotation | `spec.ingressClassName: nginx` (annotation still honoured by nginx, deprecated) |
| `pathType` optional / absent | `pathType` **required**: `Prefix`, `Exact`, or `ImplementationSpecific` |
| `spec.backend` (default) | `spec.defaultBackend` |
| `port: {number: 80}` only | `port: {number: 80}` **or** `port: {name: http}` (a named Service port) |

```yaml
# old
backend:
  serviceName: wear-service
  servicePort: 8080

# new
backend:
  service:
    name: wear-service
    port:
      number: 8080
```

```bash
kubectl convert -f old-ingress.yaml --output-version networking.k8s.io/v1   # the kubectl-convert plugin rewrites it
kubectl explain ingress.spec.rules.http.paths.backend --recursive            # the v1 shape, from the server
```

## pathType, precisely

| pathType | `/wear` matches |
|---|---|
| `Exact` | only `/wear` |
| `Prefix` | `/wear`, `/wear/`, `/wear/anything` - split on `/`, so **not** `/wearable` |
| `ImplementationSpecific` | whatever the controller decides (nginx: like Prefix, plus regex if the annotation asks) |

`Prefix` is what you want nearly always. Forgetting `pathType` is the v1
error you will see most:
`spec.rules[0].http.paths[0].pathType: Required value`.

## IngressClass

v1 made the class a real object, so a cluster can run two controllers (nginx
for internal, Traefik for edge) and each Ingress says which one it is for:

```yaml
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: nginx
  annotations:
    ingressclass.kubernetes.io/is-default-class: "true"    # Ingresses with no class get this one
spec:
  controller: k8s.io/ingress-nginx
```

```bash
kubectl get ingressclass
```

An Ingress with **no** `ingressClassName` and **no** default class is
processed by nobody. When a controller "does nothing", that is the check.

:::exam-tip
The exam clusters are current: write `networking.k8s.io/v1`, include
`pathType`, use `ingressClassName`. `kubectl create ingress` does all three
for you, which is one more reason to generate rather than type.
:::

## Reading an Ingress back

```bash
kubectl get ingress -A
kubectl describe ingress ingress-wear-watch -n app-space
# Rules:
#   Host              Path  Backends
#   shop.example.com  /wear   wear-service:8080 (10.244.1.5:8080,10.244.2.7:8080)
#                     /watch  video-service:8080 (<none>)        <- no endpoints: this path will 503
```

`describe` resolves each backend to its endpoints; `<none>` next to a
backend is the fastest way to see which Service is the broken link.

## Check yourself

1. Rewrite `backend: {serviceName: api, servicePort: 80}` in the v1 shape.
2. Which field became required in v1, and what are its three values?
3. An Ingress has no `ingressClassName` and the cluster has no default
   IngressClass. What happens?
