## The problem a LoadBalancer per Service creates

One application, exposed: a `LoadBalancer` Service, a cloud load balancer,
an external IP, DNS pointing at it. Fine. Now there are twelve applications:
twelve load balancers, twelve IPs, twelve bills, and no single place to do
TLS or routing by path. And on bare metal there is no cloud to make the
load balancers at all.

**Ingress** puts one thing in front: an **Ingress controller** (a reverse
proxy - nginx, HAProxy, Traefik - running as Pods) with **one** external
entry point, and **Ingress resources** that tell it "host X, path Y → this
Service". Twelve applications, one load balancer, routing by host and path,
TLS termination in one place.

```
internet ─▶ one LB / NodePort ─▶ Ingress controller Pods ─▶ Service wear:8080 (for /wear)
                                                         ─▶ Service video:8080 (for /watch)
```

Kubernetes ships the Ingress **resource type** but **no controller**: like
the CNI, you install one. The nginx Ingress controller is the one the exam
has (and lets you read the docs for).

## The controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.1/deploy/static/provider/baremetal/deploy.yaml
kubectl get all -n ingress-nginx
# deployment.apps/ingress-nginx-controller
# service/ingress-nginx-controller   NodePort   ...  80:30080/TCP,443:30443/TCP
kubectl get ingressclass
# NAME    CONTROLLER             PARAMETERS   AGE
# nginx   k8s.io/ingress-nginx   <none>       1m
```

Under the hood the controller manifest is: a Deployment running nginx with
a controller process that watches Ingress objects and rewrites nginx's
config; a Service to reach it (NodePort or LoadBalancer); a ConfigMap for
nginx settings; a ServiceAccount with RBAC to watch Ingresses, Services and
EndpointSlices; and an **IngressClass** so that Ingress resources can say
which controller they are for.

## The resource

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
    - host: shop.example.com              # optional; no host = any host
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
  defaultBackend:                          # optional: where everything unmatched goes
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
kubectl describe ingress ingress-wear-watch -n app-space      # the rules as a table, plus events from the controller
```

Two things to get right that cost marks:

- The Ingress lives in the **same namespace as the Services it routes to**.
  An Ingress in `default` cannot point at `wear-service` in `app-space`.
- `ingressClassName` (or the older annotation
  `kubernetes.io/ingress.class: nginx`) must name an existing IngressClass,
  or the controller ignores the resource and ADDRESS stays empty.

:::exam-tip
`kubectl create ingress` is the fast path and supports `--rule`
(`host/path=service:port`), `--class`, `--annotation`, and `--default-backend`.
Use it, then `$do` and edit only if you need `pathType: Exact` or TLS.
:::

## Testing

```bash
curl -H "Host: shop.example.com" http://<node-ip>:30080/wear
kubectl get svc -n ingress-nginx        # which NodePort / external IP the controller has
kubectl logs -n ingress-nginx deploy/ingress-nginx-controller | tail   # the nginx access log: you see your request, and 404s
```

A `404` from nginx means the request reached the controller but no rule
matched (wrong host, wrong path, wrong namespace); a `503` means a rule
matched but the Service has no endpoints; a connection refused means you
have the controller's port wrong.

## Check yourself

1. What does Kubernetes provide for Ingress, and what do you have to install?
2. Why must an Ingress be in the same namespace as its backend Services?
3. Your Ingress shows no ADDRESS and the controller ignores it. Which field
   do you check first?
