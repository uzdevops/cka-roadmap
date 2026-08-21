## Pod resurslarini uni o’ldirmasdan o’zgartirish

Kubernetes umrining ko’p qismida ishlab turgan Pod’da `resources` o’zgarmas
edi: konteynerga ko’proq memory berish uchun Pod’ni o’chirib, kattarog’ini
yaratardingiz, Deployment uchun esa bu rollout degani edi. **In-place Pod
vertical scaling** bu cheklovni olib tashlaydi: kubelet ishlab turgan
konteynerning CPU va memory limit hamda request’larini o’zgartira oladi va -
hech bo’lmaganda CPU uchun - konteynerni qayta ishga tushirmasdan.

Holati: 1.27 da `InPlacePodVerticalScaling` feature gate ostida alpha,
**1.33 dan boshlab beta va sukut bo’yicha yoqilgan**. Imtihon klasterida
tekshiring:

```bash
kubectl version --short
kubectl get --raw /metrics | grep -c InPlacePodVerticalScaling    # yoki API server flaglarini o'qing
```

## resizePolicy

Har bir konteyner har bir resurs o’zgarganda nima bo’lishi kerakligini
aytadi:

```yaml
spec:
  containers:
    - name: app
      image: myapp:1.0
      resizePolicy:
        - resourceName: cpu
          restartPolicy: NotRequired     # jonli o'zgartiriladi
        - resourceName: memory
          restartPolicy: RestartContainer # ba'zi runtime/ilovalar yangi memory limitini ko'rish uchun qayta ishga tushishi kerak
      resources:
        requests: {cpu: 250m, memory: 256Mi}
        limits:   {cpu: "1",  memory: 512Mi}
```

Ikkalasi uchun ham sukut qiymati - `NotRequired`. Amalda memory’ni
*kamaytirish* ko’pincha qayta ishga tushirishni talab qiladi (yadro cgroup’ni
ishlatilayotgan hajmdan pastga siqmaydi); CPU o’zgarishlari esa har qanday
runtime’da jonli bo’ladi.

## Resize qilish

Resize oddiy tahrir orqali emas, subresource orqali o’tadi:

```bash
kubectl patch pod app --subresource resize --patch \
  '{"spec":{"containers":[{"name":"app","resources":{"requests":{"cpu":"500m"},"limits":{"cpu":"2"}}}]}}'

kubectl get pod app -o jsonpath='{.spec.containers[0].resources}'     # kutilgan qiymatlar
kubectl get pod app -o jsonpath='{.status.containerStatuses[0].resources}'   # aslida qo'llangani
```

Eski kubectl versiyalari gate yoqilganda buni oddiy `kubectl edit pod` bilan
qilardi; yangilari `--subresource resize` talab qiladi, bu ham tasodifiy
tahrir resize’ni ishga tushirib yuborishini to’xtatadi.

Pod’ning **status**i qanday ketganini aytadi:

| `status.resize` / conditions | Ma’nosi |
|---|---|
| `Proposed` → `InProgress` → (yo’qoladi) | qabul qilindi va qo’llandi |
| `Deferred` | node hozir buni sig’dira olmaydi; resurslar bo’shaganda kubelet qayta urinadi |
| `Infeasible` | node buni **hech qachon** sig’dira olmaydi (node’dagidan ko’proq so’ralgan) - Pod qanday bo’lsa shunday qoladi |

```bash
kubectl get pod app -o jsonpath='{.status.resize}'
kubectl describe pod app | grep -iA2 resize
```

## Bu qayerga tushadi

- **VPA** o’zining yangiroq `InPlaceOrRecreate` yangilash rejimida
  tavsiyalarni imkon boricha Pod’larni qayta ishga tushirmasdan qo’llash uchun
  shundan foydalanadi.
- Deployment shablonining o’zgarishi baribir rollout’ni ishga tushiradi -
  in-place resize **Pod darajasidagi** amaliyot. Deployment uchun uning
  Pod’larini birma-bir resize qilasiz (yoki buni VPA qiladi), yoki rollout’ga
  rozi bo’lasiz.
- Resize’da QoS klassi o’zgarmaydi: `Guaranteed` Pod Guaranteed bo’lib qolishi
  kerak (request’lar limitlarga teng), aks holda resize rad etiladi.

:::exam-tip
2025 yilgi o’quv dasturida bu "borligini va maydonlari nimaligini bilish"
mavzusi. Agar topshiriq ishlab turgan Pod’ning CPU’sini uni qayta
yaratmasdan o’zgartirishni so’rasa, shakli shunday: `resizePolicy`ni
tekshiring, `resize` subresource’iga patch qiling,
`status.containerStatuses[].resources` da tasdiqlang. Agar klasterda bu
funksiya yoqilmagan bo’lsa, halol javob baribir - o’chirib qayta yaratish.
:::

## O’zingizni tekshiring

1. `resizePolicy.restartPolicy: NotRequired` nimani va’da qiladi va bu qaysi
   resurs uchun eng ishonchli tarzda to’g’ri?
2. Resize `Infeasible` ko’rsatyapti. Pod’ning resurslariga nima bo’ldi?
3. Nega Deployment shablonini o’zgartirish in-place resize bor klasterda ham
   Pod’larni rollout qiladi?
