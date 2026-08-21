## Bitta qaror, sekundiga bir necha marta

Scheduler aynan bitta savolga javob beradi: **bu Pod qaysi node’da ishlashi
kerak?** U Pod’ni ishga tushirmaydi - buni tanlangan node’dagi kubelet qiladi.
Scheduler faqat javobni (`spec.nodeName`) Pod obyektiga yozadi, o’sha node’dagi
kubelet esa o’ziga biriktirilgan Pod’ni ko’radi va ishni o’z zimmasiga oladi.

```
yangi Pod (nodeName bo'sh) ──▶ scheduler ──▶ nodeName=node02 bo'lgan Pod ──▶ node02 dagi kubelet
```

Har bir Pod uchun ikki bosqich:

1. **Filtrlash** - uni ishlata olmaydigan node’larni chetga surish: Pod’ning
   *request*’lari uchun yetarli bo’sh CPU yoki xotira yo’q, Pod chidamaydigan
   taint bor, mos kelmaydigan `nodeSelector` yoki node affinity, allaqachon
   band bo’lgan majburiy port, u yerga ulana olmaydigan volume.
2. **Ball berish** - omon qolganlarni saralash: replikalarni node’lar bo’ylab
   tarqatish, image’i allaqachon bor node’larni afzal ko’rish, preferred
   affinity’larni hisobga olish, resurs sarfini muvozanatlash. Eng yuqori ball
   yutadi; teng ballar tasodifiy hal qilinadi.

Bu track’ning rejalashtirish bosqichidagi hamma narsa - label’lar, taint’lar,
affinity, resurs request’lari, priority - o’sha ikki qadam natijasini
o’zgartirish usuli.

## U qanday ishlaydi

```bash
cat /etc/kubernetes/manifests/kube-scheduler.yaml
kubectl get pods -n kube-system | grep scheduler
```

```yaml
- kube-scheduler
- --kubeconfig=/etc/kubernetes/scheduler.conf
- --authentication-kubeconfig=/etc/kubernetes/scheduler.conf
- --authorization-kubeconfig=/etc/kubernetes/scheduler.conf
- --bind-address=127.0.0.1
- --leader-elect=true
```

Flag’lar ro’yxati qisqa, chunki scheduler xatti-harakatining ko’p qismi
flag’lar orqali emas, **KubeSchedulerConfiguration** fayli (`--config`) orqali
sozlanadi - scheduler-profiles darsida profillar va plugin’lar aynan shu
tarzda sozlanadi.

## Scheduler bo’lmaganda

Scheduler ishlamay qolsa, yangi Pod’lar shunchaki **Pending** bo’lib qoladi va
node’lar haqida umuman event bo’lmaydi - `kubectl describe pod` yaratilish
qatoridan keyin hech narsa ko’rsatmaydi, chunki unga hech kim qaramagan.
`nodeName`ni o’zingiz yozib, Pod’ni qo’lda joylashtirishingiz mumkin (qo’lda
rejalashtirish darsi); kubelet bu maydonni kim yozganiga ahamiyat bermaydi.

```bash
kubectl get pods -n kube-system | grep scheduler        # umuman Running holatdami?
kubectl logs -n kube-system kube-scheduler-controlplane
kubectl get events --sort-by=.lastTimestamp | tail
```

:::exam-tip
Pending Pod’lar ikki xil bo’ladi. **Event yo’q** = scheduler uni umuman
ko’rmagan: scheduler ishlamayapti yoki Pod mavjud bo’lmagan `schedulerName`ni
ko’rsatgan. **FailedScheduling event** = scheduler uni ko’rgan, lekin node
topmagan: xabarni o’qing - u so’zma-so’z har bir node nega rad etilganini
sanab beradi ("1 node(s) had untolerated taint", "Insufficient cpu").
:::

## Rejalashtirish qarorini o’qish

```bash
kubectl describe pod web | grep -A3 Events
#  Normal  Scheduled  12s  default-scheduler  Successfully assigned default/web to node02
```

O’sha qatordagi `default-scheduler` - scheduler’ning **nomi**. Pod
`spec.schedulerName` orqali boshqasini so’rashi mumkin; ikkinchi, maxsus
scheduler’ni yonma-yon ishlatish shu tarzda amalga oshiriladi
(multiple-schedulers darsi) - va ishlamayotgan scheduler nomini yozib, Pod’ni
abadiy Pending holatda qoldirish ham shu tarzda bo’ladi.

```bash
kubectl get pods -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName,SCHED:.spec.schedulerName
```

## U nima qilmaydi

- U ishlayotgan Pod’larni ko’chirmaydi. Pod bir marta joylashtiriladi; agar
  keyinchalik node mos kelmay qolsa, kimdir (descheduler yoki siz) Pod’ni
  o’chirmaguncha hech narsa bo’lmaydi.
- U limit’larni majburlamaydi. Filtrlash *request*’lardan foydalanadi;
  limit’lar - kubelet va yadroning ishi.
- U Pod yaratmaydi. Bu - controller manager’ning ishi.

## O’zingizni tekshiring

1. Scheduler aynan nimani yozadi va unga qaysi komponent javob qaytaradi?
2. Pod Pending holatda, umuman event yo’q. Ikkita sababni ayting.
3. Nega filtrlash limit’lardan emas, resurs request’laridan foydalanadi?
