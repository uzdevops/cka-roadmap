## What Ingress could not say

Ingress did one thing - HTTP host/path routing - and everything else was an
annotation that only one controller understood. It also had one object for
two very different people: the platform team that runs the entry point and
the application team that routes its paths. The **Gateway API** is the
redesign: a set of resources, role-oriented, expressive enough that
traffic-splitting, header matching, TCP/UDP/gRPC routing and TLS are
**fields**, not annotations, and portable across implementations.

```
GatewayClass (cluster-scoped)  ─ "which controller"         - the infrastructure provider
      │
Gateway (namespaced)           ─ "a listener on port 80/443" - the platform / cluster operator
      │
HTTPRoute / TCPRoute / ...     ─ "this host+path -> this Service" - the application developer
```

| Resource | Owned by | Analogy |
|---|---|---|
| **GatewayClass** | the implementer (nginx, Istio, Envoy Gateway, cloud LB) | IngressClass |
| **Gateway** | cluster operator | the Ingress controller's entry point, as an object you create |
| **HTTPRoute** (GRPCRoute, TCPRoute, TLSRoute, UDPRoute) | app team | the Ingress rules |

Routes **attach** to a Gateway (by `parentRefs`), and the Gateway decides
which namespaces' routes it accepts. That is the role split Ingress lacked.

## The objects

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
          from: All                # or Same, or Selector
    - name: https
      protocol: HTTPS
      port: 443
      tls:
        certificateRefs:
          - name: shop-tls         # a Secret
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
        - type: URLRewrite                  # rewrite-target, as a field
          urlRewrite:
            path:
              type: ReplacePrefixMatch
              replacePrefixMatch: /
      backendRefs:
        - name: video-service
          port: 8080
```

Compare to the nginx annotation lesson: the rewrite is
`filters: [{type: URLRewrite, ...}]` - the same everywhere, no vendor
prefix.

## What it can do that Ingress cannot (without annotations)

```yaml
rules:
  - matches:
      - headers:
          - name: x-canary
            value: "true"                 # route by header
    backendRefs:
      - name: web-v2
        port: 80
  - backendRefs:
      - name: web-v1
        port: 80
        weight: 90                          # traffic splitting
      - name: web-v2
        port: 80
        weight: 10
```

Header and method matching, weighted backends, request/response header
modification, redirects, mirroring - all as typed fields. Plus non-HTTP
protocols through the other Route kinds.

## Status and the things to check

```bash
kubectl get gatewayclass                    # ACCEPTED True?
kubectl get gateway -A                      # PROGRAMMED True, ADDRESS assigned?
kubectl get httproute -A
kubectl describe httproute web-route -n app-space | grep -A10 Status
#   Conditions: Accepted True / ResolvedRefs True        <- attached, and backends exist
```

A route with `Accepted: False` was refused by the Gateway - usually the
Gateway's `allowedRoutes` does not include the route's namespace, or
`parentRefs` names it wrong. `ResolvedRefs: False` means a `backendRefs`
Service does not exist (or is in another namespace without a
ReferenceGrant).

:::exam-tip
The 2025 curriculum says "understand and use Gateway API". Expect: install
the CRDs and a controller from a supplied manifest, create a Gateway with
an HTTP listener, create an HTTPRoute sending a path to a Service, confirm
with `kubectl get gateway` showing an ADDRESS and `curl` through it. The
three objects and their `status` conditions are the whole skill.
:::

## Check yourself

1. Name the three Gateway API resources and who owns each.
2. How does an HTTPRoute connect to a Gateway, and what on the Gateway can
   refuse it?
3. Give two routing capabilities the Gateway API has as fields that Ingress
   only had as annotations.
