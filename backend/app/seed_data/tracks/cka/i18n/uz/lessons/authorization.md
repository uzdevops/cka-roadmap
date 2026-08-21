## Shaxs tasdiqlandi, endi u nima qila oladi

Autentifikatsiya so’rovni *kim* yuborganini aniqladi. Avtorizatsiya esa
**o’sha shaxs shu resurs ustida shu verb’ni bajara oladimi** degan qarorni
qabul qiladi. U har bir so’rovda ishlaydi, API serverda sozlanadi va eng kam
imtiyoz tamoyili aynan shu yerda amalga oshiriladi yoki oshirilmaydi.

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
- --authorization-mode=Node,RBAC
```

Bu flag - **ro’yxat**; rejimlar tartib bo’yicha sinaladi va birinchi bo’lib
ruxsat yoki rad javobini qaytargani g’olib bo’ladi. Hech biri qaror qilmasa,
so’rov rad etiladi.

| Rejim | Nima asosida qaror qiladi | Nima uchun |
|---|---|---|
| `Node` | so’rov yuboruvchining kubelet ekani (`system:nodes` guruhi) va obyekt *o’sha* node’ga tegishli ekani | kubelet’larga o’z Pod/Secret/ConfigMap’larini o’qish va o’z Node status’ini yozish ruxsatini berish - boshqa hech narsaga emas |
| `RBAC` | foydalanuvchilar, guruhlar va ServiceAccount’larga bog’langan Role/ClusterRole’lar | o’zingiz sozlaydigan hamma narsa |
| `ABAC` | API serverdagi JSON siyosat fayli (`--authorization-policy-file`) | eski uslub; har bir o’zgarish uchun API serverni qayta ishga tushirish kerak |
| `Webhook` | tashqi HTTP xizmat (`--authorization-webhook-config-file`) | tashqi siyosat dvigatelini integratsiya qilish |
| `AlwaysAllow` | - | xavfsizligi yo’q klaster; hech narsa qo’ymasangiz sukut qiymati |
| `AlwaysDeny` | - | sinov |

`Node,RBAC` - kubeadm’ning sukut qiymati va yodda tutish kerak bo’lgani:
avval Node authorizer (u faqat kubelet’lar uchun javob beradi), qolgan hamma
uchun RBAC.

## RBAC bitta abzatsda

**Role** - bu qoidalar ro’yxati - API guruhlaridagi resurslar ustidagi
verb’lar - va u bitta namespace bilan chegaralangan; **ClusterRole** xuddi
shu narsa, faqat namespace chegarasisiz (yoki node kabi klaster darajasidagi
resurslar uchun). **RoleBinding** Role’ni *yoki ClusterRole’ni* namespace
ichidagi subyektlarga biriktiradi; **ClusterRoleBinding** ClusterRole’ni
butun klaster bo’ylab subyektlarga biriktiradi. Subyektlar - foydalanuvchilar,
guruhlar yoki ServiceAccount’lar. Rad etish qoidasi yo’q: berilmagan narsa
taqiqlangan. Keyingi ikki dars - shuning amaliyoti.

## Serverdan so’rash

```bash
kubectl auth can-i create deployments                        # o'zim sifatida, joriy namespace'da
kubectl auth can-i delete nodes                              # klaster darajasida
kubectl auth can-i list pods --as dev-user -n dev            # impersonatsiya (impersonate ruxsati kerak; adminlarda bor)
kubectl auth can-i get pods/log --as system:serviceaccount:dev:builder
kubectl auth can-i --list --as dev-user -n dev               # u qila oladigan hamma narsa
kubectl auth whoami                                          # server sizni qanday ko'radi
```

`can-i` - RBAC o’zgarishini sinashning eng tez yo’li va 403 obyekt nomidagi
xato emas, ruxsat muammosi ekanini o’zingizga isbotlash usuli.

## Rad etish qanday ko’rinadi

```
Error from server (Forbidden): pods is forbidden: User "dev-user" cannot list resource "pods" in API group "" in the namespace "dev"
```

Bu xabar - matn ko’rinishidagi to’liq RBAC qoidasi: **foydalanuvchi**,
**verb**, **resurs**, **API guruh**, **namespace**. Aynan shuni beradigan Role
yozing va uni bog’lang. `403 Forbidden` = avtorizatsiya yo’q dedi;
`401 Unauthorized` = autentifikatsiya ishlamadi - boshqa qatlam, boshqa yechim.

:::exam-tip
Forbidden xabarini *so’zma-so’z* o’qing va uni Role’ga ko’chiring: resurs
`pods` → `resources: ["pods"]`; API guruh `""` → `apiGroups: [""]`; verb
`list` → `verbs: ["list"]`; namespace `dev` → Role ham, RoleBinding ham
`dev`da bo’ladi. Keyin tasdiqlash uchun `auth can-i`. To’qson soniya.
:::

## Node authorizer, qisqacha

kubelet `system:nodes` guruhidagi `system:node:node01` sifatida
autentifikatsiyadan o’tadi. Node authorizer unga node01’ga joylashtirilgan
Pod’larni, o’sha Pod’lar mount qiladigan Secret va ConfigMap’larni o’qishga
va node01 status’ini yangilashga ruxsat beradi - node02 uchun esa xuddi shu
narsalarni rad etadi. `NodeRestriction` admission plugini bilan birga (u
kubelet’ning boshqa node’larga label qo’yishiga yo’l qo’ymaydi), buzib
kirilgan node buzib kirilgan klaster emas, buzib kirilgan node bo’lib qoladi.
Buni siz sozlamaysiz; kubelet’larga nega ClusterRoleBinding kerak emasligini
bilishingiz kerak.

## O’zingizni tekshiring

1. `--authorization-mode=Node,RBAC` tartib bo’yicha nimani anglatadi?
2. Buni Role’ga aylantiring: `User "ana" cannot create resource "deployments"
   in API group "apps" in the namespace "web"`.
3. Qaysi buyruq hisob ma’lumotlarini almashtirmasdan ServiceAccount berilgan
   namespace’da Pod loglarini o’qiy oladimi yoki yo’qmi degan savolga javob
   beradi?
