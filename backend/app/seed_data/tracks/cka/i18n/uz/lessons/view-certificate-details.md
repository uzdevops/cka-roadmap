## Har qanday sertifikatni o’qiydigan bitta buyruq

```bash
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout
```

```
Certificate:
    Data:
        Serial Number: ...
        Issuer: CN = kubernetes                        <- who signed it: the cluster CA
        Validity
            Not Before: Aug 20 10:00:00 2026 GMT
            Not After : Aug 20 10:00:00 2027 GMT       <- expiry
        Subject: CN = kube-apiserver                   <- who it is
        X509v3 extensions:
            X509v3 Subject Alternative Name:
                DNS:controlplane, DNS:kubernetes, DNS:kubernetes.default, DNS:kubernetes.default.svc,
                DNS:kubernetes.default.svc.cluster.local, IP Address:10.96.0.1, IP Address:192.168.1.10
```

Sizdan so’raladigan har qanday sertifikat savoliga to’rtta satr javob beradi:

```bash
openssl x509 -in cert.crt -noout -subject      # kim
openssl x509 -in cert.crt -noout -issuer       # kim imzolagan
openssl x509 -in cert.crt -noout -dates        # qachondan / qachongacha
openssl x509 -in cert.crt -noout -ext subjectAltName   # u amal qiladigan har bir nom va IP
```

## Butun klasterni tekshirish

Klasterni meros qilib olganingizda - yoki imtihonda "sertifikatlarda nima
noto’g’ri ekanini toping" deyilganda - to’plamni shu jadvalni yodda tutgan
holda aylanib chiqing:

| Sertifikat | Yo’l | Kutilgan CN | Kutilgan O / SAN’lar | Kim imzolagan |
|---|---|---|---|---|
| API server | `pki/apiserver.crt` | `kube-apiserver` | klasterning barcha nomlari + IP’lar | `kubernetes` (klaster CA’si) |
| API server → kubelet | `pki/apiserver-kubelet-client.crt` | `kube-apiserver-kubelet-client` | `O=kubeadm:cluster-admins` | klaster CA’si |
| API server → etcd | `pki/apiserver-etcd-client.crt` | `kube-apiserver-etcd-client` | - | **etcd CA’si** |
| etcd server | `pki/etcd/server.crt` | node nomi | node nomi, IP, localhost | etcd CA’si |
| etcd peer | `pki/etcd/peer.crt` | node nomi | node nomi, IP | etcd CA’si |
| admin | `admin.conf` ichida | `kubernetes-admin` | `O=kubeadm:cluster-admins` | klaster CA’si |
| kubelet klienti | `kubelet.conf` ichida | `system:node:<name>` | `O=system:nodes` | klaster CA’si |

```bash
# kubeconfig'larga joylangan sertifikatlar: avval dekodlang, keyin o'qing
grep client-certificate-data /etc/kubernetes/admin.conf | awk '{print $2}' | base64 -d | openssl x509 -noout -subject -dates
```

:::tip
Hujjatlar bilan birga **Certificate health check spreadsheet** keladi - aynan
shu ustunlarga ega jadval - klasterni tartib bilan ko’rib chiqish uchun. Sizga
bu fayl kerak emas; sizga odat kerak: har bir sertifikat uchun subject,
issuer, SAN’lar, amal qilish muddati va unga murojaat qiladigan flagni yozib
boring, shunda nomuvofiqlik ko’zga tashlanadi.
:::

## kubeadm bu yurishni siz uchun bajaradi

```bash
kubeadm certs check-expiration
```

```
CERTIFICATE                EXPIRES                  RESIDUAL TIME   CERTIFICATE AUTHORITY   EXTERNALLY MANAGED
admin.conf                 Aug 20, 2027 10:00 UTC   364d            ca                      no
apiserver                  Aug 20, 2027 10:00 UTC   364d            ca                      no
apiserver-etcd-client      Aug 20, 2027 10:00 UTC   364d            etcd-ca                 no
apiserver-kubelet-client   Aug 20, 2027 10:00 UTC   364d            ca                      no
...
CERTIFICATE AUTHORITY   EXPIRES                  RESIDUAL TIME
ca                      Aug 18, 2036 10:00 UTC   9y
etcd-ca                 Aug 18, 2036 10:00 UTC   9y
```

Bitta ekran: kubeadm biladigan har bir sertifikat, uni qaysi CA imzolagani va
unga qancha vaqt qolgani. Uzoq sokinlikdan keyin g’alati ishlayotgan har
qanday klasterda avval shuni ishga tushiring.

## kubectl o’lganda muammoni topish

Agar API server ishga tushmasa, kubectl sizga sababini ayta olmaydi. Control
plane node’da:

```bash
crictl ps -a | grep kube-apiserver               # crash-loop'damikan?
crictl logs <container-id> 2>&1 | tail -20
# ... open /etc/kubernetes/pki/etcd/ca.crt: no such file or directory
# ... x509: certificate has expired or is not yet valid
# ... tls: failed to find any PEM data in certificate input
journalctl -u kubelet | grep -i cert              # o'sha voqeaning kubelet tomoni
```

Bu satrlarning har biri bitta faylga ishora qiladi: noto’g’ri yo’l (manifestdagi
flagni tuzating), muddati o’tgan sertifikat (`kubeadm certs renew`) yoki aslida
sertifikat bo’lmagan fayl (kimdir uning ustiga yozgan - backup’dan tiklang yoki
`kubeadm init phase certs <name>` bilan qayta yarating).

:::exam-tip
"Sertifikat topshirig’i" uchun tez saralash tartibi: muddat uchun
`kubeadm certs check-expiration` → API server ishlatadigan har bir yo’lni
sanash uchun `grep -- --.*file /etc/kubernetes/manifests/kube-apiserver.yaml`
va har birini `ls -l` qilish → shubhali fayl ustida `openssl x509
-noout -subject -issuer -dates`. Uchta buyruq deyarli barcha variantni qoplaydi.
:::

## O’zingizni tekshiring

1. Sertifikatning subject, issuer va sanalarini chop etadigan bitta qatorli
   openssl buyrug’ini yozing.
2. `apiserver-etcd-client.crt` ni qaysi CA imzolagan bo’lishi kerak va buni
   qanday tekshirasiz?
3. API server ishlamayapti. Node’dagi qaysi ikkita buyruq sizga sertifikat
   xatosi xabarini ko’rsatadi va qanday uch xil xatoni ko’rishni kutasiz?
