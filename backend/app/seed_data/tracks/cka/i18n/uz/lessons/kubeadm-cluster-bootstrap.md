## Ikki node’li klasterni ko’tarish

`controlplane` (192.168.56.11) va `node01` (192.168.56.21) node’lari, ikkalasi
ham oldingi darsdagidek tayyorlangan. Bu yerdagi har bir buyruqni siz
o’rnatish labida ham, imtihonda ham yozasiz.

### 1. Control plane’da: init

```bash
kubeadm init \
  --pod-network-cidr=10.244.0.0/16 \
  --apiserver-advertise-address=192.168.56.11
```

Uning phase’lardan o’tishini kuzating. U nusxa olish kerak bo’lgan uchta narsa
bilan tugaydi:

```
Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:
  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

You should now deploy a pod network to the cluster. ...

Then you can join any number of worker nodes by running the following on each as root:
kubeadm join 192.168.56.11:6443 --token x1y2z3.abcdefghij123456 \
        --discovery-token-ca-cert-hash sha256:9f2d...
```

Birinchi blokni darhol bajaring; join buyrug’ini biror joyga saqlab qo’ying.

```bash
mkdir -p $HOME/.kube && sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config && sudo chown $(id -u):$(id -g) $HOME/.kube/config
kubectl get nodes
# controlplane   NotReady   control-plane   40s   v1.30.2      <- NotReady kutilgan: hali CNI yo'q
kubectl get pods -n kube-system
# coredns-...    Pending                                        <- bu ham kutilgan
# etcd-controlplane, kube-apiserver-controlplane, ... Running
```

### 2. CNI

```bash
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
# (uning sukut bo'yicha Network'i 10.244.0.0/16 - --pod-network-cidr ga mos; sizniki boshqacha bo'lsa, ConfigMap'ni tahrirlang)
kubectl get pods -n kube-flannel -w
kubectl get nodes
# controlplane   Ready   control-plane   3m   v1.30.2
kubectl get pods -n kube-system | grep coredns       # endi Running
```

### 3. Worker’da: join

```bash
kubeadm join 192.168.56.11:6443 --token x1y2z3.abcdefghij123456 \
  --discovery-token-ca-cert-hash sha256:9f2d...
# [preflight] Running pre-flight checks
# ...
# This node has joined the cluster
```

Buyruqni yo’qotdingizmi? Control plane’da:

```bash
kubeadm token create --print-join-command
```

### 4. Tekshirish

```bash
kubectl get nodes -o wide
# controlplane   Ready   control-plane   5m   v1.30.2   192.168.56.11
# node01         Ready   <none>          1m   v1.30.2   192.168.56.21
kubectl get pods -A -o wide            # ikkala node'da ham flannel va kube-proxy, CoreDNS Running
kubectl run test --image=nginx
kubectl get pod test -o wide           # node01 ga joylashtirilgan, 10.244.x.x IP'si bor
kubectl exec test -- curl -s kubernetes.default.svc   # DNS + Service + API: 403 JSON javobi tarmoq boshdan oxirigacha ishlayotganini bildiradi
```

Control plane taint qilingan, shuning uchun `test` node01 ga ketdi. Bitta
node’li labda u yerga joylashtirish uchun taint’ni olib tashlang:

```bash
kubectl taint nodes controlplane node-role.kubernetes.io/control-plane:NoSchedule-
```

### 5. Nimadir noto’g’ri ketganda

| Belgi | Yechim |
|---|---|
| `init` preflight’dan o’tmaydi | `[ERROR ...]` satrini o’qing: swap, CPU soni, band portlar (oldingi urinish - `kubeadm reset -f`), runtime o’chgan |
| `init` "waiting for the kubelet to boot up the control plane" da osilib qoladi | o’sha node’da `journalctl -u kubelet -f`: containerd bilan cgroup drayveri mos emas yoki kubelet image’larni torta olmayapti (internet yo’q / noto’g’ri `sandbox_image`) |
| CNI’dan keyin ham node’lar NotReady | `kubectl get pods -n kube-flannel -o wide` - o’sha node’dagi DaemonSet Pod’i; loglarida CIDR mos kelmasligi |
| `join` ishlamaydi: token yaroqsiz | muddati tugagan (24 soat) - `kubeadm token create --print-join-command` |
| `join` ishlamaydi: `/etc/kubernetes/kubelet.conf already exists` | oldingi urinishdan qolgan eski holat - worker’da `kubeadm reset -f`, so’ng join |
| control plane’da `kubectl`: `connection refused localhost:8080` | `admin.conf` nusxasini olishni o’tkazib yubordingiz |
| `kubectl get nodes -o wide` NAT IP 10.0.2.15 ni ko’rsatadi | `/etc/default/kubelet`’da `KUBELET_EXTRA_ARGS=--node-ip=<private ip>`’ni belgilang, kubelet’ni qayta ishga tushiring |

:::exam-tip
O’rnatish vazifasi `kubectl get nodes` har bir node’ni so’ralgan versiyada
Ready ko’rsatishi va odatda worker’da ishlayotgan Pod bo’yicha baholanadi.
To’rtta qadamni tartib bilan bajaring, kubectl’ga tegishdan oldin
`admin.conf` nusxasini oling, CNI CIDR’ini mos qiling va join buyrug’ini
saqlab qo’ying. Agar imtihon sizga `kubeadm` konfiguratsiya faylini yoki
aniq versiyani bersa, `kubeadm init --config` / `--kubernetes-version`
- topshiriqni ikki marta o’qing.
:::

## O’zingizni tekshiring

1. Nega muvaffaqiyatli init’dan keyin ham control plane node NotReady bo’ladi
   va uni nima Ready qiladi?
2. join buyrug’ini yo’qotdingiz. Yangisini qanday olasiz?
3. `init` "waiting for the kubelet" da bir necha daqiqa turib qoldi. Nimaga
   qaraysiz?
