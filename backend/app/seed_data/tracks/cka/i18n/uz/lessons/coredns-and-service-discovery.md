## CoreDNS klasterda qanday ishlaydi

```bash
kubectl get deployment coredns -n kube-system          # kubeadm'da 2 ta replika
kubectl get pods -n kube-system -l k8s-app=kube-dns -o wide
kubectl get svc kube-dns -n kube-system                # ClusterIP 10.96.0.10 - har bir resolv.conf dagi manzil
kubectl get configmap coredns -n kube-system -o yaml   # Corefile
```

Uchta obyekt: Deployment (DNS server Pod’lari, tarixiy sabablarga ko’ra
`k8s-app=kube-dns` label’i bilan), Service (`kube-dns`, kubelet Pod’larga
beradigan qat’iy ClusterIP) va ConfigMap (Corefile). Ustiga ServiceAccount va
ClusterRole - `kubernetes` plugin’i Service va EndpointSlice’larni kuzata
olishi uchun.

## Corefile, qatorma-qator

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

| Qator | Ta’siri |
|---|---|
| `kubernetes cluster.local ...` | `*.cluster.local`’ga (va teskari so’rovlarga) API’dan javob beradi: Service’lar → ClusterIP, headless → Pod IP’lari |
| `pods insecure` | `<dashed-ip>.<ns>.pod.cluster.local` nomlariga ruxsat beradi |
| `forward . /etc/resolv.conf` | qolgan hamma narsa **CoreDNS Pod’ining** resolv.conf faylidagi resolver’larga ketadi - Deployment’da `dnsPolicy: Default` bo’lgani uchun bu **node’ning** resolv.conf fayli |
| `cache 30` | 30 s keshlaydi - Service o’zgarishi nega 30 s gacha kechikib ko’rinadi, sababi shu |
| `loop` | agar forward nishoni CoreDNS’ning o’zi bo’lsa, buni logga yozadi va chiqadi - sababini nomi bilan aytadigan crash loop |
| `reload` | Corefile’ni kuzatadi va o’zgarganda qayta yuklaydi - ConfigMap’ni tahrirlang, ~2 daqiqa kuting |
| `health`, `ready` | :8080 da liveness, :8181 da readiness |

Bu yerdagi `cluster.local` kubelet’ning `clusterDomain` qiymatiga mos kelishi
kerak. kubeadm klasterida ular mos; birini ikkinchisisiz o’zgartirsangiz, hech
narsa aniqlanmaydi.

## Service qanday qilib yozuvga aylanadi

`kubernetes` plugin’i Service va EndpointSlice’larni **kuzatadi** - poll
qilmaydi. Service yarating va yozuv bir soniya ichida paydo bo’ladi; qayta
ishga tushirish ham, reload ham kerak emas. CoreDNS’ga RBAC (services,
endpointslices, namespaces ustida list/watch) shuning uchun kerak va ishlab
turgan, lekin ServiceAccount token’ini yo’qotgan CoreDNS klasterdagi hamma
narsaga NXDOMAIN qaytarishi ham shundan.

```bash
kubectl logs -n kube-system -l k8s-app=kube-dns
# [ERROR] ... failed to list *v1.Service: ... forbidden        <- RBAC/token muammosi
# [FATAL] plugin/loop: Loop ... detected                        <- forward tsikli
# [INFO] 10.244.1.5:43892 - 12345 "A IN web.payroll.svc.cluster.local. udp 45 false 512" NOERROR ...   (`log` yoqilgan bo'lsa)
```

## Nosozlik holatlari va ularning yechimi

| Alomat | Sababi | Yechimi |
|---|---|---|
| hech narsa aniqlanmaydi, CoreDNS Pod’lari Pending/CrashLoopBackOff | CNI yo’q / loop aniqlangan / noto’g’ri Corefile | CNI’ni tuzating; node’ning resolv.conf faylini tuzating (Ubuntu’dagi `127.0.0.53` → `/run/systemd/resolve/resolv.conf`’dan foydalaning); ConfigMap’ni tuzating |
| klaster nomlari ishlamaydi, tashqi nomlar ishlaydi | `kubernetes` plugin’i xato beradi | `kubectl logs` - RBAC yoki `clusterDomain` mos emas |
| tashqi nomlar ishlamaydi, klaster nomlari ishlaydi | `forward` nishoniga yetib bo’lmaydi | node’larning resolver’lari, `kube-system`’dan 53-portga egress uchun NetworkPolicy, firewall |
| bitta Pod aniqlay olmaydi | uning `resolv.conf` fayli / `dnsPolicy` | `kubectl exec <pod> -- cat /etc/resolv.conf` |
| Service noto’g’ri IP’ga aylanadi / eskirgan | kesh | 30 s kuting; sabringiz chidamasa `kubectl rollout restart deployment coredns -n kube-system` |

:::exam-tip
Universal test, tartib bilan: (1) `kubectl get pods -n kube-system -l
k8s-app=kube-dns` - Running’mi? (2) `kubectl exec <pod> -- nslookup kubernetes` -
klasterning o’z API Service’i; bu ishlamasa DNS o’lgan, ishlasa DNS joyida va
muammo so’ralayotgan *nom*da (namespace, xato yozilgan harf). (3) Xato
qatorini topish uchun CoreDNS’ning `kubectl logs` chiqishi.
:::

## Corefile’ni tahrirlash

```bash
kubectl edit configmap coredns -n kube-system
# masalan, server bloki qo'shish:
#   corp.internal:53 { forward . 10.10.0.53 }
# yoki forward . /etc/resolv.conf ni forward . 8.8.8.8 ga o'zgartirish
kubectl rollout restart deployment coredns -n kube-system     # faqat `reload`'ni kuta olmasangiz
```

`forward`’ni ommaviy resolver’ga o’zgartirish - o’z resolv.conf fayli systemd
stub’i bo’lgan lab node’i uchun tezkor yechim; productionda esa node’ning
o’zini tuzatasiz.

## O’zingizni tekshiring

1. CoreDNS qaysi uchta Kubernetes obyektidan iborat va har bir Pod’ning
   `resolv.conf` fayli ularning qaysi biriga ko’rsatadi?
2. Yangi Service hech qanday qayta ishga tushirishsiz bir soniya ichida
   aniqlanadi. Nega?
3. Klaster nomlari aniqlanadi; `google.com` esa yo’q. Corefile’ning qaysi
   qatori va uning ortida nima turadi?
