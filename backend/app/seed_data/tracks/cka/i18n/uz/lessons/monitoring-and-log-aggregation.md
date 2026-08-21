## Konteyner loglari qayerdan keladi

Konteynerning stdout va stderr’ini konteyner runtime tutib oladi va node’dagi
faylga yozadi - containerd bilan `/var/log/pods/<namespace>_<pod>_<uid>/<container>/0.log`.
API server so’raganda kubelet o’sha faylni o’qiydi, `kubectl logs` esa - API
server’ning so’rashi. Hech narsa agregatsiya qilinmaydi, hech qayerga
jo’natilmaydi va node saqlaganidan uzoqroq turmaydi; node’dagi log rotation
qanchalik orqaga qaray olishingizni belgilaydi.

```
container stdout/stderr ──▶ containerd ──▶ /var/log/pods/.../0.log ──▶ kubelet ──▶ API server ──▶ kubectl logs
```

O’zlashtirib olish kerak bo’lgan ikkita oqibat:

- Konteyner ichida **faylga** yozadigan ilova `kubectl logs` chiqishini
  umuman bermaydi. Yechim - stdout’ga yozish yoki faylni tail qiladigan
  sidecar qo’shish (ko’p konteynerli Pod darsi).
- Pod **o’chirilganda**, Kubernetes nuqtai nazaridan uning loglari yo’qoladi.
  Keyinroq kerak bo’ladigan hamma narsa qayergadir jo’natilishi kerak -
  Elasticsearch yoki Loki bilan ishlaydigan Fluentd/Fluent Bit DaemonSet’lari
  shuning uchun, va bu imtihondan tashqarida.

## Buyruq va uning flag’lari

```bash
kubectl logs web                          # bitta konteynerli Pod: butun log
kubectl logs web -c sidecar               # aniq bir konteyner
kubectl logs web --all-containers         # har bir konteyner, prefiks bilan
kubectl logs web -f                       # kuzatib turish
kubectl logs web --tail=50
kubectl logs web --since=10m              # yoki --since-time=2026-08-20T10:00:00Z
kubectl logs web --timestamps
kubectl logs web --previous               # OLDINGI nusxa, crash/restart dan keyin
kubectl logs -l app=web                   # label li har bir Pod (--prefix bo'lmasa bittalab)
kubectl logs -l app=web --prefix --tail=20
kubectl logs deployment/web               # Deployment ning bir Pod i (bittasini tanlaydi)
kubectl logs job/backup
```

:::exam-tip
`--previous` - "nega crash bo’ldi" degan savolga javob beradigan flag.
`CrashLoopBackOff` dagi konteyner har bir necha soniyada qayta ishga tushadi;
uning *joriy* logi - yangi startning birinchi qatorlari, uni o’ldirgan xato
esa *oldingi* nusxaning logida. Har doim avval `kubectl logs <pod>
--previous`.
:::

```bash
kubectl logs webapp-2 -c simple-webapp | grep -i "warning\|error"
kubectl logs webapp-1 | grep -i "login failed"
```

Bu yerdagi imtihon topshiriqlarining ko’pi - grep masalalari: foydalanuvchini,
xatoni, kerakli qatorni toping. Log katta bo’lsa, `--tail` va `--since` bilan
birlashtiring.

## kubectl logs hech narsa bermaganda

| Alomat | Sababi | Harakat |
|---|---|---|
| chiqish bo’sh, ilova ishlayapti | ilova stdout’ga emas, faylga yozadi | `kubectl exec <pod> -- cat /var/log/app.log`, sidecar qo’shing |
| `Error from server: ... container "x" in pod is waiting to start` | konteyner umuman ishga tushmagan (image pull, init konteyner) | `kubectl describe pod` - Events |
| `a container name must be specified` | ko’p konteynerli Pod | `-c <name>` yoki `--all-containers` |
| `error dialing backend` / timeout | API server node’dagi kubelet’ga 10250 portida yeta olmayapti | kubelet o’chgan, firewall, noto’g’ri `--kubelet-client-*` sertifikatlar |

Node’ning o’zida, API server’ni chetlab o’tib:

```bash
crictl ps -a                      # konteyner id sini toping
crictl logs <id> --tail 50
ls /var/log/pods/                 # xom fayllar
journalctl -u kubelet             # kubelet'ning o'z logi - konteyner emas
```

Control plane komponentlari - static Pod’lar, shuning uchun API server ishlab
turganda `kubectl logs kube-apiserver-controlplane -n kube-system` ishlaydi -
u ishlamayotganda esa node’da `crictl logs`.

## Event’lar ham log

```bash
kubectl get events -n payroll --sort-by=.lastTimestamp
kubectl get events --field-selector type=Warning -A
kubectl describe pod web | tail -15
```

Event’lar - obyekt haqidagi *klasterning* logi: scheduled, pulled, started,
probe failed, OOMKilled, evicted. Sukut bo’yicha ular bir soatdan keyin
yo’qoladi, shuning uchun ular turganida o’qing.

:::tip
`kubectl logs` `--since` va `--tail` ni birga qabul qiladi; `--since=1h
--tail=100` "oxirgi soatdagi oxirgi yuz qator" degani, ko’p gapiradigan
konteynerda sizga deyarli har doim aynan shu ko’rinish kerak.
:::

## O’zingizni tekshiring

1. Konteyner `CrashLoopBackOff` da. Uni o’ldirayotgan xatoni aynan qaysi
   buyruq ko’rsatadi?
2. Ilova o’z logini konteyner ichidagi `/var/log/app.log` ga yozadi.
   `kubectl logs` nima ko’rsatadi va sizda qanday ikkita variant bor?
3. API server ishlamayapti. API server’ning o’z logini qanday o’qiysiz?
