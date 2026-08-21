## Bitta control plane node - bitta nosozlik nuqtasi

Uni yo’qotsangiz: mavjud Pod’lar ishlashda davom etadi (kubelet’larga narsalarni
tirik saqlash uchun API server kerak emas), lekin yangi hech narsa sodir
bo’lmaydi - joylashtirish yo’q, masshtablash yo’q, `kubectl` yo’q, o’lgan
narsaning o’z-o’zini tiklashi yo’q. HA - bu har bir control plane
komponentidan bittadan ko’p bo’lishi va ularning har biri ishni qanday
bo’lishishini bilish.

## API server: load balancer ortida active-active

Har bir API server nusxasi holatsiz va teng huquqli; ularning hammasi bitta
etcd bilan gaplashadi. Uchtasini ishga tushiring, oldiga **load balancer**
qo’ying va har bir mijozni (kubectl, kubelet’lar, scheduler va controller
manager) biror bitta node manzili o’rniga load balancer manziliga
yo’naltiring.

```
kubectl / kubelets ──▶ lb.example.com:6443 ──▶ apiserver@cp1 :6443
                                            ──▶ apiserver@cp2 :6443
                                            ──▶ apiserver@cp3 :6443
```

kubeadm bu manzilni init paytida ichiga yozib qo’yadi:

```bash
kubeadm init --control-plane-endpoint=lb.example.com:6443 --upload-certs ...
```

`--control-plane-endpoint` har bir kubeconfig’ga va API server sertifikatining
SAN’lariga tushadi. Agar qachondir ko’paytirish niyatingiz bo’lsa, **uni hatto
bitta control plane uchun ham belgilang**: keyinroq o’zgartirish sertifikatlar
va kubeconfig’larni qayta generatsiya qilishni anglatadi. Load balancer’ning
o’zi control plane node’larda HAProxy + keepalived, bulut LB’si yoki static
Pod sifatida ishlaydigan kube-vip bo’lishi mumkin.

## Scheduler va controller manager: leader saylovi orqali active-standby

Bir xil Pod’ni joylashtirayotgan uchta scheduler - tartibsizlik bo’lardi.
Shuning uchun scheduler va controller manager har bir control plane node’da
ishlaydi, lekin faqat **leader** harakat qiladi; qolganlari kutadi.

```yaml
# ularning static Pod manifestlarida
- --leader-elect=true
- --leader-elect-lease-duration=15s
- --leader-elect-renew-deadline=10s
- --leader-elect-retry-period=2s
```

Leader `kube-system` dagi **Lease** obyektini ushlab turadi va uni har 2
soniyada yangilaydi; agar u 15 soniya davomida yangilashni to’xtatsa, boshqa
nusxa lease’ni oladi va leader bo’ladi.

```bash
kubectl get leases -n kube-system
# NAME                      HOLDER                      AGE
# kube-controller-manager   cp1_5f3a...                 30d
# kube-scheduler            cp2_91c0...                 30d
kubectl describe lease kube-scheduler -n kube-system | grep -i holder
```

"Hozir aslida qaysi scheduler joylashtiryapti" degan savolning javobi shu.

## etcd: kvorumi bilan alohida klaster

etcd’ning HA’si - etcd darslaridagi RAFT hikoyasi: toq sonli a’zolar, yozuvlar
uchun ko’pchilik kerak. Ularni joylashtirishning ikki yo’li bor:

**Stacked** (kubeadm’ning sukut varianti): etcd har bir control plane node’da
static Pod sifatida ishlaydi; uchta control plane node = uchta etcd a’zosi.

```
cp1: apiserver + cm + sched + etcd
cp2: apiserver + cm + sched + etcd
cp3: apiserver + cm + sched + etcd
```

Kamroq mashina, soddaroq; control plane node’ni yo’qotish bir etcd a’zosini
ham yo’qotadi.

**External**: etcd o’zining uchta (yoki beshta) host’ida turadi; API
server’lar ularga `--etcd-servers=https://etcd1:2379,https://etcd2:2379,...` bilan yo’naltiriladi.

```
cp1, cp2, cp3: apiserver + cm + sched
e1, e2, e3:    etcd
```

Ko’proq mashina; control plane va ma’lumotlar ombori bir-biridan mustaqil
ishdan chiqadi; buning uchun `kubeadm init` tashqi endpoint’lar va
sertifikatlar yozilgan konfiguratsiya faylidan foydalanadi. Keyingi dars -
HA’dagi etcd, batafsil.

## kubeadm HA ish oqimi, qisqacha

1. Bo’lajak control plane node’lar oldida load balancer.
2. cp1’da `kubeadm init --control-plane-endpoint=<lb>:6443 --upload-certs`
   (ikkita join buyrug’ini chiqaradi: biri control plane’lar, biri worker’lar
   uchun).
3. cp2 va cp3’da
   `kubeadm join <lb>:6443 --control-plane --certificate-key <key> ...` - ular
   umumiy sertifikatlarni klasterdan tortib oladi va o’zining control plane
   static Pod’larini ishga tushiradi.
4. CNI o’rnating; worker’larni `kubeadm join` qiling.

```bash
kubectl get nodes            # uchta control-plane, N ta worker
kubectl get pods -n kube-system | grep -E "apiserver|etcd|scheduler|controller"   # har biridan uchta
```

:::exam-tip
Imtihon sizga HA qurdirmaydi. U `--control-plane-endpoint` nima uchun
kerakligini, qaysi komponent leader ekanini yoki nechta etcd a’zosi ishdan
chiqishi mumkinligini so’rashi mumkin. Bilib qo’ying: API server’larning
hammasi LB ortida faol; scheduler va controller manager Lease’lar orqali
leader saylaydi; etcd’ga ko’pchilik kerak; kubeadm’ning `--upload-certs` +
`--certificate-key` - ikkinchi control plane CA’ni aynan shu tarzda oladi.
:::

## O’zingizni tekshiring

1. Uchta API server ishni qanday bo’lishadi, uchta scheduler-chi?
2. Qaysi obyekt hozir qaysi controller manager faol ekanini aytadi?
3. Stacked va external etcd orasidagi farq nima va kubeadm sukut bo’yicha
   qaysi birini qiladi?
