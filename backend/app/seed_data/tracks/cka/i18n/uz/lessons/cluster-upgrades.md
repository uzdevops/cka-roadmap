## Yangilash tartibi

```
1. kubeadm (asbobning o'zi)     control plane node'da
2. control plane                kubeadm upgrade apply  -> API server, controller manager, scheduler, etcd, CoreDNS, kube-proxy
3. kubelet + kubectl            control plane node'da
4. har bir worker, birma-bir:   drain -> kubeadm upgrade node -> kubelet -> uncordon
```

Tartibni version skew qoidalari belgilaydi: API server eng yangi narsa bo’lishi
kerak; kubelet’lar undan orqada qolishi mumkin, lekin hech qachon oldinda
emas; `kubeadm` yangi manifestlarni qanday yaratishni bilishi uchun yangi
versiyada bo’lishi shart.

Worker’lar uchun ikkita strategiya:

- **Rolling** - bittadan node’ni drain qilish, yangilash, uncordon qilish.
  Klaster shu davomida ishlab turadi; sig’im bir vaqtda bitta node’ga kamayadi.
- **Yangisini qo’shib, eskisini olib tashlash** - allaqachon yangi versiyadagi
  node’larni ko’tarib, eskilarini drain qilib o’chirasiz. Node group’lari bor
  cloud’lar uchun tozaroq; bare metalda ko’proq ish.

Har bir yangilashda bitta minor versiya. 1.29 → 1.30, keyin 1.30 → 1.31.

## kubeadm buni qanday ko’radi

```bash
kubeadm upgrade plan
```

```
[upgrade/versions] Cluster version: v1.29.4
[upgrade/versions] kubeadm version: v1.30.2
Components that must be upgraded manually after you have upgraded the control plane with 'kubeadm upgrade apply':
COMPONENT   NODE           CURRENT   TARGET
kubelet     controlplane   v1.29.4   v1.30.2
kubelet     node01         v1.29.4   v1.30.2

Upgrade to the latest stable version:
COMPONENT                 NODE           CURRENT   TARGET
kube-apiserver            controlplane   v1.29.4   v1.30.2
kube-controller-manager   controlplane   v1.29.4   v1.30.2
kube-scheduler            controlplane   v1.29.4   v1.30.2
kube-proxy                               1.29.4    v1.30.2
CoreDNS                                  v1.11.1   v1.11.1
etcd                      controlplane   3.5.12-0  3.5.12-0

You can now apply the upgrade by executing the following command:
        kubeadm upgrade apply v1.30.2
```

`plan` tekshiruv ro’yxatidek o’qiladi: u sizga maqsadli versiyani, `apply`
qaysi komponentlarni o’z zimmasiga olishini va - "manually" bo’limida -
o’zingiz bajarishingiz kerak bo’lgan kubelet’larni aytadi. Uni har bir
yangilashdan oldin ishga tushiring; u sakrash ruxsat etilganini ham tekshiradi.

## `kubeadm upgrade apply` nima qiladi

Control plane node’da, yangi kubeadm o’rnatilgan holda:

1. klaster sog’ligini va versiya sakrashi qonuniyligini tekshiradi;
2. yangi control plane image’larini tortib oladi;
3. `/etc/kubernetes/manifests`’dagi static Pod manifestlarini bittalab qayta
   yozadi va har biri sog’lom holda qaytishini kutadi (ularni kubelet qayta
   ishga tushiradi);
4. kube-proxy DaemonSet’ini va CoreDNS’ni yangilaydi;
5. o’zi boshqaradigan sertifikatlarni yangilaydi;
6. yangi versiyani `kubeadm-config` ConfigMap’iga yozadi.

U kubelet binary’siga yoki node paketlariga **tegmaydi** - bu undan keyingi
qo’lda bajariladigan qadam.

Qo’shimcha control plane node’larda (HA) va worker’larda buyruq -
`kubeadm upgrade node`: u klasterdan yangi konfiguratsiyani o’qiydi va lokal
kubelet konfigini (control plane node’larda esa lokal static Pod manifestlarini
ham) yangilaydi. Versiya argumenti yo’q - u `apply` allaqachon belgilagan
narsaga ergashadi.

## Worker tomoni

```bash
# kubectl bor mashinadan:
kubectl drain node01 --ignore-daemonsets
# node01 da:
apt-get install -y kubeadm=1.30.2-*
kubeadm upgrade node
apt-get install -y kubelet=1.30.2-* kubectl=1.30.2-*
systemctl daemon-reload && systemctl restart kubelet
# control plane'ga qaytib:
kubectl uncordon node01
kubectl get nodes            # node01 v1.30.2 ni ko'rsatadi
```

:::exam-tip
Topshiriqda qaysi versiya kerakligi aytiladi va bu odatda keyingi minorning eng
so’nggi patch’i. Avval control plane’ni qiling, **`kubectl get nodes` unda yangi
VERSION ko’rsatayotganini tekshiring**, keyin worker’ni. Agar ishni
tugatganingizdan keyin ham worker eski versiyani ko’rsatsa, kubelet’ni qayta
ishga tushirishni unutgansiz - `systemctl restart kubelet` va yana qarang.
VERSION ustuni - kubelet versiyasi.
:::

## Ko’p uchraydigan xatolar

| Belgi | Sababi |
|---|---|
| `kubeadm=1.30.2-*` topilmadi | paket repozitoriysi hali ham `/v1.29/`’ga qaraydi |
| `upgrade apply` rad etadi: "skipping phase ... pre-flight" | control plane sog’lom emas - avval shuni yoki u nomlagan aniq tekshiruvni tuzating |
| yangilashdan keyin node eski versiyani ko’rsatadi | kubelet yangilanmagan yoki qayta ishga tushirilmagan |
| drain paytida Pod qotib qoldi | PDB yoki `--force`’siz boshqarilmaydigan Pod |

## O’zingizni tekshiring

1. Yangilashning to’rtta bosqichini tartib bilan yozing va har biri qaysi
   node’da bajarilishini ayting.
2. `kubeadm upgrade apply` nimani o’zgartiradi va nimani sizga qo’lda qilish
   uchun qoldiradi?
3. Barcha buyruqlarni bajarganingizdan keyin ham `kubectl get nodes`’da worker
   eski versiyani ko’rsatyapti. Ehtimol nimani o’tkazib yubordingiz?
