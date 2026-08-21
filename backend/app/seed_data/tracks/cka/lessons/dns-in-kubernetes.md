## Every Service has a name

When a Service is created, CoreDNS - the cluster's DNS, itself a Deployment
watching the API - publishes a record for it:

```
<service>.<namespace>.svc.cluster.local   ->  ClusterIP
```

```bash
kubectl get svc -n payroll
# web-service   ClusterIP   10.96.5.20   ...
kubectl run t --rm -it --image=busybox:1.36 -- nslookup web-service.payroll.svc.cluster.local
# Name:    web-service.payroll.svc.cluster.local
# Address: 10.96.5.20
```

| From a Pod in... | You can use |
|---|---|
| the same namespace (`payroll`) | `web-service` |
| another namespace | `web-service.payroll` |
| anywhere, unambiguous | `web-service.payroll.svc` or the full `web-service.payroll.svc.cluster.local` |

The short forms work because of the **search list** the kubelet writes into
every Pod's `/etc/resolv.conf`:

```bash
kubectl exec t -- cat /etc/resolv.conf
# nameserver 10.96.0.10                                     <- the kube-dns Service (CoreDNS)
# search default.svc.cluster.local svc.cluster.local cluster.local
# options ndots:5
```

`nslookup web-service` from namespace `default` tries
`web-service.default.svc.cluster.local` (NXDOMAIN), then
`web-service.svc.cluster.local` (NXDOMAIN), then
`web-service.cluster.local`, then the bare name. `web-service.payroll` hits
on the second suffix: `web-service.payroll.svc.cluster.local`. That is why
"Service in another namespace" needs the namespace and nothing more.

## Pods have names too, sort of

```
<dashed-ip>.<namespace>.pod.cluster.local   ->  10-244-1-5.default.pod.cluster.local -> 10.244.1.5
```

Only if CoreDNS's `kubernetes` plugin has `pods insecure` (the kubeadm
default does), and nobody uses it - a Pod's IP is not stable. What *is*
useful: the per-Pod names a **headless Service** and a StatefulSet create -
`db-0.db.payroll.svc.cluster.local` - which the storage phase covered.

## Record types

```bash
nslookup web-service.payroll.svc.cluster.local              # A: the ClusterIP
nslookup -type=srv _http._tcp.web-service.payroll.svc.cluster.local   # SRV: port number, for named ports
nslookup db.payroll.svc.cluster.local                        # headless: several A records, one per Pod
```

## The kubelet's role

The kubelet writes each Pod's `resolv.conf` from two things:
`clusterDNS` and `clusterDomain` in `/var/lib/kubelet/config.yaml`
(`10.96.0.10`, `cluster.local`). A Pod's `dnsPolicy` decides whether it gets
that file:

| `dnsPolicy` | The Pod resolves through |
|---|---|
| `ClusterFirst` (default) | CoreDNS; external names are forwarded by CoreDNS to the node's resolvers |
| `ClusterFirstWithHostNet` | the same, for `hostNetwork: true` Pods (which would otherwise get `Default`) |
| `Default` | the **node's** `/etc/resolv.conf` - no cluster names |
| `None` | only what `dnsConfig` says |

A `hostNetwork` Pod that cannot resolve Services is usually a `dnsPolicy` left
at `ClusterFirst` - switch it to `ClusterFirstWithHostNet`.

:::exam-tip
"Find the DNS name of Service X in namespace Y" → `X.Y.svc.cluster.local`.
"Why can the web Pod not reach mysql" when they are in different namespaces
→ the app is configured with the short name; it needs `mysql.<namespace>`
(check `kubectl describe svc` and the app's env). Test with
`kubectl exec <pod> -- nslookup mysql.payroll`.
:::

## Quick checks

```bash
kubectl get svc kube-dns -n kube-system                    # 10.96.0.10, the nameserver in every resolv.conf
kubectl get pods -n kube-system -l k8s-app=kube-dns         # CoreDNS Pods
kubectl exec <pod> -- nslookup kubernetes                   # the API server's Service: the universal "does DNS work" test
kubectl exec <pod> -- cat /etc/resolv.conf                  # nameserver + search: is this Pod even pointed at CoreDNS?
```

## Check yourself

1. Write the full DNS name of Service `api` in namespace `prod`, and the
   shortest name that works from namespace `default`.
2. What writes a Pod's `/etc/resolv.conf`, and from which two kubelet
   settings?
3. A `hostNetwork: true` Pod cannot resolve any Service. Which field do you
   change?
