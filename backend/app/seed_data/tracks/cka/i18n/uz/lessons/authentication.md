## Foydalanuvchilar obyekt emas

Kubernetes’da **User obyekti yo’q**. `kubectl create user` degan narsa yo’q.
"Foydalanuvchi" - bu shunchaki so’rovga bog’lanib keladigan nom bo’lib, uni
API server sozlangan autentifikatorlardan biri isbotlaydi.
ServiceAccount’lar esa, aksincha, *obyekt* - ular Pod’lar uchun shaxslar va
keyingi darslar ularga alohida to’xtaladi.

```
so'rov ──▶ [autentifikator 1] ──▶ [autentifikator 2] ──▶ ... ──▶ shaxs (user, guruhlar) yoki 401
```

API server yoqilgan har bir autentifikatorni navbat bilan sinaydi; birinchi
muvaffaqiyatlisi shaxsni belgilaydi. Hech biri muvaffaqiyat qozonmasa →
`401 Unauthorized` (bu har qanday avtorizatsiyadan oldin sodir bo’ladi - 401
"sen kimsan", 403 esa "senga mumkin emas").

## Autentifikatorlar

| Usul | Qanday | Nima uchun |
|---|---|---|
| **X.509 client sertifikatlari** | klaster CA’si imzolagan sertifikat; CN = user, O = groups | adminlar, komponentlar (kubelet, scheduler...) - kubeadm’ning sukut varianti |
| **ServiceAccount token’lari** | API server ServiceAccount uchun beradigan JWT’lar | Pod’lar |
| **OIDC** | identity provider’dan (Keycloak, Google, Entra) olingan token’lar | haqiqiy tashkilotlardagi odamlar |
| **Webhook token** | bearer token yaroqlimi yoki yo’qmi, tashqi xizmatdan so’rash | maxsus integratsiyalar |
| **Bootstrap token’lar** | `kubeadm join` uchun qisqa muddatli token’lar | node qo’shish |
| Statik token fayli / statik parol fayli | `--token-auth-file` | eski; basic auth **olib tashlangan** |

Statik fayllar haqida ikki og’iz so’z kerak, chunki eski materiallar hamon
ularni ko’rsatadi: API serverga `--token-auth-file` bilan beriladigan
`token,user,uid,"group1,group2"` ko’rinishidagi CSV. U ishlaydi, u xavfsiz
emas (ochiq matn, rotatsiya yo’q, o’zgartirish uchun API serverni qayta ishga
tushirish kerak) va bu siz ustiga qurishingiz kerak bo’lgan narsa emas.

## Sertifikat siz haqingizda nima deydi

```bash
openssl x509 -in /etc/kubernetes/pki/apiserver-kubelet-client.crt -noout -subject
# subject=O = kubeadm:cluster-admins, CN = kube-apiserver-kubelet-client
openssl x509 -in admin.crt -noout -subject
# subject=O = system:masters, CN = kubernetes-admin
```

- **CN** (Common Name) → foydalanuvchi nomi.
- **O** (Organization, takrorlanishi mumkin) → guruhlar.

`system:masters` - har qanday RBAC tekshiruvidan o’tkazib yuboradigan guruh;
kubeadm yozadigan admin kubeconfig’ida aynan u bor, shuning uchun ham o’sha
kubeconfig butun podshohlikning kaliti. Sertifikatlar darslari haqiqiy
foydalanuvchi uchun mantiqiy guruh bilan sertifikat berishni ko’rsatadi.

## kubectl o’z shaxsini qayerda saqlaydi

```bash
kubectl config view --minify --raw | grep -A3 "user:"
#   client-certificate-data: LS0t...   (yoki client-certificate: /path)
#   client-key-data: LS0t...
# yoki
#   token: eyJhbGciOi...
```

kubeconfig yozuvi - isbot; sertifikat isbotlarini tekshiradigan narsa esa API
serverning `--client-ca-file`i. Agar ular mos kelmasa,
`x509: certificate signed by unknown authority` olasiz - bu TLS kiyimidagi
401.

:::exam-tip
Topshiriqdagi "foydalanuvchi yarating" degani: unga kalit va CSR generatsiya
qilish, uni klasterga imzolatish (CertificateSigningRequest, keyingisidan
keyingi dars), sertifikatni kubeconfig’ga qo’yish va RBAC berish. To’rt qadam,
User obyektisiz. Agar topshiriq sizga token bersa, kubeconfig tomoni -
`kubectl config set-credentials <name> --token=...`.
:::

## Sizsiz ham mavjud bo’lgan guruhlar

| Guruh | Kim |
|---|---|
| `system:authenticated` | autentifikatsiyadan o’tgan har bir so’rov |
| `system:unauthenticated` | anonim so’rovlar (agar umuman ruxsat berilgan bo’lsa) |
| `system:masters` | klaster superuser’lari - RBAC’ni chetlab o’tadi |
| `system:serviceaccounts` / `system:serviceaccounts:<ns>` | barcha ServiceAccount’lar / namespace’dagilari |
| `system:nodes` | kubelet’lar (CN `system:node:<name>`) |

Bular RBAC uchun muhim: ClusterRole’ni `system:authenticated`’ga bog’lash uni
*yaroqli hisob ma’lumotiga ega har bir kishiga* beradi - bu kamdan-kam siz
nazarda tutgan narsa bo’ladi.

## O’zingizni tekshiring

1. So’rov 401 oldi. Avtorizatsiya ishladimi? 401 nimani, 403 esa nimani
   anglatadi?
2. Client sertifikatida qaysi maydonlar foydalanuvchi nomi va guruhlarga
   aylanadi?
3. Nega Role’ni `system:authenticated`’ga bog’lash xavfli?
