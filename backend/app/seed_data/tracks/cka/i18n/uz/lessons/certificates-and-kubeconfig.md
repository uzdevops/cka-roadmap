## Bitta fayl, uchta ro’yxat

Har bir `kubectl` buyrug’i uchta narsani bilishi kerak: qaysi **klaster** bilan
gaplashishni (manzil va CA), qaysi **foydalanuvchi** bo’lishni (sertifikat yoki
token) va hozir bu ikkovining qaysi kombinatsiyasini - ustiga sukut bo’yicha
namespace’ni - ishlatishni, ya’ni **context**ni. kubeconfig - shu uchta ro’yxat
va joriy context’ga ishora.

```yaml
apiVersion: v1
kind: Config
clusters:
  - name: kubernetes
    cluster:
      server: https://192.168.1.10:6443
      certificate-authority-data: LS0tLS1CRUdJTi...      # klaster CA'si, base64; yoki certificate-authority: /path/ca.crt
  - name: staging
    cluster:
      server: https://staging.example.com:6443
      certificate-authority: /home/me/staging-ca.crt
users:
  - name: kubernetes-admin
    user:
      client-certificate-data: LS0tLS1CRUdJTi...
      client-key-data: LS0tLS1CRUdJTi...
  - name: ci-bot
    user:
      token: eyJhbGciOiJSUzI1NiIs...
contexts:
  - name: kubernetes-admin@kubernetes
    context:
      cluster: kubernetes
      user: kubernetes-admin
      namespace: default
  - name: ci@staging
    context:
      cluster: staging
      user: ci-bot
current-context: kubernetes-admin@kubernetes
```

`-data` maydonlari fayl mazmunini base64 bilan kodlangan holda saqlaydi
(`--embed-certs` shuni beradi); `-data`siz shakllar esa fayllarga ishora
qiladi. Context - bu (cluster, user, namespace) uchligi; `current-context`
ulardan birini nomlaydi.

## kubectl qayerga qaraydi

1. buyruq satridagi `--kubeconfig=/path`
2. `$KUBECONFIG` (ikki nuqta bilan ajratilgan ro’yxat; birlashtiriladi)
3. `~/.kube/config`

kubeadm control plane’ida admin fayli - `/etc/kubernetes/admin.conf`;
`kubeadm init` sizga uni `~/.kube/config` ga nusxalashni aytadi.

## Uni kubectl config bilan boshqarish

```bash
kubectl config view                          # birlashtirilgan, secret'lar yashirilgan
kubectl config view --minify                 # faqat joriy context
kubectl config view --raw                    # sertifikat ma'lumotlari bilan birga
kubectl config get-contexts                  # * joriysini belgilaydi
kubectl config current-context
kubectl config use-context ci@staging
kubectl config set-context --current --namespace=dev       # sukut bo'yicha namespace'ni o'zgartirish
kubectl config set-context dev@kubernetes --cluster=kubernetes --user=kubernetes-admin --namespace=dev
kubectl config set-cluster staging --server=https://staging.example.com:6443 --certificate-authority=ca.crt --embed-certs=true
kubectl config set-credentials akshay --client-certificate=akshay.crt --client-key=akshay.key --embed-certs=true
kubectl config delete-context old@cluster
kubectl --kubeconfig=/root/my-kube-config config use-context research   # boshqa fayl ustida ishlash
```

:::exam-tip
Ikkita kubeconfig topshirig’i takrorlanadi. **"Qolgan ish uchun F faylidagi X
context’ini ishlating"**: yo `export KUBECONFIG=/path/F` va keyin
`use-context`, yoki `kubectl config --kubeconfig=F use-context X` va har safar
`--kubeconfig=F` uzatish; topshiriq ruxsat bersa, eng tozasi -
`cp F ~/.kube/config`. **"Fayl buzilgan, tuzating"**: u bilan bitta buyruq
ishga tushiring va xatoni o’qing - u muammoni o’zi aytib beradi.
:::

## Xatolarni o’qish

```bash
kubectl --kubeconfig=my-kube-config get pods
```

| Xato | Noto’g’ri maydon |
|---|---|
| `unable to read client-cert /etc/kubernetes/pki/users/dev-user/developer-user.crt ... no such file` | `client-certificate` yo’li - xato yozilgan yoki fayl nomi noto’g’ri |
| `x509: certificate signed by unknown authority` | `certificate-authority` klasterning CA’si emas (yoki klaster sertifikati o’zgargan) |
| `dial tcp ... connection refused` / `i/o timeout` | `server:` da manzil yoki port (`6443`) noto’g’ri |
| `error: context "research" does not exist` | context nomi yoki u boshqa faylda |
| `The connection to the server localhost:8080 was refused` | umuman kubeconfig topilmadi - `KUBECONFIG` o’rnatilmagan va `~/.kube/config` yo’q |
| `error: You must be logged in to the server (Unauthorized)` | foydalanuvchining sertifikati/token’i qabul qilinmadi - muddati o’tgan, uni noto’g’ri CA imzolagan |

Oxirgisiga ikkinchi marta qarash arziydi: fayl *to’g’ri* (kubectl uni yukladi,
ulandi, hisob ma’lumotini taqdim etdi) va shaxsni **server** rad etdi.
Tuzatish faylning tuzilishida emas, hisob ma’lumotida.

## Fayl ichidagi sertifikatlar

```bash
kubectl config view --raw -o jsonpath='{.users[?(@.name=="kubernetes-admin")].user.client-certificate-data}' | base64 -d | openssl x509 -noout -subject -dates
```

- kubeconfig sizni *kimga* aylantirishini va qachongacha amal qilishini shunday
  tekshirasiz. Muddati o’tgan klient sertifikati = `Unauthorized`.

:::tip
`kubectl config view` `-data` maydonlarini `DATA+OMITTED` qilib yashiradi;
ularni ko’rish uchun `--raw` qo’shing. `--minify` esa birlashtirilgan config
uzun bo’lib, sizni faqat ishlatilayotgan context qiziqtirganda kerak bo’ladi.
:::

## O’zingizni tekshiring

1. kubeconfig’dagi uchta ro’yxatni ayting va context nimalarni bog’lashini
   tushuntiring.
2. Qaysi buyruq joriy context’ning sukut bo’yicha namespace’ini almashtiradi?
3. `kubectl --kubeconfig=F get pods` `Unauthorized` deyapti. Fayl buzilganmi
   yoki hisob ma’lumotimi? Nimaga qaraysiz?
