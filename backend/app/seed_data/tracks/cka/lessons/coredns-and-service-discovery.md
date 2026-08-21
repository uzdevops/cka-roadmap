## CoreDNS as it runs in the cluster

```bash
kubectl get deployment coredns -n kube-system          # 2 replicas on kubeadm
kubectl get pods -n kube-system -l k8s-app=kube-dns -o wide
kubectl get svc kube-dns -n kube-system                # ClusterIP 10.96.0.10 - the address in every resolv.conf
kubectl get configmap coredns -n kube-system -o yaml   # the Corefile
```

Three objects: a Deployment (the DNS server Pods, label `k8s-app=kube-dns`
for historical reasons), a Service (`kube-dns`, the fixed ClusterIP the
kubelet hands to Pods), and a ConfigMap (the Corefile). Plus a
ServiceAccount and ClusterRole so the `kubernetes` plugin may watch Services
and EndpointSlices.

## The Corefile, line by line

```
.:53 {
    errors
    health { lameduck 5s }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
       pods insecure
       fallthrough in-addr.arpa ip6.arpa
       ttl 30
    }
    prometheus :9153
    forward . /etc/resolv.conf { max_concurrent 1000 }
    cache 30
    loop
    reload
    loadbalance
}
```

| Line | Effect |
|---|---|
| `kubernetes cluster.local ...` | answer `*.cluster.local` (and reverse lookups) from the API: Services → ClusterIP, headless → Pod IPs |
| `pods insecure` | allow `<dashed-ip>.<ns>.pod.cluster.local` names |
| `forward . /etc/resolv.conf` | everything else goes to the resolvers in the **CoreDNS Pod's** resolv.conf - which, because the Deployment has `dnsPolicy: Default`, is the **node's** resolv.conf |
| `cache 30` | cache for 30 s - why a Service change takes up to 30 s to be seen |
| `loop` | if the forward target is CoreDNS itself, log it and exit - a crash loop that names the cause |
| `reload` | watch the Corefile and reload on change - edit the ConfigMap, wait ~2 minutes |
| `health`, `ready` | liveness on :8080, readiness on :8181 |

`cluster.local` here must match the kubelet's `clusterDomain`. They agree on
a kubeadm cluster; change one without the other and nothing resolves.

## How a Service becomes a record

The `kubernetes` plugin **watches** Services and EndpointSlices - it does
not poll. Create a Service and the record exists within a second; no
restart, no reload. That is why CoreDNS needs RBAC (list/watch on services,
endpointslices, namespaces) and why a CoreDNS that is up but has lost its
ServiceAccount token answers NXDOMAIN for everything in the cluster.

```bash
kubectl logs -n kube-system -l k8s-app=kube-dns
# [ERROR] ... failed to list *v1.Service: ... forbidden        <- RBAC/token problem
# [FATAL] plugin/loop: Loop ... detected                        <- forward loop
# [INFO] 10.244.1.5:43892 - 12345 "A IN web.payroll.svc.cluster.local. udp 45 false 512" NOERROR ...   (with `log` enabled)
```

## The failure modes and their fix

| Symptom | Cause | Fix |
|---|---|---|
| nothing resolves, CoreDNS Pods Pending/CrashLoopBackOff | no CNI / loop detected / bad Corefile | fix the CNI; fix the node's resolv.conf (`127.0.0.53` on Ubuntu → use `/run/systemd/resolve/resolv.conf`); fix the ConfigMap |
| cluster names fail, external work | `kubernetes` plugin errors | `kubectl logs` - RBAC, or `clusterDomain` mismatch |
| external names fail, cluster names work | `forward` target unreachable | the nodes' resolvers, NetworkPolicy on 53 egress from `kube-system`, firewall |
| one Pod cannot resolve | its `resolv.conf` / `dnsPolicy` | `kubectl exec <pod> -- cat /etc/resolv.conf` |
| a Service resolves to the wrong IP / stale | cache | wait 30 s; `kubectl rollout restart deployment coredns -n kube-system` if impatient |

:::exam-tip
The universal test, in order: (1) `kubectl get pods -n kube-system -l
k8s-app=kube-dns` - Running? (2) `kubectl exec <pod> -- nslookup kubernetes` -
the cluster's own API Service; if this fails DNS is down, if it works DNS is
fine and the problem is the *name* being asked for (namespace, typo). (3)
`kubectl logs` of CoreDNS for the error line.
:::

## Editing the Corefile

```bash
kubectl edit configmap coredns -n kube-system
# e.g. add a server block:
#   corp.internal:53 { forward . 10.10.0.53 }
# or change forward . /etc/resolv.conf to forward . 8.8.8.8
kubectl rollout restart deployment coredns -n kube-system     # only if you cannot wait for `reload`
```

Changing `forward` to a public resolver is the quick fix for a lab node
whose own resolv.conf is the systemd stub; in production you fix the node.

## Check yourself

1. Which three Kubernetes objects make up CoreDNS, and which one does every
   Pod's `resolv.conf` point at?
2. A new Service resolves within a second without any restart. Why?
3. Cluster names resolve; `google.com` does not. Which Corefile line, and
   what is behind it?
