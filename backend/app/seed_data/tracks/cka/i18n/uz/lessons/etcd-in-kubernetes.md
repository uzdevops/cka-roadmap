## Kubeadm klasterida etcd qayerda joylashadi

kubeadm etcd’ni har bir control plane node’da **static Pod** sifatida ishga
tushiradi. Uning manifesti - `/etc/kubernetes/manifests/etcd.yaml`, kubelet uni
API server ishtirokisiz ishga tushiradi va uning ma’lumotlari node diskida
yotadi:

```bash
kubectl get pods -n kube-system | grep etcd
# etcd-controlplane   1/1   Running

cat /etc/kubernetes/manifests/etcd.yaml
```

Shu manifestdagi flaglar - siz doim qaytib keladiganlari:

```yaml
- command:
    - etcd
    - --advertise-client-urls=https://192.168.1.10:2379
    - --listen-client-urls=https://127.0.0.1:2379,https://192.168.1.10:2379
    - --listen-peer-urls=https://192.168.1.10:2380
    - --data-dir=/var/lib/etcd
    - --cert-file=/etc/kubernetes/pki/etcd/server.crt
    - --key-file=/etc/kubernetes/pki/etcd/server.key
    - --trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
    - --peer-cert-file=/etc/kubernetes/pki/etcd/peer.crt
    - --peer-key-file=/etc/kubernetes/pki/etcd/peer.key
    - --peer-trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
    - --initial-cluster=controlplane=https://192.168.1.10:2380
```

| Port | Kim u orqali gaplashadi |
|---|---|
| **2379** | klientlar - API server va `etcdctl` bilan siz |
| **2380** | peer’lar - bir-biri bilan gaplashadigan etcd a’zolari |

`/var/lib/etcd` ma’lumotlar katalogi esa `hostPath` volume, shuning uchun tiklash
"yangi katalogga tiklash, so’ng manifestni o’shanga yo’naltirish" ko’rinishida
bo’ladi.

## API server unga qanday yetib boradi

API server - etcd uchun *klient*. Uning o’z static Pod manifesti endpoint’larni
va u taqdim etadigan klient sertifikatini ko’rsatadi:

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
- --etcd-servers=https://127.0.0.1:2379
- --etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt
- --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt
- --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key
```

:::warning
Shu uchta `--etcd-*` flagdan birortasidagi noto’g’ri yo’l API serverni
crash-loop’ga tushiradi. Bunda kubectl o’lik bo’lgani uchun, siz uni control
plane node’da `crictl logs` bilan aniqlaysiz. Aynan shu nosozlik - eng sevimli
nosozlikni bartaraf etish topshiriqlaridan biri.
:::

## U bilan o’zingiz gaplashish

etcd faqat TLS klient ulanishlarini qabul qilgani uchun, kubeadm klasteridagi
har bir `etcdctl` buyrug’iga CA va klient sertifikati kerak. Node’dagi eng oson
yaroqli klient identifikatori - etcd serverning o’z cert/key jufti:

```bash
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health
```

Bu blokni qo’llaringiz yodlab olguncha ko’p tering - u imtihonda yozadigan backup
buyrug’ingizning boshlanishi. Uni qisqartirishning ikki yo’li:

```bash
# 1. etcd Pod ichiga exec qiling - sertifikatlar aynan shu yo'llarga ulangan
kubectl exec -n kube-system etcd-controlplane -- sh -c \
  "ETCDCTL_API=3 etcdctl --cacert=/etc/kubernetes/pki/etcd/ca.crt \
   --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key \
   endpoint health"

# 2. node'da ularni har bir shell uchun bir marta export qiling
export ETCDCTL_API=3 ETCDCTL_CACERT=/etc/kubernetes/pki/etcd/ca.crt \
       ETCDCTL_CERT=/etc/kubernetes/pki/etcd/server.crt ETCDCTL_KEY=/etc/kubernetes/pki/etcd/server.key
etcdctl --endpoints=https://127.0.0.1:2379 member list --write-out=table
```

:::exam-tip
Yo’llarni unutsangiz, ular qayerdan olinadi? `kubectl describe pod
etcd-controlplane -n kube-system` (yoki `cat /etc/kubernetes/manifests/etcd.yaml`)
har bir flagni ko’rsatadi. Sertifikat yo’lini hech qachon taxmin qilmang - uni
manifestdan o’qing.
:::

## Stacked va external etcd

kubeadm sukut bo’yicha etcd’ni control plane node’lar **ustiga** qo’yadi
("stacked"): sodda, boshqariladigan bitta node kam va control plane node’ni
yo’qotish u bilan birga etcd a’zosini ham yo’qotadi. **External** topologiya
etcd’ni o’z mashinalarida ishga tushiradi, shuning uchun control plane va
ma’lumotlar ombori bir-biridan mustaqil ishdan chiqadi. Ikkalasini ham HA
darsida uchratasiz; hozircha yuqoridagi static Pod sozlamasi stacked ekanini
bilib qo’ying.

## O’zingizni tekshiring

1. API server etcd’ga yetib borish uchun qaysi portdan foydalanadi, etcd a’zolari
   esa bir-biriga yetib borish uchun qaysi portdan?
2. Backup buyrug’i uchun etcd CA yo’li kerak, lekin uni eslay olmayapsiz.
   Node’da ishonchli javob qayerda?
3. Kimdir manifestini tahrirlagandan keyin API server crash-loop’da. Birinchi
   navbatda qaysi uchta flagni tekshirasiz va crash sababini qaysi vosita
   ko’rsatadi?
