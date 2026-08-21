## Node’ni xizmatdan xavfsiz chiqarish

Kernel patch, reboot, apparatni almashtirish: node bir muddat yo’q bo’ladi va
siz Kubernetes buni kutilmagan hodisa deb qabul qilishini xohlamaysiz. Uchta
buyruq buni ataylab qilingan ishga aylantiradi.

```bash
kubectl cordon node01        # unschedulable deb belgilash: bu yerga YANGI hech narsa tushmaydi; mavjud Pod'lar qoladi
kubectl drain node01 ...     # cordon + har bir Pod'ni yumshoq evict qilish, kontrollerlar ularni boshqa joyda qayta yaratadi
kubectl uncordon node01      # yana xizmatda
```

```bash
kubectl get nodes
# NAME     STATUS                     ROLES    AGE   VERSION
# node01   Ready,SchedulingDisabled   <none>   10d   v1.30.2
```

Cordon aynan `SchedulingDisabled` ko’rinishida namoyon bo’ladi. Ichida bu taint
- `node.kubernetes.io/unschedulable:NoSchedule` - shuning uchun taint’lar
haqida o’rganganingizning hammasi bu yerda ham amal qiladi.

## drain va u talab qiladigan flaglar

```bash
kubectl drain node01 --ignore-daemonsets
```

Drain sukut bo’yicha ikki holatda rad etadi va qaysi flagni qo’shish
kerakligini aytadi:

| Xabar | Sababi | Flag |
|---|---|---|
| `cannot delete DaemonSet-managed Pods` | DaemonSet ularni baribir o’sha node’da qayta yaratadi; evict qilishning ma’nosi yo’q | `--ignore-daemonsets` |
| `cannot delete Pods not managed by ReplicationController, ReplicaSet, Job, DaemonSet or StatefulSet` | yalang’och Pod hech qayerda qaytib **kelmaydi** - siz uni butunlay yo’q qilgan bo’lasiz | `--force` |
| `cannot delete Pods with local storage` | emptyDir ma’lumotlari evict paytida yo’qoladi | `--delete-emptydir-data` |

`--force` - to’xtab o’ylash kerak bo’lgani: u "ha, o’sha boshqarilmaydigan
Pod’ni butunlay o’chir" degani. Imtihonda topshiriqda "Pod yo’qolmasligi kerak"
deyilishi mumkin - unda drain qila olmaysiz; cordon qilasiz va Pod’ni qo’lda
ko’chirasiz.

```bash
kubectl drain node01 --ignore-daemonsets --delete-emptydir-data --force --grace-period=30
```

Drain **evict qiladi** (Eviction API orqali), shuning uchun u
PodDisruptionBudget’larga rioya qiladi: agar PDB "3 ta web Pod’dan kamida 2
tasi ishlab turishi kerak" desa va evict buni buzsa, drain kutadi va qayta
urinadi. Bu - foydali xususiyat, va PDB hech qachon bajarilmaydigan bo’lganda
"drain’im abadiy osilib qoldi" ning sababi ham.

## Evict qilingan Pod’larga nima bo’ladi

Ular grace period bilan o’chiriladi; ularning kontrollerlari (ReplicaSet,
StatefulSet, Job) o’rniga yangilarini yaratadi, ularni esa scheduler qolgan
node’larga joylashtiradi - joy bor bo’lsa. Ikki node’li klasterda bitta
worker’ni drain qilish qolgan biri hamma narsani ko’tarishi kerak degani; agar
ko’tara olmasa, node qaytmaguncha Pod’lar Pending holatida turadi.

```bash
kubectl get pods -A -o wide | grep node01     # endi faqat DaemonSet Pod'lari bo'lishi kerak
```

## Taqqoslash uchun: node controller timeout’i

Agar siz drain **qilmasdan** shunchaki reboot qilsangiz, kubelet heartbeat
yuborishni to’xtatadi, node ~40 s dan keyin `NotReady` bo’ladi va
**pod-eviction timeout**dan keyin (sukut bo’yicha 5 daqiqa, ya’ni har bir
Pod’dagi `tolerationSeconds: 300` li
`node.kubernetes.io/not-ready:NoExecute` tolerationi) node controller
Pod’larni evict qiladi. Besh daqiqadan kam davom etadigan reboot workload’lar
uchun ko’rinmaydi - faqat o’sha node’dagi Pod’lar shu vaqt davomida mavjud
bo’lmaydi. Drain - "besh daqiqa mavjud emas" bilan "reboot boshlanishidan
oldin ko’chirilgan" orasidagi farq.

## Xizmat ko’rsatishdan keyin

```bash
kubectl uncordon node01
kubectl get nodes                       # Ready, SchedulingDisabled yo'q
```

Uncordon Pod’larni orqaga **ko’chirmaydi**. Node shunchaki yana yaroqli bo’ladi;
yangi Pod’lar u yerga tushishi mumkin, eskilari esa ketgan joyida qoladi.
Muvozanat kerak bo’lsa, Deployment’larni qayta aylantirasiz
(`kubectl rollout restart`) yoki buni descheduler qiladi.

:::exam-tip
Ball keltiradigan ketma-ketlik: `drain --ignore-daemonsets` (`--force` ni faqat
topshiriq yalang’och Pod’ni yo’qotishga rozi bo’lsa qo’shing,
`--delete-emptydir-data` ni esa u shikoyat qilsa), ishni bajaring, `uncordon`.
Uncordon’ni unutish - klassik yarim ball: topshiriq o’z tekshiruvidan o’tadi,
keyingi topshiriqning Pod’lari esa sirli tarzda o’sha node’ga hech
joylashmaydi.
:::

## O’zingizni tekshiring

1. `cordon` va `drain` orasidagi farq nima?
2. `drain` kontroller tomonidan boshqarilmaydigan ("not managed by") Pod
   tufayli rad etdi. `--force` o’sha Pod’ga nima qiladi va uni qachon
   ishlatmaslik kerak?
3. `uncordon` dan keyin evict qilingan Pod’lar node’ga qaytadimi? Ularni nima
   qaytara oladi?
