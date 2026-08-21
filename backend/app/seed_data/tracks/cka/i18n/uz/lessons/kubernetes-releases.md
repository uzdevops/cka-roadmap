## Versiya raqamini o’qish

```
v1.30.2
 │  │ └── patch: xato va xavfsizlik tuzatishlari, yangi imkoniyat yo'q
 │  └──── minor: yiliga taxminan uch marta chiqadigan reliz - imkoniyatlar, deprecation'lar, API o'zgarishlari
 └─────── major: 2015 yildan beri 1 bo'lib kelmoqda
```

```bash
kubectl version            # klient va server
kubectl get nodes          # har bir node'dagi kubelet versiyasi, VERSION ustunida
kubeadm version
```

Har bir control plane komponenti - `kube-apiserver`, `kube-controller-manager`,
`kube-scheduler`, `kubelet`, `kube-proxy`, `kubectl` - bitta relizdan bir xil
versiyada chiqadi. etcd va CoreDNS o’z versiya raqamlariga ega; kubeadm har bir
Kubernetes relizi bilan qaysilarini deploy qilishini qat’iy belgilab qo’yadi.

## Minor qancha vaqt qo’llab-quvvatlanadi

Eng so’nggi uchta minor patch relizlarini oladi (har bir minor uchun taxminan
**14 oy** qo’llab-quvvatlash). Bundan eskisini ishlatsangiz, xavfsizlik
patch’lari bo’lmaydi - shuning uchun "bir necha oyda bir marta, bittadan minor
yangilash" - klasterni qo’llab-quvvatlanadigan chiziqda ushlab turish uchun
kerak bo’lgan ritm.

## Version skew: kim kimdan yangiroq bo’lishi mumkin

Hamma narsa bir vaqtning o’zida bir xil versiyada bo’lishi shart emas - agar
shart bo’lganida, yangilashning imkoni bo’lmasdi. Qoidalar:

| Komponent | Qanday bo’lishi mumkin | kube-apiserver’ga nisbatan |
|---|---|---|
| **kube-apiserver** (HA’da bir nechta) | n, n-1 | eng yangi API server n ni belgilaydi |
| **kubelet** | n ... n-3 | hech qachon API serverdan yangi emas |
| **kube-proxy** | n ... n-3 | kubelet bilan bir xil |
| **kube-controller-manager, kube-scheduler** | n, n-1 | hech qachon yangi emas |
| **kubectl** | n+1, n, n-1 | har ikki tomonga bitta minor |

So’z bilan aytganda: API server birinchi boradi, qolgan hammasi ergashadi,
lekin orqada qolishi mumkin. Kubelet uchta minorgacha orqada bo’lishi mumkin -
aynan shu narsa control plane’ni yangilab, keyin xohlasangiz worker’larni
kunlar davomida bittalab yangilashga imkon beradi.

:::exam-tip
Bosim ostida esda tutish kerak bo’lgan ikkita raqam: yangilashning o’zi uchun
**bir vaqtda bitta minor** (1.29 → 1.30 → 1.31, hech qachon 1.29 → 1.31) va
**avval API server**. Keyingi darslardagi hamma narsa shu ikkitasidan kelib
chiqadi.
:::

## Binary’lar qayerdan keladi

| | |
|---|---|
| Manba kodi va reliz eslatmalari | github.com/kubernetes/kubernetes/releases |
| kubeadm, kubelet, kubectl paketlari | `pkgs.k8s.io` apt/yum repozitoriylari, **har bir minor uchun** bitta repo (`/v1.30/`) |
| Control plane uchun konteyner image’lari | `registry.k8s.io/kube-apiserver:v1.30.2` va hokazo |

```bash
apt-cache madison kubeadm | head -5       # sozlangan repo qaysi versiyalarni taklif qiladi
```

O’sha "har bir minor uchun bitta repo" nuqtasi muhim: 1.30 dan 1.31 ga
yangilash uchun avval paket repozitoriysini `/v1.31/`’ga yo’naltirasiz, keyin
`apt-get update` qilasiz va faqat shundan keyin `kubeadm=1.31.x` o’rnatsa
bo’ladigan holga keladi. Repo almashtirishni unutish - "yangi versiya mavjud
emas" degan holatning eng keng tarqalgan sababi.

## Deprecation’lar

Minor reliz API versiyasini deprecate qilishi, keyingisi esa uni olib tashlashi
mumkin (`extensions/v1beta1` Ingress, `PodSecurityPolicy`, `batch/v1beta1`
CronJob). Olib tashlangan versiyadan foydalanadigan manifestlar yangilashdan
keyin apply bo’lmaydi. Nima ketayotganini `kubectl api-resources` va reliz
eslatmalari aytadi; `kubectl convert` plugini eski manifestlarni qayta yozadi.
Minor yangilashdan oldin manifestlaringizni reliz eslatmalarida nomlangan
versiyalar bo’yicha bir marta qidirib chiqishga arziydi.

## O’zingizni tekshiring

1. Patch relizda nima o’zgaradi va minorda nima o’zgarishi mumkin?
2. API server 1.30 da. Klasterda ruxsat etilgan eng eski kubelet versiyasi
   qaysi?
3. Siz 1.29 dan 1.31 ga o’tmoqchisiz. Bu nechta yangilash va paketlar topilishi
   uchun har biridan oldin nimani o’zgartirasiz?
