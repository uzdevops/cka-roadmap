## Ba’zi Pod’lar boshqalardan muhimroq

Klaster to’lib qolganda scheduler tanlov qilishi kerak: yangi Pod’ni Pending
holatda qoldirish yoki joy bo’shatish uchun kamroq muhim narsani **evict**
qilish. Priority - unga qaysi Pod’lar kamroq muhimligini aytish usuli.

**PriorityClass** - butun klaster miqyosidagi obyekt bo’lib, u butun songa nom
beradi:

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 100000
globalDefault: false
preemptionPolicy: PreemptLowerPriority     # sukut bo'yicha; ikkinchi qiymat - Never
description: "Customer-facing workloads"
```

```bash
kubectl create priorityclass high-priority --value=100000 --description="urgent"
kubectl get priorityclass
# NAME                      VALUE        GLOBAL-DEFAULT
# high-priority             100000       false
# system-cluster-critical   2000000000   false
# system-node-critical      2000001000   false
```

Ikkita `system-*` klass har bir klaster bilan birga keladi va ularni control
plane komponentlari hamda CNI/kube-proxy DaemonSet’lari ishlatadi.
Foydalanuvchi klasslari bir milliardgacha (`1000000000`) boradi; undan yuqori
qiymatlar zaxiraga olingan.

Pod unga nom orqali qo’shiladi:

```yaml
spec:
  priorityClassName: high-priority
  containers: [...]
```

Priority class’i yo’q Pod’lar **0** priority oladi, agar biror klassda
`globalDefault: true` bo’lmasa (bunday klass ko’pi bilan bitta bo’lishi
mumkin).

## Preemption

Yuqori priority’li Pod joylasha olmaganda, scheduler *pastroq* priority’li
ba’zi Pod’larni evict qilish orqali unga joy chiqadigan node’ni qidiradi,
ularni evict qiladi (ular o’z graceful termination’ini oladi) va yangi Pod’ni
joylashtiradi. Evict qilingan Pod’lar Pending holatiga qaytadi va agar ularga
kontroller egalik qilsa, qayta rejalashtiriladi.

```bash
kubectl get events --sort-by=.lastTimestamp | grep -i preempt
# Normal  Preempted  pod/batch-7xk2  Preempted by default/important on node node02
```

`preemptionPolicy: Never` shunday klass yaratadiki, u *navbatda* pastroq
priority’lardan oldin joylashtiriladi, lekin hech kimni evict qilmaydi -
"muhim, lekin buning uchun boshqasini o’ldirishga arzimaydi" turidagi batch
ishlar uchun foydali.

:::exam-tip
Priority faqat biror narsa sig’maganda ahamiyatga ega bo’ladi. Bo’sh klasterda
yuqori priority’li Pod xuddi boshqalardek joylashadi. Agar topshiriqda "Pod X
bosim ostida ham joylashtirilishini ta’minlang" deyilsa, javob - priority;
"Pod Y nega evict qilindi" deb so’ralsa, yuqoriroq priority’li Pod nomini
ko’rsatgan preemption event’ini qidiring.
:::

## Topology spread

Maqsadi boshqacha bo’lgan yaqin rejalashtirish vositasi: replikalarni failure
domain’lar bo’ylab teng tarqatish, toki bitta node yoki zonani yo’qotish butun
ilovani ishdan chiqarmasin.

```yaml
spec:
  topologySpreadConstraints:
    - maxSkew: 1
      topologyKey: topology.kubernetes.io/zone
      whenUnsatisfiable: DoNotSchedule        # yoki ScheduleAnyway
      labelSelector:
        matchLabels:
          app: web
  containers: [...]
```

Buni shunday o’qing: `app=web` label’i bor Pod’lar orasida bitta zonadagi soni
boshqa istalgan zonadagi sondan `maxSkew`’dan ortiq oshib ketmasligi kerak.
`DoNotSchedule` bilan bu - qat’iy qoida (Pod’lar uni buzgandan ko’ra Pending
bo’lib turadi); `ScheduleAnyway` bilan esa bu - afzallik. Kalit sifatida
`kubernetes.io/hostname` zonalar o’rniga node’lar bo’ylab tarqatadi.

Deployment uchun "iltimos, har node’ga bitta replika" deyishning zamonaviy
usuli shu - podAntiAffinity xuddi shuni qattiqroq tarzda qiladi.

## O’zingizni tekshiring

1. `priorityClassName` yo’q Pod qanday priority’ga ega va u umuman biror
   narsani preempt qila oladimi?
2. `preemptionPolicy: Never` nimani o’zgartiradi va u sizga qachon kerak
   bo’ladi?
3. `app=api` Pod’larini node’lar bo’ylab ko’pi bilan bitta Pod farqi bilan
   tarqatadigan topologySpreadConstraint’ni qat’iy qoida sifatida yozing.
