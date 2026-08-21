## Klaster orqali imzolash, klasterda emas

Odamlarga control plane’da `ca.key` bilan imzolangan sertifikatlarni ulashish
masshtablanmaydi va hech kim CA kaliti bilan openssl ishlatish uchun control
plane’ga kirmasligi kerak. **Certificates API** imzolashni Kubernetes ish
oqimiga aylantiradi: foydalanuvchi CSR obyektini yuboradi, administrator uni
kubectl bilan tasdiqlaydi, CA kalitini ushlab turgan controller manager esa
uni imzolaydi va sertifikatni obyektning ichiga qaytarib yozadi.

```
user: openssl key + CSR ──▶ CertificateSigningRequest object ──▶ admin approves ──▶ controller-manager signs ──▶ .status.certificate
```

## Bosqichma-bosqich

**Foydalanuvchi kalit va CSR yasaydi** (o’z mashinasida; shaxsiy kalit hech
qayerga ko’chmaydi):

```bash
openssl genrsa -out akshay.key 2048
openssl req -new -key akshay.key -subj "/CN=akshay/O=developers" -out akshay.csr
```

**CSR’ni obyektga o’rang:**

```bash
cat akshay.csr | base64 -w 0          # bitta satr, request maydoni uchun
```

```yaml
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: akshay
spec:
  request: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURSBSRVFVRVNULS0tLS0K...   # base64 qilingan CSR
  signerName: kubernetes.io/kube-apiserver-client                # "API server bilan gaplashish uchun klient sertifikati"
  expirationSeconds: 86400                                        # ixtiyoriy, min 600
  usages:
    - client auth
```

```bash
kubectl apply -f akshay-csr.yaml
kubectl get csr
# NAME     AGE   SIGNERNAME                            REQUESTOR          REQUESTEDDURATION   CONDITION
# akshay   5s    kubernetes.io/kube-apiserver-client   kubernetes-admin   24h                 Pending
```

**Admin tasdiqlaydi (yoki rad etadi):**

```bash
kubectl certificate approve akshay
kubectl certificate deny agent-smith          # o'zingiz tanimagan har qanday so'rovni
kubectl get csr akshay -o yaml | grep -A3 conditions
```

**Imzolangan sertifikatni chiqarib oling:**

```bash
kubectl get csr akshay -o jsonpath='{.status.certificate}' | base64 -d > akshay.crt
openssl x509 -in akshay.crt -noout -subject -issuer -dates
# subject=O = developers, CN = akshay
# issuer=CN = kubernetes
```

**Uni ishga soling:**

```bash
kubectl config set-credentials akshay --client-certificate=akshay.crt --client-key=akshay.key --embed-certs=true
kubectl config set-context akshay@kubernetes --cluster=kubernetes --user=akshay
kubectl --context=akshay@kubernetes get pods        # RBAC boshqacha demaguncha 403 - bu to'g'ri
```

## signerName

| Signer | Nima beradi |
|---|---|
| `kubernetes.io/kube-apiserver-client` | foydalanuvchilar uchun klient sertifikatlari; **qo’lda tasdiqlash kerak** |
| `kubernetes.io/kube-apiserver-client-kubelet` | kubelet klient sertifikatlari; bootstrap qilinayotgan node’lar uchun avtomatik tasdiqlanadi |
| `kubernetes.io/kubelet-serving` | kubelet’ning **server** sertifikatlari (10250-port); avto-tasdiqlovchini yoqmagan bo’lsangiz, tasdiqlash kerak |
| `kubernetes.io/legacy-unknown` | controller manager uni avtomatik imzolamaydi |

Noto’g’ri signer bilan yozilgan CSR abadiy `Pending` bo’lib qoladi yoki
tasdiqlanadi-yu, hech qachon sertifikat olmaydi. Agar `approve` muvaffaqiyatli
o’tsa, lekin `.status.certificate` bo’sh qolsa, signer’ni tekshiring - va
controller manager CA’ga ishora qiluvchi `--cluster-signing-cert-file` hamda
`--cluster-signing-key-file` bilan ishlayotganini tekshiring, chunki imzolashni
o’sha komponent bajaradi.

:::exam-tip
Ball yo’qotadigan uchta satr: `request` CSR’ning **bitta satrdagi** base64’i
bo’lishi kerak (`base64 -w 0`); `usages` ichida `client auth` bo’lishi kerak;
`signerName` esa `kubernetes.io/kube-apiserver-client` bo’lishi kerak.
Hujjatlarning "Certificate Signing Requests" sahifasida nusxa ko’chiriladigan
tayyor manifest bor - o’shani ishlating.
:::

## Shubhali CSR’ni o’qish

```bash
kubectl get csr agent-smith -o jsonpath='{.spec.request}' | base64 -d | openssl req -noout -subject
# subject=CN = agent-x, O = system:masters
```

Notanish so’rovchidan kelgan `system:masters` so’rovi - bu cluster-admin
so’rovi. Uni rad eting. Tasdiqlashdan oldin so’rovning ichidan subject’ni o’qib
olish - aynan o’sha odat.

## Kubelet’lar ham buni ishlatadi

Node qo’shilganda uning kubelet’i o’zining klient sertifikati uchun CSR
yuboradi (bootstrap token orqali avtomatik tasdiqlanadi), ixtiyoriy ravishda
serving sertifikati uchun ham. Rotatsiya yoqilgan klasterda `kubectl get csr`
`system:node:*` so’rovlarining muntazam oqimini ko’rsatadi - bu normal.
`kubelet-serving` CSR’i Pending turgan node ishonchli sertifikat orqali
`kubectl logs` bera olmaydi; uni `kubectl certificate approve` qiling.

## O’zingizni tekshiring

1. Tasdiqlangan CSR’ni kim imzolaydi va o’sha komponentga buning uchun qaysi
   ikkita fayl kerak?
2. CSR Approved, lekin `.status.certificate` bo’sh. Nimani tekshirasiz?
3. CSR’ni tasdiqlashdan oldin undan nimani o’qib olishingiz kerak va buni
   qanday qilasiz?
