## kubeadm klasteridagi har bir sertifikat

```bash
ls /etc/kubernetes/pki /etc/kubernetes/pki/etcd
```

```
/etc/kubernetes/pki
├── ca.crt  ca.key                          klaster CA'si
├── apiserver.crt  apiserver.key            API server'ning SERVER sertifikati
├── apiserver-kubelet-client.crt/.key       API server kubelet'larga CLIENT sifatida
├── apiserver-etcd-client.crt/.key          API server etcd'ga CLIENT sifatida
├── front-proxy-ca.crt/.key                 aggregation layer uchun CA
├── front-proxy-client.crt/.key             API server aggregatsiyalangan API'larga CLIENT (metrics-server)
├── sa.key  sa.pub                          ServiceAccount token'larini imzolaydi (sertifikat emas)
└── etcd/
    ├── ca.crt  ca.key                      etcd CA'si (ataylab alohida)
    ├── server.crt/.key                     etcd'ning SERVER sertifikati
    ├── peer.crt/.key                       etcd a'zolari orasida
    └── healthcheck-client.crt/.key         etcd'ning o'z probe'i
```

Ustiga fayl sifatida emas, **kubeconfig’lar ichida** yashaydigan client
sertifikatlari:

| kubeconfig | Shaxs (CN) | Guruh (O) | Kim ishlatadi |
|---|---|---|---|
| `/etc/kubernetes/admin.conf` | `kubernetes-admin` | `kubeadm:cluster-admins` | siz |
| `/etc/kubernetes/controller-manager.conf` | `system:kube-controller-manager` | - | controller manager |
| `/etc/kubernetes/scheduler.conf` | `system:kube-scheduler` | - | scheduler |
| `/etc/kubernetes/kubelet.conf` | `system:node:<name>` | `system:nodes` | shu node’ning kubelet’i |

Va har bir node’da kubelet’ning 10250-port uchun o’z **server** sertifikati
(`/var/lib/kubelet/pki/kubelet.crt`, yoki rotatsiya yoqilgan bo’lsa
`kubelet-server-current.pem`) turadi; API server loglar va exec uchun
kubelet’ga murojaat qilganda aynan uni tekshiradi.

## Server sertifikatlar, client sertifikatlar va kim nimani tekshiradi

```
kubectl  ──(client: admin.conf cert)──▶ apiserver (server: apiserver.crt; checks client against ca.crt)
apiserver ──(client: apiserver-etcd-client)──▶ etcd (server: etcd/server.crt; checks client against etcd/ca.crt)
apiserver ──(client: apiserver-kubelet-client)──▶ kubelet (server: kubelet.crt; checks client against ca.crt)
kubelet  ──(client: kubelet.conf cert)──▶ apiserver
scheduler/controller-manager ──(client: their .conf certs)──▶ apiserver
```

Ikkita CA: **klaster CA’si** Kubernetes tomonidagi hamma narsani imzolaydi;
**etcd CA’si** esa etcd tomonidagi hamma narsani. Shuning uchun API
serverning etcd client sertifikatini etcd CA’si imzolagan (`--etcd-cafile`
`etcd/ca.crt`’ga ishora qiladi) va shuning uchun etcd’ni joyidan ko’chiradigan
tiklash topshirig’i o’sha fayllarni birga saqlashi shart.

## Ularni nomlab beradigan flaglar

```yaml
# kube-apiserver.yaml
- --client-ca-file=/etc/kubernetes/pki/ca.crt                       # menga kim murojaat qila oladi
- --tls-cert-file=/etc/kubernetes/pki/apiserver.crt                 # men nimani ko'rsataman
- --tls-private-key-file=/etc/kubernetes/pki/apiserver.key
- --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt
- --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key
- --etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt
- --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt
- --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key
- --service-account-key-file=/etc/kubernetes/pki/sa.pub
- --service-account-signing-key-file=/etc/kubernetes/pki/sa.key
```

```yaml
# etcd.yaml
- --cert-file=/etc/kubernetes/pki/etcd/server.crt
- --key-file=/etc/kubernetes/pki/etcd/server.key
- --trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
- --peer-cert-file=/etc/kubernetes/pki/etcd/peer.crt
- --peer-key-file=/etc/kubernetes/pki/etcd/peer.key
- --peer-trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
```

:::exam-tip
Imtihonda "API server ko’tarilmayapti" deyilsa va siz `--etcd-cafile`
`.../etcd/ca.crt` o’rniga `/etc/kubernetes/pki/ca.crt` (klaster CA’si) ga
ishora qilayotganini topsangiz, xato aynan shu: API server o’zining etcd
client sertifikatini ko’rsatadi, etcd uni o’z CA’si bo’yicha tekshiradi - bu
joyi joyida - lekin API server etcd’ning server sertifikatini *noto’g’ri* CA
bo’yicha tekshiradi va rad etadi. Xulosa: har bir `*-cafile`’ni *narigi*
tomonni imzolagan CA’ga moslang.
:::

## Muddat tugashi va yangilash

kubeadm sertifikatlarning ko’pini **bir yilga** beradi (CA’larni o’n yilga).

```bash
kubeadm certs check-expiration
kubeadm certs renew all            # boshqaradigan hammasini yangilaydi; keyin control plane Pod'larini qayta ishga tushiring
```

`kubeadm upgrade apply` ham ularni yangilaydi, shuning uchun yiliga kamida
bir marta yangilanadigan klaster hech qachon jarlikka yetib bormaydi.
Yangilanmaydigani esa: bir kuni ertalab har bir komponent
`certificate has expired` deydi va kubectl ishlashdan to’xtaydi - yechim
yuqoridagi renew buyrug’i (node’ning root huquqi bilan bajariladi).

## O’zingizni tekshiring

1. API serverning etcd client sertifikatini qaysi CA imzolaydi va etcd’ning
   server sertifikati uchun qaysi CA’ga ishonishni API serverga qaysi flag
   aytadi?
2. Admin foydalanuvchining client sertifikati qayerda saqlanadi?
3. kubeadm boshqaradigan har bir sertifikatning muddatini qanday
   ro’yxatlaysiz va ularni nima yangilaydi?
