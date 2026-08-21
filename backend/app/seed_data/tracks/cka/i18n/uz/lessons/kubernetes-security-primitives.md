## Muammoning shakli

Klasterdagi hamma narsa API server orqali o’tadi, shuning uchun klasterni
himoyalash API server haqidagi ikki savol bilan boshlanadi va workload’lar
haqidagi uchinchi savol bilan tugaydi:

1. **API serverga kim yeta oladi?** - autentifikatsiya
2. **U yerga yetgach nima qilishi mumkin?** - avtorizatsiya (va admission)
3. **Workload’lar bir-biriga va node’larga nima qila oladi?** - network
   policy’lar, security context’lar, Pod Security

Va bularning barchasi ostidagi narsa: har bir komponent boshqasi bilan
**TLS** orqali, klaster CA’si imzolagan sertifikatlar bilan gaplashadi. Bu
bosqich ularni tartib bilan oladi: avval TLS va sertifikatlar, keyin
autentifikatsiya va avtorizatsiya, keyin workload darajasidagi nazoratlar.

## API serverga kim yetadi

| Chaqiruvchi | Shaxsini nima bilan isbotlaydi |
|---|---|
| administratorlar, dasturchilar | client sertifikatlari yoki identity provider’dan olingan token’lar |
| kubelet’lar, scheduler, controller manager | kubeconfig’laridagi client sertifikatlari |
| Pod’lar | ServiceAccount token’lari |
| tashqi tizimlar (CI, dashboard’lar) | ServiceAccount token’lari yoki OIDC |

API server deyarli hamma narsa uchun anonim so’rovlarni rad etadi
(`/healthz`, `/version` va shu kabilarga ruxsat beradi). Qolgan har bir
so’rov foydalanuvchi yoki service account’ga bog’lanadi va avtorizatsiya
aynan shu shaxs ustida ishlaydi.

```bash
kubectl config view --minify            # SIZNING kubectl qaysi shaxsni ishlatmoqda?
kubectl auth whoami                     # serverning bunga qarashi
kubectl auth can-i create deployments -n dev
```

## Ular nima qilishi mumkin

**Avtorizatsiya rejimlari** API serverda ro’yxat sifatida yoqiladi; birinchi
bo’lib qaror qabul qilgani g’olib:

- `Node` - kubelet’lar faqat o’z node’ining obyektlariga tegishi mumkin;
- `RBAC` - foydalanuvchi va guruhlarga bog’langan Role va ClusterRole’lar:
  siz yozadigani;
- `ABAC` - policy fayli (eski);
- `Webhook` - tashqi xizmatdan so’rash.

```bash
ps -ef | grep kube-apiserver | grep -o -- '--authorization-mode=[^ ]*'
# --authorization-mode=Node,RBAC
```

Avtorizatsiyadan keyin ham **admission** obyektni rad etishi yoki qayta
yozishi mumkin - Pod Security admission workload xavfsizligining aynan o’sha
yerda yashaydigan qismi.

## Workload’lar va node’lar

Pod ishga tushgach, uni har bir boshqa Pod’ga va har bir node’ga yetishdan
nima to’xtatadi? Sukut bo’yicha: hech narsa. Barcha Pod’lar barcha Pod’lar
bilan gaplasha oladi (tarmoq modeli buni va’da qiladi) va konteyner o’z
image’i aytgan foydalanuvchi nomidan ishlaydi, root ham bunga kiradi. Siz
qo’shadigan nazoratlar:

| Xavf | Nazorat |
|---|---|
| har qanday Pod har qanday Pod’ga yetadi | NetworkPolicy (uni qo’llaydigan CNI kerak) |
| konteyner root nomidan, capability’lar bilan ishlaydi | securityContext, Pod Security admission |
| Pod o’qimasligi kerak bo’lgan Secret’larni o’qiydi | ServiceAccount ustidan RBAC, token’ni mount qilmaslik |
| image istalgan joydan | imagePullSecrets, yopiq registry, registry’lar ustidan admission policy |
| konteyner node’ga qochib chiqadi | privileged yo’q, hostPath yo’q, kerak bo’lmasa hostNetwork yo’q |

## Ostidagi sertifikatlar

Arxitektura diagrammasidagi har bir strelka - TLS ulanish: kubectl → API
server, API server → etcd, API server → kubelet, kubelet → API server,
scheduler → API server. Har bir uchning ikkinchi uch ishonadigan CA imzolagan
sertifikati bor. kubeadm ularning barchasini yaratadi va
`/etc/kubernetes/pki` ichiga qo’yadi. Ular muddati tugaganda, narsalar tarmoq
muammosiga o’xshab ko’rinadigan tarzda ishlamay qoladi; birortasiga yo’l
noto’g’ri bo’lsa, komponent crash-loop’ga tushadi. Keyingi besh dars ularni
o’qish va berish haqida.

:::exam-tip
Imtihondagi xavfsizlik topshiriqlari konseptual emas, aniq: Role yaratib uni
bog’lash, sertifikat generatsiya qilib CSR’ni tasdiqlash, NetworkPolicy
yozish, securityContext o’rnatish, ServiceAccount yaratib undan foydalanish.
Bu dars - xarita; ballar keyingilarida.
:::

## O’zingizni tekshiring

1. Klaster xavfsizligi javob beradigan uchta savolni va har biriga javob
   beradigan mexanizmni ayting.
2. Yangi klasterda Pod’lar orasidagi sukut bo’yicha tarmoq qoidalari qanday?
3. kubeadm klasterining sertifikatlari qaysi katalogda turadi?
