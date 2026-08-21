## Yagona eshik

Kubernetes klasteri bilan har qanday muloqot API server orqali o’tadi -
`kubectl`, scheduler, controller manager, har bir node’dagi har bir kubelet,
dashboard, CI pipeline’ingiz. Boshqa hech narsa etcd bilan gaplashmaydi. Aynan
shu bitta fakt uning dizaynining ko’p qismini tushuntiradi: bu - so’rovlar
autentifikatsiya, avtorizatsiya, admission va validatsiyadan o’tib, nihoyat
yoziladigan joy.

```
kubectl ──▶ kube-apiserver ──▶ etcd
               ▲   ▲   ▲
    scheduler ─┘   │   └─ controller-manager
                kubelets
```

So’rov quvuri, bajarilish tartibida:

1. **Autentifikatsiya** - siz kimsiz? Sertifikatlar, bearer token’lar, service
   account token’lari, OIDC.
2. **Avtorizatsiya** - buni qilishingiz mumkinmi? RBAC, Node, Webhook, ABAC.
3. **Admission** - bu obyektga ruxsat berilsinmi yoki u o’zgartirilsinmi?
   Mutating webhook’lar, keyin validating webhook’lar va o’rnatilgan pluginlar.
4. **Sxema validatsiyasi** - obyekt to’g’ri shakllanganmi?
5. **Saqlash** - etcd’ga yozish va yangi resourceVersion’ni qaytarish.

Bu bosqichlarning har biri - trekning keyingi qismidagi alohida dars; bu dars
esa ularni o’zida saqlaydigan komponent haqida.

## U qanday ishlaydi

kubeadm klasterida API server har bir control plane node’dagi **static Pod**,
shuning uchun u ConfigMap bilan emas, fayldagi flaglar bilan sozlanadi:

```bash
cat /etc/kubernetes/manifests/kube-apiserver.yaml
kubectl get pods -n kube-system | grep apiserver
ps -ef | grep kube-apiserver | tr ' ' '\n' | grep -- --    # har bir flag alohida satrda
```

"Hard way" bilan o’rnatilgan klasterda u o’rniga systemd xizmati bo’ladi va
o’sha flaglar `/etc/systemd/system/kube-apiserver.service` ichida yashaydi. Bir
xil komponent, boshqa supervizor.

## Siz haqiqatan tegadigan flaglar

```yaml
- kube-apiserver
- --advertise-address=192.168.1.10
- --secure-port=6443
- --etcd-servers=https://127.0.0.1:2379
- --etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt
- --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt
- --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key
- --client-ca-file=/etc/kubernetes/pki/ca.crt
- --tls-cert-file=/etc/kubernetes/pki/apiserver.crt
- --tls-private-key-file=/etc/kubernetes/pki/apiserver.key
- --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt
- --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key
- --service-cluster-ip-range=10.96.0.0/12
- --authorization-mode=Node,RBAC
- --enable-admission-plugins=NodeRestriction
- --encryption-provider-config=/etc/kubernetes/enc/enc.yaml   # faqat uni qo'shganingizdan keyin
```

| Flaglar guruhi | Qaysi darsda ishlatiladi |
|---|---|
| `--etcd-*` | Kubernetesda etcd, backup va tiklash |
| `--client-ca-file`, `--tls-*` | TLS va sertifikatlar |
| `--kubelet-client-*` | `kubectl logs` va `exec` ishlashini ta’minlaydigan narsa |
| `--service-cluster-ip-range` | Service tarmog’i |
| `--authorization-mode` | avtorizatsiya |
| `--enable-admission-plugins` | admission kontrollerlar |
| `--encryption-provider-config` | Secret’larni diskda shifrlash |

:::exam-tip
Static Pod manifestini tahrirlaganingizda, kubelet fayl o’zgarganini sezadi va
Pod’ni qayta yaratadi. Hech qanday `systemctl restart` yo’q. Unga 20-30 soniya
bering; agar `kubectl` qaytib kelmasa, siz xato yozgansiz - node’dagi
`crictl ps -a` va `crictl logs` qaysi birini xato qilganingizni ko’rsatadi.
:::

## Nima buziladi va u qanday ko’rinadi

| Alomat | Ehtimoliy sabab |
|---|---|
| `The connection to the server ... was refused` | API server ishlamayapti: manifestdagi xato yoki control plane’da kubelet o’chgan |
| `Unable to connect to the server: x509: certificate ...` | kubeconfig’ingizdagi CA yoki klient sertifikati mos kelmaydi |
| API server crash-loop’da, loglarda etcd tilga olinadi | noto’g’ri `--etcd-*` yo’li yoki etcd o’zi o’chgan |
| `kubectl logs` / `exec` 401 yoki timeout bilan ishlamaydi, lekin `get` ishlaydi | `--kubelet-client-*` sertifikatlari yoki kubelet porti bloklangan |

```bash
# control plane node'dagi tekshirish ketma-ketligi
systemctl status kubelet
crictl ps -a | grep kube-apiserver
crictl logs <container-id> 2>&1 | tail -30
cat /etc/kubernetes/manifests/kube-apiserver.yaml   # xatoni qidiring
```

:::tip
`kubectl get --raw /healthz`, `/livez` va `/readyz` - API serverdan o’zini
qanday his qilayotganini so’rashning arzon yo’llari - `/readyz?verbose` u
bajaradigan har bir tekshiruvni sanab beradi.
:::

## O’zingizni tekshiring

1. Autentifikatsiya, admission va avtorizatsiya qanday tartibda bajariladi va
   nega bu tartib muhim?
2. `kube-apiserver.yaml` dagi flagni o’zgartirdingiz. API serverni nima qayta
   ishga tushiradi?
3. `kubectl get pods` ishlaydi, lekin `kubectl logs` xato qaytaradi. Qaysi API
   server flaglari ishtirok etadi va narigi uchida qaysi komponent turadi?
