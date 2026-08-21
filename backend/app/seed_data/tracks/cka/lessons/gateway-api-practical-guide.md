## From nothing to routed traffic

A Gateway API setup is four steps. Do them on a lab cluster once and the
exam version is the same steps with the files handed to you.

### 1. Install the CRDs

The Gateway API resources are **not** built into Kubernetes; they are CRDs,
versioned separately:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.1.0/standard-install.yaml
kubectl get crd | grep gateway.networking.k8s.io
# gatewayclasses.gateway.networking.k8s.io
# gateways.gateway.networking.k8s.io
# httproutes.gateway.networking.k8s.io
# grpcroutes..., referencegrants...
```

`standard-install.yaml` is the stable set; `experimental-install.yaml` adds
TCPRoute/UDPRoute/TLSRoute.

### 2. Install a controller

The CRDs define the API; something has to implement it. NGINX Gateway
Fabric, Envoy Gateway, Istio, Contour, Cilium and the cloud providers'
controllers all do. For a lab:

```bash
kubectl apply -f https://raw.githubusercontent.com/nginxinc/nginx-gateway-fabric/v1.3.0/deploy/crds.yaml
kubectl apply -f https://raw.githubusercontent.com/nginxinc/nginx-gateway-fabric/v1.3.0/deploy/default/deploy.yaml
kubectl get pods -n nginx-gateway
kubectl get gatewayclass
# NAME    CONTROLLER                                   ACCEPTED   AGE
# nginx   gateway.nginx.org/nginx-gateway-controller   True       30s
```

The controller's manifest usually creates the GatewayClass for you. If it
did not, you write one with the controller's `controllerName`.

### 3. Create a Gateway

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
kubectl get svc -n nginx-gateway         # the controller's Service: LoadBalancer or NodePort - this is how traffic gets in
```

`PROGRAMMED True` means the controller configured itself for this Gateway.
On a cluster with no load balancer the ADDRESS may be the NodePort
Service's node IP, or empty with the Service still reachable on its
NodePort - read `kubectl get svc` in the controller's namespace.

### 4. Create an HTTPRoute

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

### 5. When it does not route

| Check | Means |
|---|---|
| `kubectl get gatewayclass` → ACCEPTED False | no controller implements this class - is the controller running? |
| `kubectl get gateway` → PROGRAMMED False | the controller rejected a listener (port in use, bad TLS ref) - `describe gateway` |
| `describe httproute` → Accepted False | Gateway's `allowedRoutes` excludes this namespace, or `parentRefs` wrong |
| `describe httproute` → ResolvedRefs False | the backend Service does not exist / wrong port / other namespace |
| everything True, curl fails | the path into the controller: its Service's NodePort, firewall, or `Host` header if `hostnames` is set |

```bash
curl -H "Host: shop.example.com" http://<node>:<nodeport>/web    # if the route has hostnames
kubectl logs -n nginx-gateway deploy/nginx-gateway | tail
```

:::exam-tip
Four objects, four checks: GatewayClass **Accepted**, Gateway
**Programmed** (with an address), HTTPRoute **Accepted** and
**ResolvedRefs**. Walk them in order when a task's `curl` fails; each one's
`describe` says what is wrong. And remember the Route goes in the
**application's** namespace, the Gateway in the **controller's** - the
`parentRefs` carries the namespace across.
:::

## Migrating an Ingress

| Ingress | Gateway API |
|---|---|
| `ingressClassName` | Gateway's `gatewayClassName` (set once, by the operator) |
| the controller's entry Service | the Gateway object |
| `spec.rules[].host` | `HTTPRoute.spec.hostnames` |
| `paths[].path` + `pathType` | `rules[].matches[].path` (`PathPrefix`, `Exact`, `RegularExpression`) |
| `backend.service` | `backendRefs` |
| `rewrite-target` annotation | `filters: URLRewrite` |
| `spec.tls` | the Gateway's HTTPS listener `tls.certificateRefs` |

`ingress2gateway` (a kubernetes-sigs tool) does the translation for nginx
and a few other controllers; for one Ingress it is quicker by hand.

## Check yourself

1. What has to be installed before a `kind: Gateway` manifest will even
   apply, and then what before it becomes Programmed?
2. Which namespace does the HTTPRoute go in, and how does it name a Gateway
   in a different one?
3. `curl` to the Gateway fails; all four conditions are True. Where is the
   problem?
