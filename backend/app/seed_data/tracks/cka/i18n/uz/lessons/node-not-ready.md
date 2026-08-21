## Node NotReady bo’lib qoladi

```bash
kubectl get nodes
# NAME       STATUS     ROLES           AGE   VERSION
# node01     NotReady   <none>          10d   v1.31.0
kubectl describe node node01
```

`describe node` biror joyga ssh qilishingizdan oldin sizga ikki narsani
aytadi.

**Condition’lar**:

```
Conditions:
  Type             Status    LastHeartbeatTime   Reason              Message
  MemoryPressure   Unknown   ...                 NodeStatusUnknown   Kubelet stopped posting node status.
  DiskPressure     Unknown
  PIDPressure      Unknown
  Ready            Unknown   ...                 NodeStatusUnknown   Kubelet stopped posting node status.
```

- Reason bilan `Ready False`: kubelet ishlayapti va muammo haqida xabar
  berayapti (konteyner runtime ishlamayapti, network plugin tayyor emas,
  disk to’la).
- `Ready Unknown` va barcha condition’lar `Unknown`: kubelet API server
  bilan **gaplashishni to’xtatgan** - to’xtagan, qulagan, sertifikatlar,
  tarmoq yoki node o’chiq.
- `MemoryPressure`/`DiskPressure`/`PIDPressure` `True`: node tirik, lekin
  resursi qurigan; kubelet Pod’larni evict qiladi va yangilarini qabul
  qilmaydi.

**Events va sig’im**: `Allocatable` va request’lar nisbati hamda
`NodeHasDiskPressure`, `ContainerGCFailed`, `Rebooted` kabi Events.

## Node ustida

```bash
ssh node01
top; free -h; df -h /; df -h /var/lib/kubelet /var/lib/containerd     # tirikmi? resursi qurib qolganmi?
systemctl status kubelet
journalctl -u kubelet -n 100 --no-pager                                 # tushuntirish deyarli har doim shu yerda
systemctl status containerd                                             # kubelet usiz Pod ishlata olmaydi
```

Agar node’ning o’zi o’chiq bo’lsa (ssh ham yo’q), bu infratuzilma masalasi:
uni yoqing. U qaytganda kubelet ishga tushadi va node Ready bo’ladi; agar
bo’lmasa, quyida davom eting.

## Kubelet ishga tushmayapti yoki ishdan chiqaverayapti

```bash
systemctl status kubelet
# ● kubelet.service - kubelet: The Kubernetes Node Agent
#    Active: activating (auto-restart) (Result: exit-code)
journalctl -u kubelet -f
```

Log sababni nomlaydi. To’rtta odatiy sabab:

| Log qatori | Sabab | Yechim |
|---|---|---|
| `failed to load Kubelet config file /var/lib/kubelet/config.yaml` / `open /etc/kubernetes/pki/CA.crt: no such file` | **`/var/lib/kubelet/config.yaml`** ichidagi noto’g’ri yo’l (`clientCAFile`, `staticPodPath`) | yo’lni to’g’rilang (haqiqiy nomni ko’rish uchun `ls /etc/kubernetes/pki/`); `systemctl restart kubelet` |
| `dial tcp 10.0.0.10:6553: connect: connection refused` / `Unable to register node` | **`/etc/kubernetes/kubelet.conf`** ichida noto’g’ri API server **manzili yoki porti** (`server: https://...:6443`) | server qatorini tuzating; kubelet’ni qayta ishga tushiring |
| `part of the existing bootstrap client certificate is expired` / `x509: certificate has expired` | kubelet’ning **client sertifikati** muddati tugagan (`/var/lib/kubelet/pki/kubelet-client-current.pem`) | control plane’dagi `kubeadm certs renew` kubelet sertifikatlarini qamrab olmaydi; yangi token bilan qayta bootstrap qiling yoki rotatsiyani tuzating; soatni tekshiring |
| `x509: certificate signed by unknown authority` | kubelet API server’ni imzolamagan CA’ga ishonadi | `kubelet.conf` ichidagi `certificate-authority-data` noto’g’ri - `/etc/kubernetes/pki/ca.crt` bilan solishtiring |
| `Failed to start ContainerManager` / `failed to run Kubelet: ... cgroup` | cgroup driver mos kelmayapti (kubelet’da `systemd`, containerd’da `cgroupfs`) | config.yaml ichidagi `cgroupDriver`’ni containerd konfiguratsiyasiga moslang |
| `Unit kubelet.service is masked` / `not found` | service’ning o’zi | `systemctl unmask kubelet`; `systemctl enable --now kubelet`; `kubelet` binary’si PATH’damikan? |

```bash
cat /var/lib/kubelet/config.yaml | grep -E "clientCAFile|staticPodPath|cgroupDriver|address|port"
cat /etc/kubernetes/kubelet.conf | grep server
ls /etc/kubernetes/pki/ /var/lib/kubelet/pki/
openssl x509 -in /var/lib/kubelet/pki/kubelet-client-current.pem -noout -dates -issuer
cat /etc/systemd/system/kubelet.service.d/10-kubeadm.conf                  # kubelet qanday ishga tushiriladi: flag'lar, env fayllar
```

Kubelet’ning **uchta fayli**, tekshirish tartibida:

1. `/var/lib/kubelet/config.yaml` - KubeletConfiguration: CA yo’li, static
   Pod yo’li, cgroup driver, klaster DNS’i, eviction chegaralari.
2. `/etc/kubernetes/kubelet.conf` - API server’ga yetish uchun ishlatadigan
   kubeconfig: server URL’i, CA ma’lumotlari, client sertifikat yo’li.
3. `/etc/systemd/system/kubelet.service.d/10-kubeadm.conf` (+
   `/var/lib/kubelet/kubeadm-flags.env`) - 1 va 2 raqamli fayllarga ishora
   qiluvchi flag’lari bor systemd drop-in.

Har qanday tahrirdan keyin: unit’ga tekkan bo’lsangiz
`systemctl daemon-reload`, so’ng `systemctl restart kubelet`, keyin
`Successfully registered node` deyilguncha `journalctl -u kubelet -f`, va
control plane’dan `Ready` bo’lguncha `kubectl get nodes`.

## Kubelet joyida, lekin node hali ham NotReady

```bash
journalctl -u kubelet | grep -iE "network|cni"
# "Container runtime network not ready: NetworkReady=false reason:NetworkPluginNotReady message:Network plugin returns error: cni plugin not initialized"
ls /etc/cni/net.d/ /opt/cni/bin/
kubectl get pods -n kube-system -o wide | grep node01            # CNI DaemonSet Pod'i shu node'da ishlayaptimi?
```

CNI konfiguratsiyasi yo’q → node ataylab NotReady deb xabar
beradi. Kubelet’ni emas, network plugin’ni (o’sha node’dagi DaemonSet
Pod’ini, konfiguratsiya faylini) tuzating.

```bash
systemctl status containerd; crictl ps                            # runtime ishlamasa → kubelet hech narsa ishlata olmaydi
```

## NotReady node’dagi Pod’lar

`--node-monitor-grace-period` (40s) o’tgach node NotReady deb belgilanadi;
Pod’ning `node.kubernetes.io/not-ready` uchun toleration’i (sukut bo’yicha
300s) tugagach kontroller uning Pod’larini evict qiladi va Deployment’lar
ularni boshqa joyda qayta yaratadi. O’lgan node’da `Terminating` holatida
qotib qolgan Pod’lar node qaytmaguncha yoki ularni majburan
o’chirmaguningizcha shundayligicha qoladi.

:::exam-tip
Imtihonning worker node savoli shunday bo’ladi: node NotReady; `ssh` bilan
kiring; `systemctl status kubelet`; `journalctl -u kubelet`; log uchta
fayldan biridagi noto’g’ri yo’l, port yoki sertifikatni nomlaydi; tuzating;
`systemctl restart kubelet`; `exit`; Ready bo’lguncha `kubectl get nodes`.
Ikkita tuzoq: kubelet.conf ichida API server porti `6553` deb yozilgani va
config.yaml ichida katta-kichik harfi bilan farq qiluvchi CA fayl nomi
(`CA.crt` va `ca.crt`).
:::

## O’zingizni tekshiring

1. Node’dagi `Ready False` va `Ready Unknown` orasidagi farq nima?
2. Kubelet’ning uchta faylini va har biri nimani sozlashini ayting.
3. Kubelet ishlayapti va ro’yxatdan o’tgan, lekin node
   `NetworkPluginNotReady` bilan NotReady. Nimani tuzatasiz va nimaga
   tegmaysiz?
