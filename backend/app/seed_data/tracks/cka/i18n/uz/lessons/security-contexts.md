## Pod spec ichidagi Docker tugmachalari

Oldingi darsdagi hamma narsa - qaysi foydalanuvchi, qaysi capability’lar,
privileged yoki yo’q - `securityContext` ostida yashaydi. U **ikki darajada**
mavjud va to’g’ri tushunib olish kerak bo’lgan qism ham aynan shu:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ubuntu-sleeper
spec:
  securityContext:                 # POD darajasi: har bir konteynerga va volume larga tegishli
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000                  # mount qilingan volume larning guruh egaligi
  containers:
    - name: ubuntu
      image: ubuntu
      command: ["sleep", "3600"]
      securityContext:             # KONTEYNER darajasi: bu konteyner uchun Pod darajasini bekor qiladi
        runAsUser: 1010
        capabilities:              # capability lar FAQAT konteyner darajasida bor
          add: ["SYS_TIME", "NET_ADMIN"]
          drop: ["ALL"]
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        privileged: false
```

| Maydon | Pod darajasi | Konteyner darajasi |
|---|---|---|
| `runAsUser`, `runAsGroup`, `runAsNonRoot` | ha | ha (ustun keladi) |
| `fsGroup`, `supplementalGroups`, `seccompProfile`, `sysctls` | ha | (seccomp konteyner bo’yicha ham) |
| `capabilities` | **yo’q** | ha |
| `privileged`, `allowPrivilegeEscalation`, `readOnlyRootFilesystem` | **yo’q** | ha |

Konteyner darajasidagi sozlamalar o’sha konteyner uchun Pod darajasidagilarni
bekor qiladi. Imtihonda keng tarqalgan xato - `capabilities`ni Pod’ning
`securityContext`i ostiga qo’yish; u yerda bunday maydon umuman mavjud emas
va API server buni aytadi.

```bash
kubectl explain pod.spec.securityContext --recursive
kubectl explain pod.spec.containers.securityContext --recursive
```

## Siz ishlatadigan maydonlar

```yaml
securityContext:
  runAsUser: 1010               # jarayon ishlaydigan UID
  runAsNonRoot: true            # agar image root sifatida ishlasa, ishga tushmasin
  capabilities:
    add: ["NET_ADMIN"]
    drop: ["ALL"]               # keyin faqat kerakligini qaytarib qo'shing
  privileged: true              # hamma narsa - faqat CNI/storage plaginlar uchun
  allowPrivilegeEscalation: false   # setuid binarlar root ololmasin
  readOnlyRootFilesystem: true      # yozishi kerak bo'lgan narsalarga emptyDir mount qiling
```

```bash
kubectl exec ubuntu-sleeper -- whoami            # root? yoki 1010?
kubectl exec ubuntu-sleeper -- id
kubectl exec ubuntu-sleeper -- date -s "19 APR 2012 11:14:00"   # faqat SYS_TIME bilan ishlaydi
kubectl get pod ubuntu-sleeper -o jsonpath='{.spec.containers[0].securityContext}'
```

:::exam-tip
`securityContext` ishlab turgan Pod’da o’zgarmas. Ketma-ketlik: `kubectl get
pod X -o yaml > x.yaml`, tahrirlash, `kubectl replace --force -f x.yaml`.
Darajani tekshiring: foydalanuvchi → ikkala daraja ham; capability’lar →
konteyner darajasi, konteyner ostida, Pod ostida emas. Keyin buni isbotlash
uchun `kubectl exec X -- whoami`.
:::

## Nega bu muhim, ikki qatorda

Web server root bo’lishi shart emas va unga `SYS_ADMIN` ham kerak emas. Agar
u buzib kirilsa, `runAsNonRoot` va tashlab yuborilgan capability’lar va faqat
o’qish uchun root fayl tizimi "hujumchi node’ni egalladi" ni "hujumchi yoza
olmaydigan, imtiyozini oshira olmaydigan va 1024 dan pastga bog’lana
olmaydigan jarayonni egalladi" ga aylantiradi.

## Pod Security admission: klaster buni majburlaydi

Buni har bir Pod uchun abadiy qo’lda yozishingiz mumkin yoki klasterga
standartga javob bermaydigan Pod’larni **rad etish**ni aytishingiz mumkin.
O’rnatilgan `PodSecurity` admission plagini har bir namespace uchun uchta
profildan birini label’lar orqali qo’llaydi:

```bash
kubectl label namespace dev pod-security.kubernetes.io/enforce=restricted
kubectl label namespace dev pod-security.kubernetes.io/warn=restricted
```

| Profil | Nimaga ruxsat beradi |
|---|---|
| `privileged` | hamma narsaga |
| `baseline` | privileged yo’q, hostPath/hostNetwork/hostPID yo’q, cheklangan capability’lar |
| `restricted` | baseline va ustiga: non-root sifatida ishlashi, ALL capability’larni tashlashi, seccomp o’rnatilgani, imtiyoz oshirish yo’qligi shart |

`enforce` rad etadi, `warn` ogohlantirish chiqaradi, `audit` logga yozadi.
`restricted`dan o’tmagan Pod o’ziga kerak bo’lgan har bir maydonni sanab
o’tgan xabar bilan rad etiladi - `allowPrivilegeEscalation != false`,
`unrestricted capabilities`, `runAsNonRoot
!= true` - bu esa moslashgan spec yozish uchun qulay tekshiruv ro’yxati ham.

:::tip
`restricted` ko’plab image’larni sindiradigan darajada qattiq (root talab
qiladigan har qanday narsani). Namespace’da `warn=restricted` dan boshlang,
bir kun ogohlantirishlarni o’qing, keyin majburlang.
:::

## O’zingizni tekshiring

1. `runAsUser` Pod va konteyner darajasida turli qiymatlar bilan berilgan -
   o’sha konteyner uchun qaysi biri ustun keladi?
2. `capabilities`ni qayerda o’rnatish mumkin va uni boshqa darajaga qo’ysangiz
   qanday xato chiqadi?
3. Namespace’ga `pod-security.kubernetes.io/enforce=restricted` label’ini
   qo’yish root sifatida ishlaydigan Pod’ga nima qiladi?
