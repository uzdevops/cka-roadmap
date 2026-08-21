## kubectl o’zi noto’g’ri ishlaganda

Workload’ga emas, control plane’ga ishora qiluvchi simptomlar:

- `kubectl` osilib qoladi yoki `The connection to the server ... was refused`
  deydi - **API server**.
- yangi Pod’lar hech qanday Events’siz `Pending` bo’lib qoladi, hech narsa
  rejalashtirilmaydi - **scheduler**.
- Deployment’lar ReplicaSet yaratmaydi, ReplicaSet’lar Pod yaratmaydi,
  node’lar hech qachon NotReady deb belgilanmaydi, Service’lar Endpoint
  olmaydi - **controller manager**.
- hamma narsa sekin, yozish amallari ishlamaydi, `etcdserver: request timed out` - **etcd**.

## Birinchi qarash

```bash
kubectl get nodes
kubectl get pods -n kube-system                        # kubeadm klasterlarida control plane AYNAN shu Pod'lar
# NAME                             READY   STATUS             RESTARTS
# etcd-controlplane                1/1     Running
# kube-apiserver-controlplane      1/1     Running
# kube-controller-manager-...      1/1     Running
# kube-scheduler-controlplane      0/1     CrashLoopBackOff   5     <- mana shu
kubectl describe pod kube-scheduler-controlplane -n kube-system | tail -20
kubectl logs kube-scheduler-controlplane -n kube-system [--previous]
```

Komponentlar static Pod emas, **systemd service’lari** sifatida ishlaydigan
klasterda (kubeadm yagona yo’l emas):

```bash
systemctl status kube-apiserver kube-controller-manager kube-scheduler etcd
journalctl -u kube-apiserver -f
```

## Static Pod’lar va ularning manifestlari

kubeadm’ning control plane’i **static Pod’lar** sifatida ishlaydi:
control-plane node’dagi kubelet `/etc/kubernetes/manifests/*.yaml` fayllarini
o’qiydi va ularni to’g’ridan-to’g’ri ishga tushiradi. API server ular uchun
faqat **mirror** Pod’larni ko’radi.

```bash
ls /etc/kubernetes/manifests/
# etcd.yaml  kube-apiserver.yaml  kube-controller-manager.yaml  kube-scheduler.yaml
```

Buning oqibatlari:

- `kubectl delete pod kube-scheduler-controlplane -n kube-system` uzoq
  muddatli hech narsa qilmaydi - kubelet uni fayldan qayta yaratadi.
- **Faylni tahrirlash** - yechim aynan shu; kubelet buni sezadi va Pod’ni bir
  necha soniya ichida qayta ishga tushiradi. `kubectl apply` ham, qayta ishga
  tushirish buyrug’i ham kerak emas.
- Agar API server ishlamayotgan bo’lsa, `kubectl` foydasiz - konteyner
  runtime’idan to’g’ridan-to’g’ri foydalaning.

```bash
crictl ps -a | grep -E "apiserver|scheduler|controller|etcd"
crictl logs <container-id>
ls /var/log/pods/kube-system_kube-apiserver-*/kube-apiserver/        # xuddi o'sha loglar, fayl ko'rinishida
journalctl -u kubelet | grep -i apiserver                             # kubelet uni nega ishga tushira olmaganini tushuntiradi
```

## Odatiy buzilishlar

| Simptom | Qayerda | Odatda nima bo’ladi |
|---|---|---|
| scheduler / controller-manager `CrashLoopBackOff`, logda: `unknown flag` yoki `flag provided but not defined` | manifestdagi `command:` | xato yozilgan yoki yaroqsiz flag |
| control-plane Pod’i uchun `ErrImagePull` | manifestdagi `image:` | noto’g’ri tag (`kube-scheduler:v1.31.0-bad`) |
| controller-manager logi: `unable to load client CA file` / `no such file or directory` | manifestdagi `volumes:` hostPath yoki `--client-ca-file` | noto’g’ri yo’l - kubelet’niki yoki boshqa manifest bilan solishtiring |
| apiserver ishga tushmayapti, kubectl rad etilyapti | `/etc/kubernetes/manifests/kube-apiserver.yaml` | noto’g’ri `--etcd-servers`, sertifikat yo’li yoki xato yozilgan so’z; `crictl logs` buni ko’rsatadi |
| apiserver logi: 127.0.0.1:2379 ga `connection refused` | etcd | etcd ishlamayapti yoki uning manifesti buzilgan - avval shuni tekshiring |
| sertifikat muddati tugaguniga qadar hammasi joyida edi | `/etc/kubernetes/pki` | `kubeadm certs check-expiration`, `kubeadm certs renew all` |
| kube-scheduler Pod’i umuman ro’yxatda yo’q | manifest fayli | fayl yo’q yoki nomi noto’g’ri - `.yaml` emas, yoki katalogdan chiqarib yuborilgan |
| controller-manager logi: `--service-account-private-key-file` yoki `--cluster-signing-cert-file` xatosi | manifest | yo’l o’zgargan; fayllar `/etc/kubernetes/pki` ichida turadi |

## Manifestni xato izlab o’qish

```bash
cat /etc/kubernetes/manifests/kube-scheduler.yaml
```

```yaml
spec:
  containers:
  - command:
    - kube-scheduler
    - --authentication-kubeconfig=/etc/kubernetes/scheduler.conf
    - --authorization-kubeconfig=/etc/kubernetes/scheduler.conf
    - --bind-address=127.0.0.1
    - --kubeconfig=/etc/kubernetes/scheduler.conf
    - --leader-elect=true
    image: registry.k8s.io/kube-scheduler:v1.31.0
    livenessProbe: ...
    volumeMounts:
    - mountPath: /etc/kubernetes/scheduler.conf
      name: kubeconfig
      readOnly: true
  volumes:
  - hostPath:
      path: /etc/kubernetes/scheduler.conf
      type: FileOrCreate
    name: kubeconfig
```

Tartib bilan tekshiring: **image** tag’i mavjudmi; har bir **flag** to’g’ri
yozilganmi (`kube-scheduler --help` ularni ro’yxatlaydi); flag’lardagi va
**volumeMounts/hostPath** ichidagi har bir yo’l hostda mavjudmi (`ls` bilan
qarang). Keyin saqlang; `watch crictl ps` yoki
`kubectl get pods -n kube-system -w` bilan kuzating.

:::warning
Buzilgan `kube-apiserver.yaml` - nima noto’g’ri ekanini ko’rish uchun
`kubectl` ishlata olmaydigan yagona holat. `crictl ps -a` konteyner chiqib
ketayotganini ko’rsatadi; `crictl logs` (yoki `/var/log/pods`) nega ekanini
ko’rsatadi; `journalctl -u kubelet` kubelet uni yarata olmayotganini
ko’rsatadi. Faylni tuzating, `kubectl` o’zi qaytadi.
:::

## Bo’laklarning loglari

```bash
kubectl logs -n kube-system kube-apiserver-controlplane
kubectl logs -n kube-system kube-controller-manager-controlplane
kubectl logs -n kube-system kube-scheduler-controlplane
kubectl logs -n kube-system etcd-controlplane
journalctl -u kubelet -n 100 --no-pager                  # kubelet Pod emas; u Pod'larni ishga tushiradigan narsa
```

:::exam-tip
Imtihonning control plane savoli deyarli har doim `/etc/kubernetes/manifests`
ichidagi, bitta noto’g’ri narsasi bor manifest - flag, yo’l yoki image tag’i.
`kubectl get pods -n kube-system` buzilganini topadi; uning loglari yoki
`describe` Events’lari xatoni nomlaydi; manifestni `vi` bilan tahrirlang;
kuting. Static Pod’larga `kubectl delete` qilmang va kubelet’ning o’zi muammo
bo’lmasa, kubelet’ni qayta ishga tushirmang.
:::

## O’zingizni tekshiring

1. kubeadm klasterining control plane’i aslida qayerdan ishlaydi va bu uni
   qanday tuzatishingizga nima ta’sir qiladi?
2. API server ishlamayapti va `kubectl` ulana olmayapti. API server
   konteynerining loglarini qanday ko’rasiz?
3. Hech narsa rejalashtirilmayapti va yangi Pod’larda Events yo’q. Qaysi
   komponent va birinchi buyruq qaysi?
