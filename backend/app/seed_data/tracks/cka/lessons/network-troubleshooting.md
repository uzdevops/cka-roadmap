## Three places cluster networking breaks

Pods cannot reach each other, Services do not answer, names do not resolve.
Behind those three symptoms sit three components, and each has its own
check.

| Symptom | Component | Lives in |
|---|---|---|
| Pods stuck `ContainerCreating`, node NotReady with `NetworkPluginNotReady`, Pod-to-Pod traffic fails across nodes | **CNI plugin** | a DaemonSet in `kube-system` (+ `/etc/cni/net.d`, `/opt/cni/bin` on each node) |
| Pod IPs reachable but **Service ClusterIPs** are not | **kube-proxy** | DaemonSet `kube-proxy` in `kube-system` |
| IPs work, **names** do not (`nslookup` fails, apps say "no such host") | **CoreDNS** | Deployment `coredns` + Service `kube-dns` in `kube-system` |

## 1. The network plugin

```bash
kubectl get pods -n kube-system -o wide | grep -iE "weave|flannel|calico|cilium"
kubectl get ds -n kube-system
kubectl describe node node01 | grep -iA2 "NetworkUnavailable\|Ready"
ssh node01 'ls /etc/cni/net.d/; ls /opt/cni/bin/ | head'
journalctl -u kubelet | grep -i cni | tail
```

No CNI installed at all (a fresh kubeadm cluster) → every node NotReady,
CoreDNS Pods Pending. Install one:

```bash
kubectl apply -f https://github.com/weaveworks/weave/releases/download/v2.8.1/weave-daemonset-k8s.yaml
# or flannel / calico per their docs - the exam gives you the URL or has the manifest on disk
```

The plugin's DaemonSet Pod missing or crashing **on one node** → that
node's Pods cannot get IPs. Its logs (`kubectl logs -n kube-system
weave-net-xxxx -c weave`) usually say why: a Pod CIDR mismatch with
kubeadm's `--pod-network-cidr`, a missing kernel module, a port blocked
between nodes.

:::note
Weave, Flannel and Calico each ship their CNI binaries and config via the
DaemonSet; if `/etc/cni/net.d` is empty on a node, the DaemonSet Pod is not
running there - look at that, not at the directory.
:::

## 2. kube-proxy

```bash
kubectl get pods -n kube-system -l k8s-app=kube-proxy -o wide       # one per node, Running?
kubectl logs -n kube-system kube-proxy-xxxxx
kubectl describe ds kube-proxy -n kube-system | grep -A3 Command
kubectl get cm kube-proxy -n kube-system -o yaml | head -40
```

kube-proxy reads its config from the `kube-proxy` ConfigMap, mounted at
`/var/lib/kube-proxy/config.conf`. The usual breakage is a wrong **path**
in the DaemonSet's command (`--config=/var/lib/kube-proxy/configuration.conf`
when the file is `config.conf`) - the Pods CrashLoop and the log says
`open ...: no such file or directory`. Fix with `kubectl edit ds kube-proxy
-n kube-system`.

Symptom check: `curl <pod-ip>:<port>` works from another Pod, `curl
<cluster-ip>:<port>` does not → kube-proxy. On a node: `iptables -t nat -L
KUBE-SERVICES | grep <svc>` (iptables mode) or `ipvsadm -Ln` shows whether
the rules exist.

## 3. CoreDNS

```bash
kubectl get pods,svc,ep -n kube-system -l k8s-app=kube-dns
# pod/coredns-xxx   1/1 Running   (two replicas)
# service/kube-dns  ClusterIP 10.96.0.10   53/UDP,53/TCP,9153/TCP
# endpoints/kube-dns  10.244.0.2:53,10.244.0.3:53 ...       <- must be non-empty
kubectl logs -n kube-system -l k8s-app=kube-dns
kubectl get cm coredns -n kube-system -o yaml                 # the Corefile
```

```
.:53 {
    errors
    health { lameduck 5s }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa { pods insecure; fallthrough in-addr.arpa ip6.arpa; ttl 30 }
    prometheus :9153
    forward . /etc/resolv.conf { max_concurrent 1000 }
    cache 30
    loop
    reload
    loadbalance
}
```

| CoreDNS symptom | Cause | Fix |
|---|---|---|
| Pods `Pending` | no network plugin yet | install the CNI (section 1) |
| `CrashLoopBackOff`, log: `Loop ... detected` | the node's `/etc/resolv.conf` points at localhost (systemd-resolved stub); CoreDNS forwards to itself | point `forward` at a real upstream, or set kubelet `resolvConf: /run/systemd/resolve/resolv.conf` |
| Pods Running, `nslookup` times out from Pods | `kube-dns` Service has **no endpoints** or wrong port; kube-proxy broken; NetworkPolicy blocking 53 | `kubectl get ep kube-dns -n kube-system`; check `kube-dns` selector `k8s-app=kube-dns` and port 53; test the CoreDNS Pod IP directly |
| some names resolve, others not | Corefile `kubernetes` zone edited, or the name is in another namespace | use `svc.ns.svc.cluster.local`; check the ConfigMap |
| Pod `/etc/resolv.conf` has wrong nameserver | kubelet `clusterDNS` mis-set | `/var/lib/kubelet/config.yaml` → `clusterDNS: [10.96.0.10]` |

Test from inside a Pod:

```bash
kubectl run dnstest --rm -it --image=busybox:1.36 --restart=Never -- sh
# / # cat /etc/resolv.conf           nameserver 10.96.0.10  search default.svc.cluster.local svc.cluster.local cluster.local
# / # nslookup kubernetes.default
# / # nslookup web-service.shop.svc.cluster.local
# / # nslookup web-service.shop.svc.cluster.local 10.244.0.2      # ask a CoreDNS Pod directly - bypasses the Service/kube-proxy
```

If asking the Pod IP works and asking the Service IP does not, the problem
is kube-proxy or the `kube-dns` Service/Endpoints, not CoreDNS.

## The order

1. **Nodes Ready? CNI Pods Running on every node?** If not, nothing else
   matters yet.
2. **Pod-to-Pod by IP** across nodes: `kubectl exec a -- curl <pod-b-ip>`.
   Fails → CNI.
3. **Pod-to-Service by ClusterIP**. Fails → kube-proxy (or Endpoints
   empty - that is the app layer, last lesson).
4. **By name**. Fails → CoreDNS, or the Pod's `resolv.conf`, or a
   NetworkPolicy on UDP 53.

:::exam-tip
The network-troubleshooting exam question is usually one of: install the
CNI whose manifest is given (nodes NotReady), fix the kube-proxy DaemonSet's
config path (Services dead), or fix CoreDNS (Pods CrashLoop or the
`kube-dns` Service's selector/port is wrong). `kubectl get all -n
kube-system -o wide` shows which of the three is unhealthy in one screen.
:::

## Check yourself

1. Pod IPs reach each other but ClusterIPs do not. Which component, and
   what is the first check?
2. CoreDNS is in CrashLoopBackOff with "loop detected". What happened, and
   what is the fix?
3. How do you prove whether a DNS failure is CoreDNS itself or the path to
   it?
