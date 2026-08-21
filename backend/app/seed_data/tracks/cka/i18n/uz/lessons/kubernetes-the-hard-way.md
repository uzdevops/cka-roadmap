## Qolgan hamma narsani ravshan qiladigan qo’llanma

"Kubernetes the Hard Way" - Kelsey Hightower’ning klasterni kubeadm’siz
qurish bo’yicha qo’llanmasi: **hech qanday** o’rnatuvchi ham, distributiv
ham yo’q. Har bir sertifikatni o’zingiz yaratgan CA bilan generatsiya
qilasiz, har bir kubeconfig’ni qo’lda yozasiz, etcd’ni, API serverni,
controller manager va scheduler’ni har bir flagi yozib chiqilgan systemd
xizmatlari sifatida sozlaysiz, worker’larda kubelet’lar va kube-proxy’ni
ko’tarasiz, Pod tarmog’ini route’lar bilan ulaysiz va CoreDNS’ni o’zingiz
deploy qilasiz.

github.com/kelseyhightower/kubernetes-the-hard-way - dastlab GCP uchun
yozilgan edi, hozir bir nechta lokal VM uchun yozilgan va so’nggi Kubernetes
versiyalari bilan yangilanib turadi.

## Nega buni bir marta qilish kerak

kubeadm yashiradigan har bir narsa - imtihon buza oladigan narsa:

| KTHW’da qo’lda qilasiz | Bu qaysi imtihon vazifasini ravshan qiladi |
|---|---|
| CA va har bir komponent sertifikatini `cfssl`/`openssl` bilan, CN va O’ni belgilab generatsiya qilish | nega `CN=system:node:node01, O=system:nodes`; sertifikatni o’qib, u kimga tegishliligini aniqlash |
| `kubelet.kubeconfig`, `kube-proxy.kubeconfig`, `admin.kubeconfig` fayllarini yozish | kubeconfig nimalardan tuzilgani; buzilganini tuzatish |
| `kube-apiserver`’ni 30 ta flag bilan systemd unit sifatida ishga tushirish | har bir `--etcd-*`, `--client-ca-file`, `--service-cluster-ip-range` flagi nima qilishi va xato yozuv nima qilishi |
| etcd’ni `--initial-cluster`, peer va client sertifikatlari bilan sozlash | etcd’ning ikkita porti, ikkita CA’si va backup buyrug’ining flaglari |
| node’lar orasida Pod CIDR’lari uchun statik route’lar yozish | CNI plugini aslida siz uchun nima qilayotgani |
| CoreDNS’ni manifestdan deploy qilish | Corefile va kube-dns Service’i |
| kubelet’larni bootstrap qilish va ularning CSR’larini tasdiqlash | Certificates API, `kubectl certificate approve` |

kubeadm klasteri aynan shuning o’zi: faqat flaglar systemd unit’lari o’rniga
static Pod manifestlarida turadi va sertifikatlar siz uchun generatsiya
qilinadi. Vazifa o’sha flaglardan birini buzganda, ularning hammasini bir
marta o’z qo’li bilan yozgan odam nosozlikni bir necha soniyada ko’radi.

## U siz ishlatadigan narsadan nimasi bilan farq qiladi

| KTHW | kubeadm |
|---|---|
| control plane systemd xizmatlari sifatida | control plane kubelet ostidagi static Pod’lar sifatida |
| sertifikatlar `/var/lib/kubernetes`’da | sertifikatlar `/etc/kubernetes/pki`’da |
| route’lar qo’lda | CNI plugini |
| yangilash yo’li yo’q | `kubeadm upgrade` |

Ya’ni **tushunchalar** bir-biriga to’liq ko’chadi, **yo’llar** esa yo’q.
Imtihon uchun KTHW’ning fayl joylashuvlarini yodlamang; kubeadm’nikini
yodlang.

:::tip
Unga bir kun va uchta VM ajrating. Birinchi marta avtomatlashtirmang - butun
gap flaglarni o’z qo’lingiz bilan yozishda. Ikkinchi marta, agar bo’lsa,
skriptga ruxsat beriladi.
:::

## O’quv dasturi buni qayerga qo’yadi

2025 yilgi CKA o’quv dasturida "Kubernetes klasterini o’rnatish uchun asosiy
infratuzilmani tayyorlash" va "kubeadm yordamida Kubernetes klasterlarini
yaratish va boshqarish" deyilgan - "qo’lda" emas. KTHW - tushunishni qo’lga
kiritish yo’li; keyingi uchta dars va lab esa imtihon baholaydigan kubeadm
ko’nikmasi.

## O’zingizni tekshiring

1. KTHW sizga qo’lda qildiradigan, kubeadm esa siz uchun bajaradigan uchta
   narsani ayting.
2. KTHW klasterida API serverni nima nazorat qiladi, kubeadm klasterida-chi?
3. "kube-apiserver systemd unit’ini qo’lda yozish" sizni qaysi imtihon
   vazifasiga tayyorlaydi?
