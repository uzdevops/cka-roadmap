## Uchala turni qo’lda yasash

kubeadm bularning hammasini siz uchun qiladi. Buni bir marta qo’lda bajarish -
oldingi darsdagi flaglarning sehr bo’lishdan to’xtaydigan joyi va bu imtihonda
foydalanuvchi hisob ma’lumotlarini yasash uchun ishlatadigan o’sha openssl.

### 1. CA

```bash
openssl genrsa -out ca.key 2048
openssl req -new -key ca.key -subj "/CN=KUBERNETES-CA" -out ca.csr
openssl x509 -req -in ca.csr -signkey ca.key -CAcreateserial -days 3650 -out ca.crt
```

`-signkey ca.key` so’rovni o’zining kaliti bilan imzolaydi: o’zini o’zi
imzolagan root. `ca.crt` - har bir komponentga ishonish aytiladigan narsa;
`ca.key` - qolgan hamma narsani imzolaydigan va hech qachon control plane’dan
chiqmasligi kerak bo’lgan narsa.

### 2. Klient sertifikati - admin

```bash
openssl genrsa -out admin.key 2048
openssl req -new -key admin.key -subj "/CN=kube-admin/O=system:masters" -out admin.csr
openssl x509 -req -in admin.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 365 -out admin.crt
```

`CN` foydalanuvchi nomiga, `O` esa guruhga aylanadi. `system:masters` buni
cheksiz vakolatli admin qiladi; haqiqiy foydalanuvchi esa `O=developers` va
RBAC binding olardi.

Uni ishlating:

```bash
curl https://<apiserver>:6443/api/v1/pods --cacert ca.crt --cert admin.crt --key admin.key
# yoki uni kubeconfig'ga qo'ying:
kubectl config set-credentials kube-admin --client-certificate=admin.crt --client-key=admin.key --embed-certs=true
```

O’sha retsept, boshqa subject’lar bilan, scheduler’ning
(`CN=system:kube-scheduler`), controller manager’ning
(`CN=system:kube-controller-manager`) va har bir kubelet’ning
(`CN=system:node:node01`, `O=system:nodes`) klient sertifikatlarini yasaydi.

### 3. Server sertifikati - API server

Server sertifikati klientlar unga ulanish uchun ishlatadigan **har bir nom va
manzilni** sanab o’tishi kerak, aks holda klientning nom tekshiruvi
ishlamaydi. API server uchun bu - uzun ro’yxat:

```bash
cat > apiserver.cnf <<EOF
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name
[req_distinguished_name]
[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names
[alt_names]
DNS.1 = kubernetes
DNS.2 = kubernetes.default
DNS.3 = kubernetes.default.svc
DNS.4 = kubernetes.default.svc.cluster.local
DNS.5 = controlplane
IP.1 = 10.96.0.1            # kubernetes Service'ining ClusterIP'si
IP.2 = 192.168.1.10         # node'ning IP'si
IP.3 = 127.0.0.1
EOF

openssl genrsa -out apiserver.key 2048
openssl req -new -key apiserver.key -subj "/CN=kube-apiserver" -config apiserver.cnf -out apiserver.csr
openssl x509 -req -in apiserver.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -days 365 -extensions v3_req -extfile apiserver.cnf -out apiserver.crt
```

`subjectAltName` ro’yxati - kubeadm to’g’ri qiladigan, odamlar esa xato
qiladigan qism. O’rnatish paytida load balancer nomini
`kubeadm init --apiserver-cert-extra-sans=lb.example.com` bilan qo’shasiz;
keyinchalik esa bu "apiserver sertifikatini qayta yaratish" bo’ladi - eskisini
chetga surib, `kubeadm init phase certs apiserver --apiserver-cert-extra-sans=...`.

:::warning
API serverga uning SAN’lari ichida **bo’lmagan** IP yoki nom orqali ulanish
`x509: certificate is valid for kubernetes, ..., not lb.example.com` bilan
ishlamaydi. Bu xato uning *bor* SAN’larini sanab beradi - uni o’qing; u sizga
nima qo’shish kerakligini aniq aytadi.
:::

### 4. Ular qayerga boradi

| Fayl | Qayerga |
|---|---|
| `ca.crt` | har bir kubeconfig (`certificate-authority-data`), API server `--client-ca-file`, kubelet `clientCAFile` |
| `ca.key` | faqat API server node’i; CSR’larni imzolay olishi uchun controller manager `--cluster-signing-key-file` |
| `apiserver.crt/.key` | API server `--tls-cert-file` / `--tls-private-key-file` |
| `admin.crt/.key` | adminning kubeconfig’i |

## Yasaganingizni o’qish

```bash
openssl x509 -in apiserver.crt -text -noout | grep -E "Subject:|Issuer:|Not After|DNS:|IP Address"
```

Subject - u kim ekani, Issuer - uni kim imzolagani, Not After - u qachon
ishlashdan to’xtashi, SAN satri esa u amal qiladigan har bir nom. Keyingi dars
buni odatga aylantiradi.

:::exam-tip
Imtihonda foydalanuvchi uchun siz `openssl x509 -CA ca.key`’ni o’zingiz
**ishlatmaysiz** - sog’lom klasterda sizda `ca.key` yo’q. Siz openssl bilan
kalit va CSR yaratasiz va CSR’ni imzolash uchun **Certificates API**’ga
berasiz (ikki darsdan keyin). openssl qismi - 2-qadamning dastlabki ikkita
buyrug’i.
:::

## O’zingizni tekshiring

1. Qaysi ikkita openssl buyrug’i foydalanuvchining shaxsiy kaliti va CSR’ini
   yaratadi va qaysi subject maydonlari foydalanuvchi nomi bilan guruhni
   belgilaydi?
2. Nega API server sertifikatiga SAN ro’yxati kerak va biror nom yetishmasa
   nima bo’ladi?
3. Qaysi fayl hech qachon control plane’dan nusxalanmasligi kerak va qaysi
   fayl har bir kubeconfig’ga kiradi?
