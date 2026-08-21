## Default scheduler yetarli bo’lmaganda

Default scheduler umumiy maqsadli. Ba’zan workload’ga boshqacha joylashtirish
mantig’i kerak bo’ladi - batch job’lar uchun bin-packing, maxsus algoritm,
vendor’dan kelgan scheduler. Kubernetes bir vaqtning o’zida **bir nechta
scheduler** ishlatishga imkon beradi va har bir Pod o’zini qaysi biri
joylashtirishini ayta oladi.

```yaml
spec:
  schedulerName: my-scheduler       # sukut bo'yicha "default-scheduler"
  containers: [...]
```

Scheduler nomini ko’rsatgan Pod’ni qolgan barcha scheduler’lar e’tiborsiz
qoldiradi. Ko’rsatilgani ishlamayotgan bo’lsa, Pod **event’siz Pending** bo’lib
qoladi - bu ham klassik nosozlik topshirig’i: yechim yo o’sha scheduler’ni
ishga tushirish, yo `schedulerName`ni olib tashlash, toki Pod’ni default
scheduler olib ketsin.

## Ikkinchi scheduler’ni joylashtirish

Ikkinchi scheduler - o’sha binary’ning boshqa nom bilan, Pod (yoki static Pod,
yoki Deployment) sifatida ishlayotgan nusxasi. Uning nomi
**KubeSchedulerConfiguration** dan keladi:

```yaml
# my-scheduler-config.yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
  - schedulerName: my-scheduler
leaderElection:
  leaderElect: false            # yagona nusxaga qulf kerak emas
```

```bash
kubectl create configmap my-scheduler-config -n kube-system --from-file=my-scheduler-config.yaml
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-scheduler
  namespace: kube-system
spec:
  serviceAccountName: my-scheduler          # Pod/Node o'qish va binding yozish uchun RBAC kerak
  containers:
    - name: kube-scheduler
      image: registry.k8s.io/kube-scheduler:v1.30.0   # klaster bilan bir xil versiya
      command:
        - kube-scheduler
        - --config=/etc/kubernetes/my-scheduler/my-scheduler-config.yaml
      volumeMounts:
        - name: config
          mountPath: /etc/kubernetes/my-scheduler
  volumes:
    - name: config
      configMap:
        name: my-scheduler-config
```

RBAC qismi - `system:kube-scheduler` va `system:volume-scheduler`
ClusterRole’lariga bog’langan ServiceAccount hamda lease’lar uchun Role -
hujjatlarda "Configure Multiple Schedulers" bo’limida turibdi; imtihon uni
nusxalashga ruxsat beradi. Image versiyasi control plane bilan mos kelishi
shart:

```bash
kubectl get pod kube-scheduler-controlplane -n kube-system -o jsonpath='{.spec.containers[0].image}'
```

## Pod’ni qaysi scheduler joylashtirganini tasdiqlash

```bash
kubectl get events -o wide | grep Scheduled
# ...  Scheduled  pod/nginx  my-scheduler  Successfully assigned default/nginx to node02
kubectl describe pod nginx | grep -A1 Events
```

Event’ning `SOURCE` ustuni scheduler nomini ko’rsatadi. Topshiriq so’raydigan
dalil ana shu.

```bash
kubectl logs my-scheduler -n kube-system        # scheduler'ning o'z nuqtayi nazari
```

:::exam-tip
Uchta narsa xato ketadi: Pod’ning `schedulerName`i va profildagi
`schedulerName` aynan mos kelmaydi; yagona nusxada `leaderElect` `true`
qoldirilgan, lease ruxsatlari esa yo’q, shuning uchun u abadiy kutadi; image
tegi klaster versiyasiga mos emas. Har biri scheduler Pod’ining
`kubectl logs` natijasida bir necha soniya ichida ko’rinadi.
:::

## Bitta scheduler’da bir nechta profil

Har doim ham ikkinchi jarayon kerak emas. Bitta scheduler binary’si bir nechta
**profil**ga xizmat qila oladi, har birining o’z nomi va plugin to’plami
bo’ladi:

```yaml
profiles:
  - schedulerName: default-scheduler
  - schedulerName: bin-packing
    plugins:
      score:
        disabled:
          - name: NodeResourcesBalancedAllocation
        enabled:
          - name: NodeResourcesMostAllocated
```

Pod’lar profilni `schedulerName` orqali xuddi u alohida scheduler bo’lgandek
tanlaydi. Yengilroq, qo’shimcha RBAC kerak emas va bu - keyingi darsning
mavzusi.

## O’zingizni tekshiring

1. Pod `schedulerName: foo` deb ko’rsatgan, `foo` esa ishlamayapti. Nimani
   ko’rasiz va ikkita yechim qanday?
2. Pod’ni qaysi scheduler joylashtirganini event’ning qaysi maydoni
   isbotlaydi?
3. Qachon ikkinchi scheduler jarayoni o’rniga ikkinchi profilni afzal
   ko’rasiz?
