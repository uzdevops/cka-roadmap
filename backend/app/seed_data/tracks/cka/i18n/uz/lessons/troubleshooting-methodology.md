## Nosozlikni bartaraf etish - imtihonning uchdan biri

CKA unga 30% og’irlik beradi - boshqa har qanday domendan ko’proq - chunki
ish aynan shundan iborat. Hech kim administratorni Deployment yaratish
uchun yollamaydi; uni kechasi soat 3 dagi chaqiruv uchun yollaydi. Yaxshi
xabar: nosozlikni bartaraf etish - ilhom emas, u tsikl, va bu tsikl har
safar bir xil.

```
  symptom ──▶ WHERE does it live? ──▶ describe ──▶ events ──▶ logs ──▶ exec/ssh ──▶ fix ──▶ VERIFY
                  ▲                                                                         │
                  └──────────────────────── tuzalmadimi? keyingi qatlam ◀───────────────────┘
```

## 0-qadam: nosozlik qayerda yashaydi?

Biror buyruq yozishdan oldin simptomni bitta qatlamga joylang. Har bir
qatlamning o’z birinchi buyrug’i bor va noto’g’ri qatlam ustida ishlash -
bir soat qanday yo’qolishi.

| Simptom | Qatlam | Birinchi buyruq |
|---|---|---|
| ilova xato qaytaradi / noto’g’ri sahifa / o’z DB’siga yeta olmaydi | **ilova** | `kubectl get pods,svc,ep -n <ns>` |
| Pod Running emas, restart’lar, Pending | **Pod / rejalashtirish** | `kubectl describe pod` → Events |
| Pod’lar joyida, Service’ga yetib bo’lmaydi | **tarmoq** | `kubectl get ep <svc>`; selector va label’lar |
| `kubectl` o’zi sekin/xato beradi, hech narsa rejalashtirilmaydi, Deployment’lar masshtablanmaydi | **control plane** | `kubectl get pods -n kube-system`; control-plane node’da `crictl ps` |
| node NotReady, undagi Pod’lar Unknown | **node** | `kubectl describe node`; node’da `systemctl status kubelet` |
| DNS nomlari resolve bo’lmayapti | **klaster DNS** | `kubectl get pods,svc -n kube-system -l k8s-app=kube-dns` |
| volume mount bo’lmaydi, PVC Pending | **storage** | `kubectl describe pvc`; `kubectl get pv,sc` |

Bu haftaning darslari qatlamlarni birma-bir ko’rib chiqadi.

## Tsikl, bitta qatlamdan boshlab

**1. describe** - `kubectl describe <kind> <name>` - eng boy yagona ekran:
spec, status, condition’lar va eng pastda **Events**. Avval Events’ni
o’qing; bu klaster sizga nima qilmoqchi bo’lgani va nega to’xtaganini
aytayotgani.

```bash
kubectl describe pod web-7d9f -n shop | tail -20
kubectl get events -n shop --sort-by=.lastTimestamp | tail -20      # namespace event'lari, eng yangisi oxirida
```

**2. status / condition’lar** - `kubectl get pods`dagi `STATUS` - bu
xulosa; `describe` esa konteynerning **State**, **Last State**,
**Reason**, **Exit Code** qiymatlarini ko’rsatadi. `Exit Code 1` - ilova;
`137` - OOMKilled yoki SIGKILL; `CrashLoopBackOff` u o’lishda davom etyapti
degani - loglarga o’ting.

**3. loglar** - `kubectl logs <pod> [-c container]`; hozirgina qulagan
konteyner uchun `--previous` (joriysida hali chiqish bo’lmasligi mumkin);
kuzatish uchun `-f`; shovqinni kesish uchun `--since=5m`, `--tail=50`.

**4. exec / ssh** - obyekt to’g’ri ko’rinib, xatti-harakat noto’g’ri
bo’lganda: `kubectl exec -it <pod> -- sh` va ichkaridan qarang (env, DNS,
bog’liqlikka curl); Pod qatlami node’ga ishora qilsa `ssh node` va
`journalctl -u kubelet`.

**5. tuzatish** - obyektni (`kubectl edit`), manifestni
(`/etc/kubernetes/manifests`), config faylni, unit’ni tahrirlang; qayta
ishga tushirish kerak bo’lganini qayta ishga tushiring (`systemctl restart
kubelet`; static Pod’lar manifest o’zgarganda o’zi qayta ishga tushadi).

**6. tekshirish** - **odamlar tashlab ketadigan qadam**. Simptomni
ko’rsatgan buyruqni qayta ishga tushiring. Running va Ready bo’lguncha
`kubectl get pods -w`; Service’ga `curl`; Ready bo’lguncha `kubectl get
nodes`. Tekshirilmagan tuzatish - taxmin.

## Behuda izlanishlardan qochish

- **Xatoni to’liq o’qing.** `Back-off pulling image "nginx:1.99"` ichida
  javobning o’zi turibdi. `0/3 nodes are available: 3 node(s) had
  untolerated taint` da ham shunday. Imtihondagi ko’p nosozliklar - bitta
  `describe` da ko’rinib turgan xato yozilgan so’z.
- **Bitta narsani o’zgartiring, keyin tekshiring.** Ikkita o’zgarish va
  bitta tuzatish sizga hech narsa o’rgatmaydi va boshqa narsani buzgan
  bo’lishi mumkin.
- **Ishlayotgani bilan solishtiring.** Qo’shni Pod, boshqa node, sog’lom
  klasterdagi control plane manifesti. `diff` o’qishdan ustun.
- **Vaqt chegarasi qo’ying.** Imtihonda qatlam 3-4 daqiqada hech narsa
  bermasa, savolni belgilang va keyingisiga o’ting. Boshqa joydagi javobsiz
  savollar bundan qimmatroqqa tushadi.
- **Simptomni tuzatmang.** CrashLoopBackOff Pod’ni o’chirish xuddi shunday
  quladigan yangisini yaratadi. Avval sababni loglar/event’lardan toping.
- **Yordam bermaganini orqaga qaytaring.** Taxmin qilib turib qo’shgan
  flag’ingiz - ortda qoldirgan bug’ingiz.

## Bu hafta eng ko’p yozadigan buyruqlaringiz

```bash
kubectl get all -n <ns> -o wide
kubectl describe pod <p> -n <ns>
kubectl logs <p> -n <ns> [-c <c>] [--previous]
kubectl get events -n <ns> --sort-by=.lastTimestamp
kubectl get ep <svc> -n <ns>                     # Service'ning backend'lari bormi?
kubectl get nodes; kubectl describe node <n>
kubectl get pods -n kube-system
ssh <node>; systemctl status kubelet; journalctl -u kubelet -f
crictl ps -a; crictl logs <id>                   # kubectl o'zi ishlamay qolganda
```

:::exam-tip
Imtihondagi nosozlik savollari kontekst almashtirish
(`kubectl config use-context ...`) bilan keladi va ko’pincha `ssh` qilib
kirishingiz kerak bo’lgan node bilan. Ikkalasini ham boshida bajaring va
keyingi savoldan oldin asosiy node’ga `exit` qiling - noto’g’ri node yoki
klasterda yozilgan buyruqlar imtihondagi eng qimmat xato.
:::

## O’zingizni tekshiring

1. Biror buyruq yozishdan oldin hal qilinadigan birinchi narsa nima va
   nega?
2. Tsiklning oltita qadamini va eng ko’p tashlab ketiladiganini ayting.
3. Pod CrashLoopBackOff’da. Nega uni o’chirish yechim emas va keyingi
   buyruq qaysi?
