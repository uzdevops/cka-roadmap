## etcd oldidagi so’nggi darvoza

API serverga yetib kelgan so’rov avval autentifikatsiyadan (siz kimsiz), keyin
avtorizatsiyadan (sizga ruxsat bormi) o’tadi va shundan so’ng **admission**’ga
tushadi: obyekt validatsiya qilinib saqlanishidan oldin pluginlar zanjiri unga
qaraydi va uni yo o’zgartiradi, yo rad etadi. Avtorizatsiya "bu foydalanuvchi
Pod yarata oladimi" degan savolga javob beradi; admission esa "aynan *shu*
Pod, yozilgan holida, mavjud bo’la oladimi" degan savolga - va u "ha, lekin
mana bu o’zgarishlar bilan" deya oladi.

```
so'rov ─▶ authN ─▶ authZ ─▶ mutating admission ─▶ sxema validatsiyasi ─▶ validating admission ─▶ etcd
```

Ikki xil plugin, shu tartibda ishlaydi:

- **Mutating** pluginlar obyektni o’zgartira oladi - sukut qiymat qo’shadi,
  sidecar kiritadi, maydon o’rnatadi.
- **Validating** pluginlar esa faqat qabul qiladi yoki rad etadi.

Ba’zi o’rnatilgan pluginlar ikkalasini ham qiladi.

## Siz uchratadigan o’rnatilgan pluginlar

| Plugin | Nima qiladi |
|---|---|
| `NamespaceLifecycle` | mavjud bo’lmagan yoki o’chirilayotgan namespace’dagi obyektlarni rad etadi (sukut bo’yicha yoqilgan - `kubectl run x -n nope` shuning uchun ishlamaydi) |
| `LimitRanger` | LimitRange sukut qiymatlari va chegaralarini qo’llaydi |
| `ResourceQuota` | ResourceQuota’larni majburlaydi |
| `ServiceAccount` | sukut service account va uning token’ini Pod’larga kiritadi |
| `DefaultStorageClass` | class’i ko’rsatilmagan PVC’ga sukut class’ni beradi |
| `NodeRestriction` | kubelet’ning boshqa node’lar obyektlarini o’zgartirishiga yo’l qo’ymaydi - kubeadm’da sukut bo’yicha yoqilgan |
| `NamespaceAutoProvision` | hali mavjud bo’lmagan namespace’ni rad etish o’rniga yaratadi (sukut bo’yicha o’chiq) |
| `AlwaysPullImages` | `imagePullPolicy: Always`ni majburlaydi |
| `MutatingAdmissionWebhook` / `ValidatingAdmissionWebhook` | o’zingizning webhook’laringizga murojaat qiladi - keyingi dars |

```bash
kube-apiserver -h | grep enable-admission-plugins    # yordam matnidagi sukut ro'yxati
```

## Pluginlarni yoqish va o’chirish

Admission pluginlar - bu **API serverdagi flaglar**:

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
- --enable-admission-plugins=NodeRestriction,NamespaceAutoProvision
- --disable-admission-plugins=DefaultStorageClass
```

`--enable-admission-plugins` sukut to’plamiga *qo’shadi*, uni almashtirmaydi.
Manifestni saqlang, kubelet API serverni qayta ishga tushirishini kuting va
tasdiqlang:

```bash
ps -ef | grep kube-apiserver | grep -o -- '--enable-admission-plugins=[^ ]*'
kubectl exec -n kube-system kube-apiserver-controlplane -- kube-apiserver -h | grep enable-admission-plugins
```

:::exam-tip
API server manifestini tahrirlash - API server qayta ishga tushadigan 20-40
soniya davomida kubectl **ishlamaydi** degani. Vahimaga tushmang, qayta
tahrirlamang; kuting. Agar u qaytib kelmasa, node’da
`crictl ps -a | grep apiserver` va `crictl logs` - plugin nomidagi xato
(klassik holat - ortiqcha -ing bilan yozilgan `NamespaceAutoProvisioning`)
o’sha yerda ko’rsatiladi.
:::

## Admission’ni amalda ko’rish

```bash
# NamespaceLifecycle (sukut bo'yicha)
kubectl run nginx --image=nginx -n blue
# Error: namespaces "blue" not found

# NamespaceAutoProvision yoqiladi, keyin:
kubectl run nginx --image=nginx -n blue       # ishlaydi
kubectl get ns blue                           # u siz uchun yaratildi

# DefaultStorageClass o'chiriladi, keyin storageClassName'siz yangi PVC:
kubectl get pvc                               # STORAGECLASS ustuni bo'sh, Pending bo'lib qoladi
```

## Admission nima uchun emas

U *kim* nima qila olishini hal qilmaydi - bu RBAC ishi. RBAC rad etgan
foydalanuvchi admission’ga umuman yetib bormaydi; RBAC’dan o’tgan
foydalanuvchini esa validating plugin u *nima* yuborganiga qarab baribir rad
etishi mumkin. Topshiriqda "X foydalanuvchi Pod yarata oladi, lekin privileged
Pod’larni emas" deyilganda bu ikki g’oyani ajratib turing - birinchi yarmi
RBAC, ikkinchisi admission (namespace’dagi Pod Security admission darajasi
yoki validating webhook).

:::note
Pod Security Admission - PodSecurityPolicy’ning o’rnatilgan o’rinbosari - o’zi
ham admission plugin (`PodSecurity`) bo’lib, har bir namespace uchun
`pod-security.kubernetes.io/enforce: restricted` kabi label’lar bilan
sozlanadi. U sukut bo’yicha yoqilgan va "bu namespace’da privileged Pod
bo’lmasin" degan talabga zamonaviy javob.
:::

## O’zingizni tekshiring

1. So’rov quvurida admission avtorizatsiyadan oldin ishlaydimi yoki keyin va
   nega bu tartib muhim?
2. `NamespaceAutoProvision`ni qanday yoqasiz va buni qilayotganingizda
   kubectl’ga nima bo’ladi?
3. Sukut klasterda `kubectl run x --image=nginx -n doesnotexist` ishlamaydi.
   Uni qaysi plugin rad etdi?
