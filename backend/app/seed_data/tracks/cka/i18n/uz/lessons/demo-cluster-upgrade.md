## To’liq minor yangilash, buyruqma-buyruq

Ikkita node - `controlplane` va `node01` - 1.29.4 da turibdi va apt bilan
1.30.2 ga o’tadi. O’z klasteringizda birga bajaring; har bir qator - imtihonda
xuddi shu tartibda yozadiganingiz.

### 0. Hech narsaga tegishdan oldin

```bash
kubectl get nodes
# controlplane   Ready   control-plane   v1.29.4
# node01         Ready   <none>          v1.29.4
kubectl get pods -n kube-system           # hammasi Running holatdami?
```

### 1. Paket repozitoriysini yangi minor’ga yo’naltiring

**Ikkala** node’da ham:

```bash
# Debian/Ubuntu
sed -i 's#/v1.29/#/v1.30/#' /etc/apt/sources.list.d/kubernetes.list
apt-get update
apt-cache madison kubeadm | head -3       # 1.30.2-1.1 chiqishi kerak
```

(RHEL oilasidagi tizimlarda bu `/etc/yum.repos.d/kubernetes.repo` ichidagi
`baseurl`.)

### 2. Control plane: avval kubeadm

```bash
apt-mark unhold kubeadm
apt-get install -y kubeadm=1.30.2-1.1
apt-mark hold kubeadm
kubeadm version                           # v1.30.2
kubeadm upgrade plan                      # o'qing - maqsad v1.30.2, kubelet'lar qo'lda deb ko'rsatilgan
```

### 3. Control plane: drain va apply

```bash
kubectl drain controlplane --ignore-daemonsets
kubeadm upgrade apply v1.30.2
# ... [upgrade/successful] SUCCESS! Your cluster was upgraded to "v1.30.2". Enjoy!
# ... [upgrade/kubelet] Now that your control plane is upgraded, please proceed with upgrading your kubelets
```

`apply` paytida API server qayta ishga tushadi; `kubectl` ~30 s to’xtab
turadi. Bu normal.

### 4. Control plane: kubelet va kubectl

```bash
apt-mark unhold kubelet kubectl
apt-get install -y kubelet=1.30.2-1.1 kubectl=1.30.2-1.1
apt-mark hold kubelet kubectl
systemctl daemon-reload
systemctl restart kubelet
kubectl uncordon controlplane
kubectl get nodes
# controlplane   Ready   control-plane   v1.30.2    <- control plane tugadi
# node01         Ready   <none>          v1.29.4
```

### 5. Worker: control plane’dan drain qiling, node’da yangilang

```bash
kubectl drain node01 --ignore-daemonsets
```

```bash
# node01 da
apt-mark unhold kubeadm
apt-get install -y kubeadm=1.30.2-1.1
apt-mark hold kubeadm
kubeadm upgrade node                       # lokal kubelet konfiguratsiyasini klasterdan yangilaydi
apt-mark unhold kubelet kubectl
apt-get install -y kubelet=1.30.2-1.1 kubectl=1.30.2-1.1
apt-mark hold kubelet kubectl
systemctl daemon-reload
systemctl restart kubelet
```

```bash
# yana control plane'da
kubectl uncordon node01
kubectl get nodes
# controlplane   Ready   control-plane   v1.30.2
# node01         Ready   <none>          v1.30.2
```

### 6. Tekshiring

```bash
kubectl get pods -n kube-system -o wide     # hammasi Running, kube-proxy/CoreDNS yangi image'da
kubectl get all -A | grep -v Running | head  # noto'g'ri holatdagi narsa bormi?
kubeadm upgrade plan                        # "You're up to date"
```

:::exam-tip
Nomzodlar tashlab ketadigan olti narsa, uchrash chastotasi bo’yicha:
repozitoriy o’zgarishi (keyin `apt` versiyani topa olmaydi), `apt-mark unhold`
(keyin `apt` rad etadi), kubelet’ni qayta ishga tushirish (keyin node eski
versiyani ko’rsatadi), uncordon (keyin keyingi topshiriqning Pod’lari hech
qachon joylashmaydi), worker’ni control plane’dan oldin qilish (keyin `kubeadm
upgrade node` norozilik bildiradi) va drain’dagi `--ignore-daemonsets`. Bu
ro’yxatni imtihon oldidagi kechada yana bir marta o’qing.
:::

:::tip
`apt-mark hold` - paketlar aloqasi yo’q `apt-get upgrade` tufayli tasodifan
yangilanib ketmasligining sababi. Unhold qiling, aniq versiyani o’rnating,
yana hold qiling - birga yuradigan uchta qator.
:::

## O’zingizni tekshiring

1. Qaysi ikkita buyruq **faqat** control plane node’da ishlaydi va boshqa hech
   qayerda emas?
2. Nega `kubeadm upgrade node` versiya argumentini olmaydi?
3. `apt-get install kubeadm=1.30.2-1.1` "version not found" deydi. Nimani
   tashlab ketdingiz?
