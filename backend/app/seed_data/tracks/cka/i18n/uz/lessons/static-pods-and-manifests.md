## API serversiz Pod’lar

Kubelet Pod’larni o’z diskidagi fayllardan ishga tushira oladi - bunda na API
server, na scheduler ishtirok etadi. Pod manifestini kubelet’ning **static Pod
yo’li**ga tashlang: kubelet uni yaratadi, o’lsa qayta ishga tushiradi va fayl
yo’qolganda olib tashlaydi. Bular - **static Pod’lar**.

kubeadm control plane’i aynan shu tarzda ko’tariladi: API server, controller
manager, scheduler va etcd - `/etc/kubernetes/manifests` ichidagi static
Pod’lar. Kubelet ularni fayllardan ishga tushiradi; *shundan keyingina*
qolgan hamma narsa murojaat qiladigan API server paydo bo’ladi.

```bash
grep staticPodPath /var/lib/kubelet/config.yaml
# staticPodPath: /etc/kubernetes/manifests
ls /etc/kubernetes/manifests
# etcd.yaml  kube-apiserver.yaml  kube-controller-manager.yaml  kube-scheduler.yaml
```

:::exam-tip
Yo’l har doim ham sukut bo’yicha bo’lavermaydi. Uni
`/var/lib/kubelet/config.yaml`’dan (`staticPodPath`), eskiroq sozlamalarda esa
kubelet’ning `--pod-manifest-path` flag’idan o’qing. Topshiriq uni g’ayrioddiy
joyga qo’yib, sizdan topishni so’rashi mumkin.
:::

## Mirror Pod’lar

Kubelet har bir static Pod haqida API serverga **mirror Pod** sifatida xabar
beradi, shuning uchun `kubectl get pods` uni ko’rsatadi. Siz uni ko’ra olasiz,
lekin boshqara olmaysiz: mirror’ni o’chirsangiz, kubelet uni qayta yaratadi;
tahrirlasangiz, hech narsa o’zgarmaydi. Static Pod’ni o’zgartirish yoki olib
tashlashning yagona yo’li - node’dagi uning **faylini** o’zgartirish yoki
o’chirish.

Belgisi - nomida: mirror Pod’ning nomi manifest nomi, ustiga `-`, ustiga
**node nomi**.

```bash
kubectl get pods -A | grep controlplane
# kube-system   etcd-controlplane                      1/1  Running
# kube-system   kube-apiserver-controlplane            1/1  Running
kubectl get pod kube-apiserver-controlplane -n kube-system -o yaml | grep -A2 ownerReferences
#   ownerReferences:
#   - kind: Node            <- ReplicaSet'ga emas, node'ga tegishli
```

## Uni yaratish

```bash
# node ustida
kubectl run static-busybox --image=busybox --command -- sleep 1000 $do \
  > /etc/kubernetes/manifests/static-busybox.yaml
# ~20 s dan keyin
kubectl get pods
# static-busybox-controlplane   1/1   Running
```

Kubelet katalogni davriy tekshiradi (sukut bo’yicha har 20 soniyada), shuning
uchun qisqa kechikish bo’ladi. Faylni joyida tahrirlash Pod’ni qayta yaratadi;
faylni o’chirish uni o’chiradi.

```bash
# qaysi node? manifestni control plane'da emas, O'SHA node'da qidiring
kubectl get pod static-greenbox-node01 -o wide       # NODE ustuni
ssh node01
ls /etc/kubernetes/manifests                          # yoki staticPodPath ko'rsatgan joyda
rm /etc/kubernetes/manifests/static-greenbox.yaml
```

:::warning
Static Pod’lar har doim faqat **Pod** bo’ladi - manifest katalogidan
Deployment, DaemonSet yoki Service ishlamaydi. U yerga tashlangan Service
manifesti e’tiborsiz qoldiriladi (`journalctl -u kubelet`’da bitta log qatori
bilan).
:::

## Bu control plane’dan tashqarida nega muhim

- **Nosozlikni bartaraf etish**: crash-loop’ga tushgan control plane
  komponenti - manifesti buzuq static Pod. Siz faylni tuzatasiz, kubelet uni
  qayta ishga tushiradi. `kubectl apply` ham, `systemctl restart` ham kerak
  emas - faqat faylni saqlang va kuting.
- **Klaster yangilanishlari**: `kubeadm upgrade apply` o’sha manifestlarni
  yangi image teglari bilan qayta yozadi; almashtirishni kubelet bajaradi.
- **Bootstrapping**: API serverdan oldin mavjud bo’lishi shart bo’lgan hamma
  narsa.

## O’zingizni tekshiring

1. `kubectl get pods -A` natijasidan qaysi Pod’lar static ekanini qanday
   aniqlaysiz?
2. Static Pod’ni `kubectl delete` qildingiz, u qaytib keldi. Uni haqiqatan
   qanday olib tashlaysiz?
3. kube-scheduler static Pod’i crash-loop’da. Nimani tahrirlaysiz va uni nima
   qayta ishga tushiradi?
