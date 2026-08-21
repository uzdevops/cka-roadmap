## One request, every layer

A browser asks for `https://shop.example.com/watch/movies/1`. Follow it all
the way to a container and back, naming the component at every step. If you
can narrate this from memory, the networking phase is yours.

### 1. Outside the cluster

DNS for `shop.example.com` (your public DNS, not CoreDNS) returns the address
of the entry point: a cloud load balancer, a MetalLB IP, or a node's IP with
a NodePort behind it. The TCP connection lands on **the Gateway controller's
Service** (or the Ingress controller's).

### 2. The entry point

The Service is `type: LoadBalancer` or `NodePort`. **kube-proxy** on the
receiving node has iptables (or IPVS/nftables) rules: destination NodePort
30443 → DNAT to one of the controller Pods' IP:443. The packet now has a
**Pod IP** as its destination.

### 3. To the controller Pod

The node routes it: if the controller Pod is local, through the bridge
(`cni0`) to the Pod's veth; if on another node, via the **CNI**'s route or
overlay to that node, then its bridge. Inside the controller Pod, nginx (or
Envoy) terminates **TLS** with the certificate from the `shop-tls` Secret
referenced by the Gateway listener / Ingress `tls`.

### 4. Routing

The controller matches `Host: shop.example.com`, path `/watch/movies/1`,
against its **HTTPRoute** (or Ingress) rules: `/watch` → `video-service:8080`,
with a URLRewrite/rewrite-target turning the path into `/movies/1`. It opens
a connection to `video-service:8080`.

### 5. Service discovery

`video-service` is resolved by **CoreDNS** - the controller Pod's
`/etc/resolv.conf` points at `10.96.0.10`; the `kubernetes` plugin answers
from its watch of Services: `video-service.app-space.svc.cluster.local →
10.96.44.3`. (Most controllers skip this and watch EndpointSlices directly,
going straight to Pod IPs - but a plain client would resolve the name.)

### 6. The Service, again

A connection to `10.96.44.3:8080` from the controller Pod hits **kube-proxy's**
rules on the controller's node: `KUBE-SERVICES` → `KUBE-SVC-*` → one
`KUBE-SEP-*` chosen at random → DNAT to a video Pod, `10.244.2.7:8080`. The
Service only ever existed as that rule.

### 7. Pod to Pod

`10.244.2.7` is on node02. The **CNI** carries it: a route `10.244.2.0/24 via
192.168.1.12` and out `eth0`, or VXLAN-encapsulated through `flannel.1`. On
node02 it arrives, is decapsulated if needed, goes through `cni0` to the
video Pod's veth and into its namespace as `eth0`.

### 8. Policy

Before delivery, the CNI checks **NetworkPolicies** selecting the video Pod:
if there is an ingress policy, only allowed sources on 8080 get through. The
controller's Pod must be in the allowed `from`.

### 9. The application

The container's process listens on `:8080` - the `containerPort`, matched by
the Service's `targetPort`. It serves `/movies/1`. If it were not Ready, it
would not have been in the EndpointSlice and step 6 would never have picked
it.

### 10. The way back

The reply leaves the video Pod for `10.244.1.x` (the controller Pod); node02
routes it back over the CNI; on the controller's node, **conntrack** un-NATs
the source so the controller sees it come from `10.96.44.3` - the Service it
asked. The controller writes the HTTP response into the TLS connection; the
node un-NATs the NodePort DNAT on the way out; the browser gets its page.

## The same picture as a checklist

| Layer | Component | Breaks as |
|---|---|---|
| entry | LB / NodePort / kube-proxy | connection refused / timeout from outside |
| TLS + routing | Gateway/Ingress controller + its Route/Ingress objects | 404 (no rule), 503 (no endpoints), TLS errors |
| names | CoreDNS | "could not resolve", NXDOMAIN |
| Services | kube-proxy on the **client's** node | name resolves, connection hangs, one node only |
| Pod-to-Pod | CNI DaemonSet, node routes, CNI port in firewall | cross-node hangs, same-node works |
| policy | NetworkPolicy + a CNI that enforces it | hangs for specific sources only |
| app | Pod readiness, `targetPort`, the process | empty endpoints, connection refused at the Pod IP |

:::exam-tip
When a task says "users cannot reach the application", start at the **end**
and work back: is the Pod Ready and listening (`kubectl exec ... curl
localhost:8080`)? Does the Service have endpoints? Does a Pod in the cluster
reach the Service? Does the controller reach it (its logs)? Is the
controller reachable from outside? Each step isolates one layer, and most
faults are in the first two.
:::

## Check yourself

1. In which two places on this path does kube-proxy rewrite a destination?
2. Which component carries the packet from the controller's node to the video
   Pod's node, and which decides whether that Pod may receive it?
3. A request reaches the controller and returns 503. Which step failed, and
   what is the first command?
