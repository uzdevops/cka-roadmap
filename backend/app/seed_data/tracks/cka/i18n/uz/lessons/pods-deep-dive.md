## Pod aslida nima

Pod - bu quyidagilarni bo’lishadigan bitta yoki bir nechta konteyner:

- **network namespace** - bitta IP manzil, bitta port maydoni, shuning uchun
  Pod ichidagi konteynerlar bir-biriga `localhost` orqali yetadi;
- ularning har biri mount qila oladigan **storage volume’lar**;
- **hayot tsikli** - ular birga bitta node’ga joylashtiriladi, birga yashaydi
  va birga o’ladi.

Bu - Kubernetes joylashtiradigan eng kichik birlik. Productionda siz uni
deyarli hech qachon to’g’ridan-to’g’ri yaratmaysiz; siz Deployment yaratasiz,
u ReplicaSet yaratadi, u esa Pod’lar yaratadi. Lekin ustidagi hamma narsa shu
shakl atrofidagi o’ram, xolos.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web
  labels:
    app: web
spec:
  containers:
    - name: nginx
      image: nginx:1.27
      ports:
        - containerPort: 80
      resources:
        requests:
          memory: "64Mi"
          cpu: "250m"
        limits:
          memory: "128Mi"
          cpu: "500m"
```

## Ko’p konteynerli shablonlar

Podga ikkinchi konteynerni faqat u birinchisi bilan tarmoqni yoki fayl
tizimini bo’lishishi shart bo’lgandagina qo’ying.

**Sidecar** - asosiy konteynerni kengaytiradi. Umumiy volume’ni o’qiydigan log
jo’natuvchi:

```yaml
spec:
  volumes:
    - name: logs
      emptyDir: {}
  containers:
    - name: app
      image: myapp:1.0
      volumeMounts:
        - name: logs
          mountPath: /var/log/app
    - name: log-shipper
      image: fluent-bit:3.0
      volumeMounts:
        - name: logs
          mountPath: /var/log/app
          readOnly: true
```

**Ambassador** - chiquvchi ulanishlarni proksilaydi, shuning uchun ilova
`localhost:6379`’ga ulanadi, ambassador esa sharding yoki TLS bilan
shug’ullanadi.

**Adapter** - ilova chiqishini standart formatga keltiradi, masalan eski log
fayldan Prometheus formatida `/metrics` chiqaradi.

:::warning
Agar ikki konteyner network namespace yoki volume’ni bo’lishishi shart
bo’lmasa, ular alohida Pod’larga tegishli. Ularni bitta Podga jamlash - birga
masshtablanadi, birga qayta ishga tushadi va birga joylashtiriladi degani -
deyarli har doim noto’g’ri kelishuv.
:::

## Init konteynerlar

Har qanday ilova konteyneri ishga tushishidan **oldin**, navbat bilan
oxirigacha bajariladi. Agar biri ishlamasa, kubelet Pod’ni uning restart
policy’siga muvofiq qayta ishga tushiradi.

```yaml
spec:
  initContainers:
    - name: wait-for-db
      image: busybox:1.36
      command:
        - sh
        - -c
        - 'until nc -z postgres 5432; do echo waiting; sleep 2; done'
    - name: run-migrations
      image: myapp:1.0
      command: ["/app/migrate"]
  containers:
    - name: app
      image: myapp:1.0
```

`Init:0/2`’da qotib qolgan Pod birinchi init konteyner tugamaganini bildiradi.
Uning loglarini aynan alohida o’qing:

```bash
kubectl logs <pod> -c wait-for-db
```

## Pod hayot tsikli

`status.phase` beshta qiymatga ega:

| Faza | Ma’nosi |
| --- | --- |
| `Pending` | Qabul qilingan, lekin hamma konteyner ishlamayapti - joylashtirish, image tortish yoki init konteynerlar kutilmoqda |
| `Running` | Node’ga bog’langan, kamida bitta konteyner ishlayapti |
| `Succeeded` | Hamma konteyner 0 bilan chiqdi va qayta ishga tushmaydi |
| `Failed` | Hamma konteyner tugatildi, kamida bittasi noldan farqli kod bilan |
| `Unknown` | Node’ning kubelet’iga ulanib bo’lmayapti |

`restartPolicy` chiqishdan keyin nima bo’lishini boshqaradi:

- `Always` (sukut bo’yicha va Deployment’lar uchun yagona variant)
- `OnFailure` - Job’lar ishlatadi
- `Never` - bir martalik debug Pod’lari uchun

## Probe’lar: Kubernetesga "sog’lom" nimaligini aytish

Uchta probe, uchta har xil vazifa. Ularni chalkashtirish - klassik imtihon
tuzog’i.

```yaml
spec:
  containers:
    - name: app
      image: myapp:1.0
      startupProbe:                 # "yuklanishni tugatdimi?"
        httpGet: {path: /healthz, port: 8080}
        failureThreshold: 30
        periodSeconds: 5            # ishga tushishga 150s gacha beradi
      livenessProbe:                # "uni o'ldirib qayta tushirayinmi?"
        httpGet: {path: /healthz, port: 8080}
        initialDelaySeconds: 10
        periodSeconds: 10
        failureThreshold: 3
      readinessProbe:               # "u trafik olishi kerakmi?"
        httpGet: {path: /ready, port: 8080}
        periodSeconds: 5
```

- **liveness** ishlamasa -> konteyner **qayta ishga tushiriladi**.
- **readiness** ishlamasa -> Pod **Service endpoint’laridan olib tashlanadi**,
  lekin ishlashda davom etadi.
- **startup** ishlamasa -> konteyner qayta ishga tushiriladi; u ishlab
  turganda liveness va readiness o’chirilgan bo’ladi.

Probe handler’lari `httpGet`, `tcpSocket`, `exec` yoki `grpc` bo’lishi mumkin.

:::exam-tip
Bog’liqlikni (ma’lumotlar bazasi, boshqa xizmat) chaqiradigan liveness probe
o’sha bog’liqlikda kichik uzilish bo’lishi bilanoq butun klaster bo’ylab
zanjirli qayta ishga tushishlarni keltirib chiqaradi. Liveness *faqat*
jarayonning o’zini tekshirishi kerak. Bog’liqlik tekshiruvlarining o’rni -
readiness.
:::

## Resurslar: request va limit

```yaml
resources:
  requests:                # scheduler node tanlash uchun ishlatadi
    cpu: "250m"            # 250 millicore = yadroning 0.25 qismi
    memory: "64Mi"
  limits:                  # ishlash vaqtida kernel majburlaydi
    cpu: "500m"
    memory: "128Mi"
```

- **CPU limit**dan oshish konteynerni sekinlashtiradi (throttle). U
  o’ldirilmaydi.
- **Memory limit**dan oshish konteynerni **OOMKilled** qiladi va qayta ishga
  tushiradi.
- Joylashtirishni limit emas, request belgilaydi. Bo’sh *so’ralgan* sig’imi
  qolmagan node bo’sh turgan bo’lsa ham Pod’ingizni qabul qilmaydi.

## Pod’lar nega qotib qoladi: ma’lumotnoma jadvali

| Status | Sabab | Birinchi buyruq |
| --- | --- | --- |
| `Pending` | Mos node yo’q: resurs yetishmaydi, taint, node selector, bog’lanmagan PVC | `kubectl describe pod` -> Events |
| `ContainerCreating` | Image tortilmoqda yoki volume mount bo’lmayapti | `kubectl describe pod` -> Events |
| `ImagePullBackOff` / `ErrImagePull` | Noto’g’ri image nomi/tegi, imagePullSecret’siz shaxsiy registry | `kubectl describe pod` |
| `CrashLoopBackOff` | Konteyner ishga tushadi va qayta-qayta chiqib ketadi | `kubectl logs --previous` |
| `OOMKilled` | Memory limitdan oshib ketilgan | `kubectl describe pod` -> Last State |
| `Init:0/2` | Init konteyner tugamagan | `kubectl logs -c <init-name>` |
| `Terminating` (qotgan) | Finalizer yoki SIGTERM’ni e’tiborsiz qoldirayotgan jarayon | `kubectl describe`, keyin `--force --grace-period=0` |
| `Completed` | Konteyner `restartPolicy: Always` bilan 0 qaytarib chiqdi | Job’lar uchun kutilgan holat; aks holda bu xato |

```bash
# OOMKill isboti loglarda emas, Last State ichida yashaydi
kubectl describe pod app | grep -A5 'Last State'
# Last State:     Terminated
#   Reason:       OOMKilled
#   Exit Code:    137
```

:::tip
137 chiqish kodi = 128 + 9 (SIGKILL) = deyarli har doim OOM. 143 chiqish kodi =
128 + 15 (SIGTERM) = odatiy to’xtash. Bu ikkalasini ko’rishi bilan tanish -
haqiqiy vaqtni tejaydi.
:::

## Muloyim to’xtatish

```yaml
spec:
  terminationGracePeriodSeconds: 30
  containers:
    - name: app
      image: myapp:1.0
      lifecycle:
        preStop:
          exec:
            command: ["sh", "-c", "sleep 5"]
```

O’chirishda Kubernetes: Pod’ni Service endpoint’laridan olib tashlaydi,
`preStop`’ni bajaradi, `SIGTERM` yuboradi, grace period tugagunicha kutadi,
keyin `SIGKILL` yuboradi. O’sha `sleep 5` yuk muvozanatlagichlarga jarayon
so’rovlarni rad qila boshlashidan oldin yangi ulanishlar yuborishni
to’xtatish uchun vaqt beradi.

## O’zingizni tekshiring

1. Pod `Running` holatida, lekin Service’i orqali trafik olmayapti. Birinchi
   qaysi probe’ni tekshirasiz?
2. CPU uchun resource request va resource limit orasidagi farq nima?
3. Pod’ingiz `CrashLoopBackOff` ko’rsatmoqda. Sababini ko’rsatadigan aniq
   buyruqni ayting.
