## Why Pods need something in front of them

Pod IPs change. Every time a Deployment rolls, every time a node drains, the
Pods behind your application are new Pods with new addresses. Nothing can be
configured to talk to a Pod IP and stay working. A **Service** is the stable
thing: one name, one virtual IP, and a selector that keeps the list of
backends current as Pods come and go.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  type: ClusterIP          # the default; covered next lesson
  selector:
    app: web
  ports:
    - port: 80             # the Service's port
      targetPort: 8080     # the container's port
      protocol: TCP
```

Three fields do the work:

- **selector** - which Pods are behind it. The endpoint controller turns this
  into an **EndpointSlice** listing the matching Pods' IPs and ports.
- **port** - what clients connect to on the Service.
- **targetPort** - what the Pod actually listens on. If omitted it equals
  `port`. It can also be a *name*, matching a named `containerPort`, which
  lets you change the container's port without touching the Service.

## The three types

| Type | Reachable from | Gets |
|---|---|---|
| **ClusterIP** | inside the cluster only | a virtual IP from the service CIDR |
| **NodePort** | every node's IP, on a high port | a ClusterIP **plus** a port 30000-32767 opened on every node |
| **LoadBalancer** | the outside world, via a cloud load balancer | a NodePort **plus** an external IP provisioned by the cloud |

They nest: a LoadBalancer is a NodePort is a ClusterIP. This lesson walks the
NodePort; the next two cover ClusterIP in depth and LoadBalancer.

## NodePort, walked through

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-np
spec:
  type: NodePort
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080     # optional; omit and one is chosen from the range
```

Three ports in one spec, and the names confuse everyone once:

```
client ──▶ <any node IP>:30080 (nodePort) ──▶ 10.96.x.x:80 (port, the ClusterIP) ──▶ 10.244.x.x:8080 (targetPort, the Pod)
```

The **only mandatory one is `port`**. `targetPort` defaults to `port`,
`nodePort` is allocated if missing.

```bash
kubectl expose deployment web --name=web-np --type=NodePort --port=80 --target-port=8080
kubectl get svc web-np
# NAME     TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
# web-np   NodePort   10.96.14.201   <none>        80:31234/TCP   3s
curl http://<node-ip>:31234
```

A NodePort is opened on **every** node, even nodes that run none of the Pods -
kube-proxy forwards it across the cluster network. That is convenient and
slightly wasteful; it is also why NodePorts are for development and for
sitting behind your own load balancer, not for exposing production apps one by
one.

:::exam-tip
`kubectl expose` cannot set `nodePort`. When a task asks for a specific node
port: `kubectl expose ... --type=NodePort --dry-run=client -o yaml > svc.yaml`,
add `nodePort: 30080` under the port entry, then `kubectl apply -f svc.yaml`.
:::

## When a Service "does not work"

```bash
kubectl get endpoints web          # or: kubectl get endpointslices -l kubernetes.io/service-name=web
kubectl describe svc web | grep -E "Selector|Endpoints|Port"
kubectl get pods -l app=web -o wide
```

| You see | It means |
|---|---|
| `Endpoints: <none>` | selector matches no Pods (label typo) or the Pods are not Ready |
| endpoints listed but connection refused | `targetPort` is not what the container listens on |
| works from inside the cluster, not from outside | it is a ClusterIP and you wanted NodePort/LoadBalancer |
| name does not resolve | CoreDNS, or you are in a different namespace and used the short name |

:::tip
Pods that fail their readiness probe are removed from the endpoints. A Service
with healthy-looking Pods and empty endpoints usually means "not Ready" -
check `kubectl get pods` READY column before the selector.
:::

## Check yourself

1. Name the three ports in a NodePort Service and what each one is.
2. Which of them is mandatory, and what do the others default to?
3. `kubectl get endpoints web` prints `<none>` although three Pods are Running.
   What are the two likely causes?
