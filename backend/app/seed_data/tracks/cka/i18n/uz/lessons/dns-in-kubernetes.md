## Har bir Service’ning nomi bor

Service yaratilganda CoreDNS - klasterning DNS’i, o’zi ham API’ni kuzatib
turadigan Deployment - unga yozuv e’lon qiladi:

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

| Qaysi Pod’dan... | Nimani ishlatasiz |
|---|---|
| xuddi shu namespace’dan (`payroll`) | `web-service` |
| boshqa namespace’dan | `web-service.payroll` |
| istalgan joydan, bir ma’noli | `web-service.payroll.svc` yoki to’liq `web-service.payroll.svc.cluster.local` |

Qisqa shakllar ishlaydi, chunki kubelet har bir Pod’ning
`/etc/resolv.conf` fayliga **search ro’yxatini** yozadi:

```bash
kubectl exec t -- cat /etc/resolv.conf
# nameserver 10.96.0.10                                     <- kube-dns Service'i (CoreDNS)
# search default.svc.cluster.local svc.cluster.local cluster.local
# options ndots:5
```

`default` namespace’idan berilgan `nslookup web-service` avval
`web-service.default.svc.cluster.local` ni (NXDOMAIN), keyin
`web-service.svc.cluster.local` ni (NXDOMAIN), keyin
`web-service.cluster.local` ni, oxirida esa yalang’och nomni sinaydi.
`web-service.payroll` ikkinchi suffiksda topiladi:
`web-service.payroll.svc.cluster.local`. Shuning uchun "boshqa namespace’dagi
Service" uchun namespace kerak bo’ladi, xolos.

## Pod’larning ham nomi bor, bir qadar

```
<dashed-ip>.<namespace>.pod.cluster.local   ->  10-244-1-5.default.pod.cluster.local -> 10.244.1.5
```

Faqat CoreDNS’ning `kubernetes` plugin’ida `pods insecure` bo’lsa (kubeadm’da
sukut bo’yicha shunday), va buni hech kim ishlatmaydi - Pod’ning IP’si
barqaror emas. *Foydali* narsa boshqa: **headless Service** va StatefulSet
yaratadigan, har bir Pod uchun alohida nomlar -
`db-0.db.payroll.svc.cluster.local` - buni storage bosqichi ko’rib chiqqan.

## Yozuv turlari

```bash
nslookup web-service.payroll.svc.cluster.local              # A: ClusterIP
nslookup -type=srv _http._tcp.web-service.payroll.svc.cluster.local   # SRV: port raqami, nomlangan portlar uchun
nslookup db.payroll.svc.cluster.local                        # headless: har bir Pod uchun bittadan bir nechta A yozuvi
```

## Kubelet’ning roli

Kubelet har bir Pod’ning `resolv.conf` faylini ikkita narsadan yozadi:
`/var/lib/kubelet/config.yaml` ichidagi `clusterDNS` va `clusterDomain`
(`10.96.0.10`, `cluster.local`). Pod shu faylni oladimi-yo’qmi, buni uning
`dnsPolicy` maydoni hal qiladi:

| `dnsPolicy` | Pod nima orqali aniqlaydi |
|---|---|
| `ClusterFirst` (sukut bo’yicha) | CoreDNS; tashqi nomlarni CoreDNS node’ning resolver’lariga uzatadi |
| `ClusterFirstWithHostNet` | xuddi shu, `hostNetwork: true` Pod’lar uchun (aks holda ular `Default` olardi) |
| `Default` | **node’ning** `/etc/resolv.conf` fayli - klaster nomlari yo’q |
| `None` | faqat `dnsConfig` aytgani |

Service’larni aniqlay olmaydigan `hostNetwork` Pod’ida odatda `dnsPolicy`
`ClusterFirst` holida qolib ketgan bo’ladi - uni `ClusterFirstWithHostNet` ga
o’zgartiring.

:::exam-tip
"Y namespace’idagi X Service’ining DNS nomini toping" → `X.Y.svc.cluster.local`.
Ular turli namespace’larda bo’lganda "nega web Pod’i mysql’ga yeta olmaydi"
→ ilova qisqa nom bilan sozlangan; unga `mysql.<namespace>` kerak
(`kubectl describe svc` va ilovaning env’ini tekshiring). Sinash uchun:
`kubectl exec <pod> -- nslookup mysql.payroll`.
:::

## Tezkor tekshiruvlar

```bash
kubectl get svc kube-dns -n kube-system                    # 10.96.0.10, har bir resolv.conf dagi nameserver
kubectl get pods -n kube-system -l k8s-app=kube-dns         # CoreDNS Pod'lari
kubectl exec <pod> -- nslookup kubernetes                   # API server'ning Service'i: universal "DNS ishlayaptimi" testi
kubectl exec <pod> -- cat /etc/resolv.conf                  # nameserver + search: bu Pod umuman CoreDNS'ga qaratilganmi?
```

## O’zingizni tekshiring

1. `prod` namespace’idagi `api` Service’ining to’liq DNS nomini va `default`
   namespace’idan ishlaydigan eng qisqa nomni yozing.
2. Pod’ning `/etc/resolv.conf` faylini nima yozadi va kubelet’ning qaysi
   ikkita sozlamasidan?
3. `hostNetwork: true` Pod’i hech qanday Service’ni aniqlay olmayapti. Qaysi
   maydonni o’zgartirasiz?
