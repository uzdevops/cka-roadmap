## Klaster tarmog’i buziladigan uchta joy

Pod’lar bir-biriga yeta olmaydi, Service’lar javob bermaydi, nomlar
aniqlanmaydi. Bu uchta alomat ortida uchta komponent turadi va har birining
o’z tekshiruvi bor.

| Alomat | Komponent | Qayerda turadi |
|---|---|---|
| Pod’lar `ContainerCreating` holatida qotgan, node `NetworkPluginNotReady` bilan NotReady, node’lar orasidagi Pod-Pod trafigi ishlamaydi | **CNI plugin** | `kube-system`’dagi DaemonSet (+ har bir node’da `/etc/cni/net.d`, `/opt/cni/bin`) |
| Pod IP’lariga yetib boriladi, lekin **Service ClusterIP**’lariga yo’q | **kube-proxy** | `kube-system`’dagi `kube-proxy` DaemonSet’i |
| IP’lar ishlaydi, **nomlar** yo’q (`nslookup` ishlamaydi, ilovalar "no such host" deydi) | **CoreDNS** | `kube-system`’dagi `coredns` Deployment’i + `kube-dns` Service’i |

## 1. Tarmoq plugin’i

```bash
kubectl get pods -n kube-system -o wide | grep -iE "weave|flannel|calico|cilium"
kubectl get ds -n kube-system
kubectl describe node node01 | grep -iA2 "NetworkUnavailable\|Ready"
ssh node01 'ls /etc/cni/net.d/; ls /opt/cni/bin/ | head'
journalctl -u kubelet | grep -i cni | tail
```

Umuman CNI o’rnatilmagan bo’lsa (yangi kubeadm klasteri) → har bir node
NotReady, CoreDNS Pod’lari Pending. Bittasini o’rnating:

```bash
kubectl apply -f https://github.com/weaveworks/weave/releases/download/v2.8.1/weave-daemonset-k8s.yaml
# yoki flannel / calico - hujjatlariga qarab; imtihon sizga URL beradi yoki manifest diskda turadi
```

Plugin’ning DaemonSet Pod’i **bitta node’da** yo’q yoki qulab tursa → o’sha
node’ning Pod’lari IP ola olmaydi. Uning loglari (`kubectl logs -n kube-system
weave-net-xxxx -c weave`) odatda sababini aytadi: Pod CIDR kubeadm’ning
`--pod-network-cidr` qiymatiga mos kelmasligi, yadro moduli yetishmasligi,
node’lar orasida to’silgan port.

:::note
Weave, Flannel va Calico - har biri o’z CNI binarlari va konfigini DaemonSet
orqali keltiradi; agar node’da `/etc/cni/net.d` bo’sh bo’lsa, demak o’sha
node’da DaemonSet Pod’i ishlamayapti - katalogga emas, o’shanga qarang.
:::

## 2. kube-proxy

```bash
kubectl get pods -n kube-system -l k8s-app=kube-proxy -o wide       # har bir node'da bitta, Running'mi?
kubectl logs -n kube-system kube-proxy-xxxxx
kubectl describe ds kube-proxy -n kube-system | grep -A3 Command
kubectl get cm kube-proxy -n kube-system -o yaml | head -40
```

kube-proxy o’z konfigini `kube-proxy` ConfigMap’idan o’qiydi, u
`/var/lib/kube-proxy/config.conf`’ga mount qilingan. Odatdagi nosozlik -
DaemonSet buyrug’idagi noto’g’ri **yo’l**
(`--config=/var/lib/kube-proxy/configuration.conf`, fayl esa `config.conf`) -
Pod’lar CrashLoop qiladi va log `open ...: no such file or directory` deydi.
`kubectl edit ds kube-proxy -n kube-system` bilan tuzating.

Alomat tekshiruvi: boshqa Pod’dan `curl <pod-ip>:<port>` ishlaydi, `curl
<cluster-ip>:<port>` esa yo’q → kube-proxy. Node’da: `iptables -t nat -L
KUBE-SERVICES | grep <svc>` (iptables rejimi) yoki `ipvsadm -Ln` qoidalar
bor-yo’qligini ko’rsatadi.

## 3. CoreDNS

```bash
kubectl get pods,svc,ep -n kube-system -l k8s-app=kube-dns
# pod/coredns-xxx   1/1 Running   (ikkita replika)
# service/kube-dns  ClusterIP 10.96.0.10   53/UDP,53/TCP,9153/TCP
# endpoints/kube-dns  10.244.0.2:53,10.244.0.3:53 ...       <- bo'sh bo'lmasligi shart
kubectl logs -n kube-system -l k8s-app=kube-dns
kubectl get cm coredns -n kube-system -o yaml                 # Corefile
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

| CoreDNS alomati | Sababi | Yechimi |
|---|---|---|
| Pod’lar `Pending` | hali tarmoq plugin’i yo’q | CNI’ni o’rnating (1-bo’lim) |
| `CrashLoopBackOff`, logda: `Loop ... detected` | node’ning `/etc/resolv.conf` fayli localhost’ga ko’rsatadi (systemd-resolved stub); CoreDNS o’zini o’ziga uzatadi | `forward`’ni haqiqiy upstream’ga qarating yoki kubelet’da `resolvConf: /run/systemd/resolve/resolv.conf`’ni belgilang |
| Pod’lar Running, lekin Pod’dan `nslookup` kutish vaqti bilan tugaydi | `kube-dns` Service’ida **endpoint yo’q** yoki port noto’g’ri; kube-proxy buzuq; NetworkPolicy 53 ni to’sib turibdi | `kubectl get ep kube-dns -n kube-system`; `kube-dns` selector’i `k8s-app=kube-dns` va 53-portni tekshiring; CoreDNS Pod IP’sini to’g’ridan-to’g’ri sinang |
| ba’zi nomlar aniqlanadi, ba’zilari yo’q | Corefile’dagi `kubernetes` zonasi tahrirlangan yoki nom boshqa namespace’da | `svc.ns.svc.cluster.local` ishlating; ConfigMap’ni tekshiring |
| Pod’ning `/etc/resolv.conf` faylida noto’g’ri nameserver | kubelet’ning `clusterDNS` qiymati xato qo’yilgan | `/var/lib/kubelet/config.yaml` → `clusterDNS: [10.96.0.10]` |

Pod ichidan sinang:

```bash
kubectl run dnstest --rm -it --image=busybox:1.36 --restart=Never -- sh
# / # cat /etc/resolv.conf           nameserver 10.96.0.10  search default.svc.cluster.local svc.cluster.local cluster.local
# / # nslookup kubernetes.default
# / # nslookup web-service.shop.svc.cluster.local
# / # nslookup web-service.shop.svc.cluster.local 10.244.0.2      # to'g'ridan-to'g'ri CoreDNS Pod'idan so'rash - Service/kube-proxy'ni chetlab o'tadi
```

Agar Pod IP’sidan so’rash ishlasa-yu, Service IP’sidan so’rash ishlamasa,
muammo CoreDNS’da emas, kube-proxy yoki `kube-dns` Service/Endpoints’da.

## Tartib

1. **Node’lar Ready’mi? CNI Pod’lari har bir node’da Running’mi?** Agar yo’q
   bo’lsa, qolgan hamma narsa hali ahamiyatsiz.
2. Node’lar orasida **IP bo’yicha Pod-Pod**: `kubectl exec a -- curl
   <pod-b-ip>`. Ishlamasa → CNI.
3. **ClusterIP bo’yicha Pod-Service**. Ishlamasa → kube-proxy (yoki
   Endpoints bo’sh - bu ilova qatlami, o’tgan dars).
4. **Nom bo’yicha**. Ishlamasa → CoreDNS yoki Pod’ning `resolv.conf` fayli
   yoki UDP 53 ga qo’yilgan NetworkPolicy.

:::exam-tip
Tarmoq nosozligi bo’yicha imtihon savoli odatda shulardan biri: manifesti
berilgan CNI’ni o’rnatish (node’lar NotReady), kube-proxy DaemonSet’ining
config yo’lini tuzatish (Service’lar o’lik) yoki CoreDNS’ni tuzatish
(Pod’lar CrashLoop yoki `kube-dns` Service’ining selector/porti noto’g’ri).
`kubectl get all -n kube-system -o wide` uchtasidan qaysi biri nosozligini
bitta ekranda ko’rsatadi.
:::

## O’zingizni tekshiring

1. Pod IP’lari bir-biriga yetadi, ClusterIP’larga esa yo’q. Qaysi komponent
   va birinchi tekshiruv nima?
2. CoreDNS "loop detected" bilan CrashLoopBackOff’da. Nima sodir bo’lgan va
   yechimi nima?
3. DNS nosozligi CoreDNS’ning o’zidami yoki unga boradigan yo’ldami - buni
   qanday isbotlaysiz?
