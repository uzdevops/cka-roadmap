## Daraxtni qo’lda quring

Bo’sh katalogda birga bajaring. Maqsad - har bir `kustomize` buyrug’i har bir
darajada nimani o’qishini va nima chiqarishini ko’rish.

### 1. Ikkita xizmat, yassi tuzilmada

```bash
mkdir -p k8s && cd k8s
kubectl create deployment api --image=myapi:1.0 --port=8080 --dry-run=client -o yaml > api-deployment.yaml
kubectl expose deployment api --port=80 --target-port=8080 --dry-run=client -o yaml > api-service.yaml
kubectl create deployment db --image=postgres:16 --port=5432 --dry-run=client -o yaml > db-deployment.yaml
kubectl expose deployment db --port=5432 --dry-run=client -o yaml > db-service.yaml
ls
# api-deployment.yaml  api-service.yaml  db-deployment.yaml  db-service.yaml
```

(Mavjud bo’lmagan Deployment’ga `expose --dry-run` qilish uchun Deployment
fayli kerak; soddarog’i: `kubectl create service clusterip api --tcp=80:8080
--dry-run=client -o yaml`. Har holda: to’rtta yaroqli manifest.)

```bash
cat > kustomization.yaml <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - api-deployment.yaml
  - api-service.yaml
  - db-deployment.yaml
  - db-service.yaml
EOF
kubectl kustomize . | grep -E "^kind:|^  name:"
# kind: Service / name: api / kind: Service / name: db / kind: Deployment / name: api / kind: Deployment / name: db
```

To’rtta obyekt kirdi, to’rttasi chiqdi, Service’lar Deployment’lardan oldin
tartiblangan.

### 2. Kataloglarga ajratish

```bash
mkdir api db
mv api-*.yaml api/ && mv db-*.yaml db/
cd api && kustomize create --autodetect && cat kustomization.yaml && cd ..
# resources: [api-deployment.yaml, api-service.yaml]
cd db  && kustomize create --autodetect && cd ..
cat > kustomization.yaml <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - api
  - db
EOF
kubectl kustomize . | grep -c "^kind:"      # 4 - o'sha obyektlar, endi ikki katalogdan yig'ilgan
kubectl kustomize db/ | grep "^kind:"       # faqat db'ning ikkitasi
```

(Alohida `kustomize` yo’qmi? Ikkita ost-kustomization’ni qo’lda yozing; har
biri uch qatordan iborat.)

### 3. Har bir katalogga o’z qoidalarini bering

```bash
cat >> db/kustomization.yaml <<EOF
namespace: data
commonLabels:
  tier: data
EOF
cat >> api/kustomization.yaml <<EOF
commonLabels:
  tier: app
EOF
kubectl kustomize . | grep -E "^kind:|^  name:|namespace:|tier:"
# db obyektlarida namespace: data va tier: data bor; api'nikilarda tier: app va namespace yo'q
```

### 4. Va hammasi uchun bitta qoida

```bash
cat >> kustomization.yaml <<EOF
commonLabels:
  app: shop
EOF
kubectl kustomize . | grep -c "app: shop"   # har bir obyektda (label va selectorlarda ham)
```

### 5. Uni qo’llash

```bash
kubectl create namespace data
kubectl apply -k .
kubectl get deploy,svc -A -l app=shop
# NAMESPACE  NAME            ...
# data       deployment/db
# default    deployment/api
```

### 6. Daraxtni qayta o’qish

```bash
find . -name kustomization.yaml -exec sh -c 'echo "== $1"; cat "$1"' _ {} \;
```

Uchta fayl, har biri bir necha qator, va butun deployment shulardan o’qib
olinadi. Aynan shu o’qish qulayligi - asosiy natija.

:::tip
`kustomize create --autodetect` katalogdagi mavjud fayllardan `resources:`
ro’yxatini yozadi. Uni allaqachon kustomization bor katalogda ishga
tushirsangiz, u bajarishdan bosh tortadi - bu yaxshi xavfsizlik odati: u
hech qachon ustiga yozmaydi.
:::

## O’zingizni tekshiring

1. 2-qadamdan keyin nechta `kustomization.yaml` fayl bo’ladi va ularning har
   birida nima bor?
2. Qaysi obyektlar `namespace: data` oldi va nega api’nikilar olmadi?
3. Daraxtning faqat ma’lumotlar bazasi yarmini qanday qo’llagan bo’lardingiz?
