## Tiklanishning uchta qatlami

Kubernetes sizning ilovangiz uchun "sog’lom" nimani anglatishini bilmaydi. U
uch darajada uchta mexanik narsani biladi, ulardan qanday foydalanishni esa
siz aytasiz.

| Qatlam | Mexanizm | Nimani tuzatadi |
|---|---|---|
| konteyner | `restartPolicy` + probe’lar | chiqib ketgan yoki javob bermay qolgan jarayon |
| Pod to’plami | ReplicaSet / Deployment | yo’qolgan Pod (node o’ldi, evict qilindi, o’chirildi) |
| node | node kontrolleri + evict | hisobot berishni to’xtatgan node |

Bu dars - birinchi qatlam haqida. Ikkinchisini siz allaqachon bilasiz;
uchinchisi - taint’lar darsida uchratgan `node.kubernetes.io/not-ready`
toleration’i.

## restartPolicy

```yaml
spec:
  restartPolicy: Always      # sukut bo'yicha: konteyner har chiqqanda qayta ishga tushiriladi
  # OnFailure                # faqat noldan farqli chiqishda qayta ishga tushirish - Job'lar
  # Never                    # tegilmaydi - qayta urinmasligi kerak Job'lar, bir martalik debug
```

U Pod’dagi **hamma** konteynerlarga tegishli va o’zgarmas. `Always` bilan
ishdan chiqayotgan konteyner eksponensial kutish bilan qayta ishga
tushiriladi (10 s, 20 s, 40 s ... 5 daqiqada cheklanadi) - `CrashLoopBackOff`
holati esa o’sha qayta ishga tushirishlar orasidagi *kutish*, alohida
nosozlik emas.

## Probe’lar

kubelet konteynerdan uning ahvolini uch xil usulda, uch xil maqsadda so’rashi
mumkin:

| Probe | Savol | Ishlamasa |
|---|---|---|
| **liveness** | jarayon tirikmi va qotib qolmaganmi? | konteynerni qayta ishga tushiradi |
| **readiness** | u *hozir* trafik ola oladimi? | Pod’ni Service endpoint’laridan olib tashlaydi (qayta ishga tushirmaydi) |
| **startup** | u ishga tushishni tugatdimi? | kutishda davom etadi; u o’tmaguncha liveness/readiness ushlab turiladi |

```yaml
containers:
  - name: api
    image: myapi:2.0
    ports: [{containerPort: 8080}]
    startupProbe:
      httpGet: {path: /healthz, port: 8080}
      failureThreshold: 30         # 30 x 5 s = ishga tushishga 2.5 daqiqa
      periodSeconds: 5
    livenessProbe:
      httpGet: {path: /healthz, port: 8080}
      periodSeconds: 10
      failureThreshold: 3          # ketma-ket uchta o'tmagan urinish -> restart
    readinessProbe:
      httpGet: {path: /ready, port: 8080}
      periodSeconds: 5
```

Probe qilishning uchta yo’li:

```yaml
httpGet: {path: /healthz, port: 8080}                # 200-399 = muvaffaqiyat
tcpSocket: {port: 5432}                               # ulanish qabul qilindi = muvaffaqiyat
exec: {command: ["cat", "/tmp/healthy"]}              # 0 bilan chiqish = muvaffaqiyat
grpc: {port: 9090}                                    # gRPC health protokoli
```

Har bir probe’dagi vaqt sozlagichlari: `initialDelaySeconds`,
`periodSeconds`, `timeoutSeconds`, `successThreshold`, `failureThreshold`.

## Ikkita xato

**Haddan tashqari qattiq liveness probe.** Agar ilova yuk ostida sekinlashsa
va probe timeout’ga uchrasa, kubelet uni qayta ishga tushiradi - bu yukni
battar og’irlashtiradi - keyin yana qayta ishga tushiradi va siz sekin
xizmatni o’lik xizmatga aylantirib qo’yasiz. Liveness’ni arzon va lokal
qiling ("jarayon javob beryaptimi"), hech qachon "ma’lumotlar bazasiga yeta
olamanmi" emas. Bunisi - readiness’ning ishi.

**Readiness probe yo’qligi.** Usiz Pod konteynerlari ishga tushishi bilanoq
Ready bo’ladi va Service hali yuklanayotgan ilovaga trafik yuboradi - yoki
rolling update paytida hali ishlamayotgan yangi Pod’larga, natijada rollout
"muvaffaqiyatli" tugaydi, foydalanuvchilar esa xatolarni ko’radi.
`maxUnavailable: 0` ga ma’no beradigan narsa - aynan readiness.

:::exam-tip
"Pod’lar Running, lekin Service xato qaytaryapti / endpoint’i yo’q" - READY
ustuniga qarang: `Running` bilan birga turgan `0/1` readiness probe
o’tmayotganini bildiradi va `kubectl describe pod` HTTP kodi yoki ulanish
xatosi bilan `Readiness probe failed: ...` ni ko’rsatadi. Odatdagi sabab -
probe’dagi noto’g’ri path yoki port.
:::

## Probe muammosini o’qish

```bash
kubectl get pods                    # READY 0/1 Running = readiness; RESTARTS o'syapti = liveness
kubectl describe pod api | grep -E "Liveness|Readiness|Startup" -A1
kubectl describe pod api | tail -8  # Warning  Unhealthy  Liveness probe failed: HTTP probe failed with statuscode: 500
kubectl get events --field-selector reason=Unhealthy
```

## O’z-o’zini tiklash, yig’ib qo’yilgan holda

Uchta replikali, readiness va liveness probe’lari bor, sukut bo’yicha
toleration’lar bilan node’larda ishlayotgan Deployment:

- konteyner qotib qoladi → liveness o’tmaydi → kubelet uni qayta ishga
  tushiradi;
- konteyner ishga tushayapti → readiness o’tmaydi → tayyor bo’lgunicha trafik
  yo’q;
- Pod o’chirildi yoki node o’ldi → ReplicaSet o’rniga yangisini yaratadi; node
  kontrolleri 5 daqiqa NotReady’dan keyin evict qiladi;
- rollout paytida yangi Pod’lar faqat tayyor bo’lgach trafik oladi, eskilari
  shu paytgacha saqlanadi.

Bularning hech biri uxlamay o’tirgan operatorni talab qilmaydi. Va’da shu,
uni haqiqatga aylantiradigan narsa esa - probe’lar.

## O’zingizni tekshiring

1. Liveness probe uch marta o’tmadi. Nima bo’ladi? Readiness probe uch marta
   o’tmadi. Buning o’rniga nima bo’ladi?
2. Nega "ma’lumotlar bazasiga yeta olamanmi" yomon liveness tekshiruvi, lekin
   o’rinli readiness tekshiruvi?
3. Pod `Running`, `READY 0/1` va nol restart bilan turibdi. Qaysi probe va
   sababini qaysi buyruq ko’rsatadi?
