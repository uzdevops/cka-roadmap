## Raqamlar qayerdan keladi

Kubernetes metrikalarni saqlamaydi. Qutidan chiqqan holida `kubectl top`
"hozir nima CPU va memory ishlatyapti" degan savolga javob beradi - faqat
hozir - va buning uchun ham unga bitta add-on kerak: **Metrics Server**.

```
kubelet (cAdvisor inside it) ──▶ metrics-server ──▶ API server (metrics.k8s.io) ──▶ kubectl top / HPA
```

- Har bir **kubelet** allaqachon cAdvisor orqali har bir konteyner bo’yicha
  CPU va memory to’playdi va ularni o’z portida beradi.
- **metrics-server** har bir kubelet’ni taxminan har 15 soniyada scrape
  qiladi, oxirgi qiymatlarni xotirada saqlaydi va API server’da agregatsiya
  qilingan API’ni (`metrics.k8s.io`) ro’yxatdan o’tkazadi.
- `kubectl top` va HorizontalPodAutoscaler o’sha API’ni o’qiydi.

Tarix yo’q, dashboard yo’q, ogohlantirish yo’q. Ular uchun Prometheus (yoki
vendor mahsuloti) qo’shasiz - bu CKA doirasidan tashqarida; imtihonning
observability’si - Metrics Server, `kubectl top`, `describe`, event’lar va
loglar.

## Metrics Server’ni o’rnatish

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl get deployment metrics-server -n kube-system
kubectl top nodes          # Pod Ready bo'lgach va bitta scrape o'tgach ishlaydi
```

kind, minikube va ko’plab lab klasterlarida kubelet’lar o’zi imzolagan
sertifikatlarni beradi va Metrics Server ularni scrape qilishdan bosh
tortadi. Odatdagi yechim - uning konteyneriga bitta argument qo’shish:

```bash
kubectl edit deployment metrics-server -n kube-system
# containers[0].args ostiga qo'shing:  - --kubelet-insecure-tls
```

:::exam-tip
`kubectl top` `error: Metrics API not available` qaytarsa, bu Metrics Server
o’rnatilmagan yoki Ready emas degani - `kubectl get pods -n kube-system
| grep metrics`’ni tekshiring. Bu kamdan-kam topshiriqning o’zi bo’ladi; bu
"qaysi Pod eng ko’p CPU ishlatyapti" deb so’raydigan topshiriqni to’sib
turgan narsa.
:::

## U bergan narsadan foydalanish

```bash
kubectl top nodes
# NAME           CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
# controlplane   180m         9%     1204Mi          31%
# node01         42m          2%     612Mi           16%

kubectl top nodes --sort-by=memory
kubectl top pods -A --sort-by=cpu | head
kubectl top pods -n kube-system --containers         # konteyner bo'yicha
kubectl top pod web -l app=web
```

`--sort-by=cpu` / `--sort-by=memory` - imtihon topshiriqlari quriladigan
ikkita flag: "eng ko’p X sarflayotgan node/Pod’ni toping va uning nomini
faylga yozing".

```bash
kubectl top pods -A --sort-by=memory --no-headers | head -1 | awk '{print $2}' > /opt/top-pod.txt
```

## `top` sizga nimani aytmayapti

- Bu **sarf**, request yoki limit emas. Limitining 80 % ida turgan Pod va
  umuman limiti yo’q Pod bir xil ko’rinadi. `kubectl describe node`
  *so’ralgan* tomonni ko’rsatadi - scheduler nuqtai nazaridan node qanchalik
  to’la:

```bash
kubectl describe node node01 | grep -A8 "Allocated resources"
#   Resource           Requests      Limits
#   cpu                1150m (57%)   2 (100%)
#   memory             1.2Gi (31%)   2Gi (52%)
```

- Bu **hozir**. Bir daqiqa oldin OOMKilled bo’lgan Pod hozir juda kichik sarf
  ko’rsatishi mumkin. "Nima bo’lgani" uchun `describe` (Last State, restart
  soni) va event’larni o’qiysiz.

## Observability asboblarining qolgan qismi

| Savol | Asbob |
|---|---|
| bu Pod nega Running emas | `kubectl describe pod` - Events bo’limi |
| bu namespace’da yaqinda nima sodir bo’ldi | `kubectl get events --sort-by=.lastTimestamp` |
| ilova nima dedi | `kubectl logs` (keyingi dars) |
| control plane sog’lommi | `kubectl get --raw /readyz?verbose`, `kubectl get cs` (eskirgan, lekin hali javob beradi) |
| node sog’lommi | `kubectl describe node` - Conditions: MemoryPressure, DiskPressure, PIDPressure, Ready |

:::tip
"Nimadir noto’g’ri, lekin qayerdaligini bilmayman" bo’lganda eng yaxshi
yagona buyruq - `kubectl get events -A --sort-by=.lastTimestamp | tail -20`.
Scheduler, kubelet, image pull va probe’lardan kelgan ogohlantirishlar
hammasi o’sha yerga tushadi.
:::

## O’zingizni tekshiring

1. Node’da konteyner metrikalarini qaysi komponent to’playdi va qaysi biri
   ularni `kubectl top` uchun mavjud qiladi?
2. `kubectl top pods` Metrics API mavjud emas deydi. Nimani tekshirasiz?
3. `kubectl top node` ko’rsatadigan narsa bilan `kubectl describe node`
   Allocated resources ostida ko’rsatadigan narsa orasidagi farq nima?
