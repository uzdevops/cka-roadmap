## Transformer’lar haqiqiy daraxtda

Kataloglar demosidagi `k8s/` daraxtini davom ettiramiz - `api/` va `db/`,
har birida bittadan Deployment va Service bor, root kustomization ularni
birlashtiradi.

### 1. Root’dan prefiks va namespace

```bash
cat k8s/kustomization.yaml
# resources: [api, db]
# commonLabels: {app: shop}
cat >> k8s/kustomization.yaml <<EOF
namePrefix: shop-
namespace: shop
EOF
kubectl kustomize k8s | grep -E "^  name:|namespace:"
#   name: shop-api       namespace: shop
#   name: shop-db        namespace: shop   (db'ning o'z `namespace: data` si otasi tomonidan bosib ketildi)
```

Havolalar tuzatilganini tekshiring: api Deployment’ining Service selectori va
nomlari hamon bir-biriga mos.

```bash
kubectl kustomize k8s | grep -B2 -A6 "kind: Service" | grep -E "name:|app:"
```

### 2. Overlay’dan image’lar

```bash
mkdir -p k8s/overlays/prod
cat > k8s/overlays/prod/kustomization.yaml <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../..                          # baza sifatida root k8s/
images:
  - name: myapi
    newTag: "2.1.0"
  - name: postgres
    newName: harbor.corp/postgres
    newTag: "16.3"
EOF
kubectl kustomize k8s/overlays/prod | grep image:
#   image: myapi:2.1.0
#   image: harbor.corp/postgres:16.3
```

### 3. Har bir muhit uchun replikalar va label’lar

```bash
cat >> k8s/overlays/prod/kustomization.yaml <<EOF
replicas:
  - name: api                      # ORIGINAL nom, root'ning namePrefix'idan oldingi
    count: 4
labels:
  - pairs: {env: prod}
    includeSelectors: false
commonAnnotations:
  owner: platform
EOF
kubectl kustomize k8s/overlays/prod | grep -E "replicas:|env:|owner:"
```

`shop-api` emas, `name: api` ekaniga e’tibor bering: Kustomize nomni o’sha
darajadagi o’z transformer’lari ishga tushishidan **oldin** resursda qanday
bo’lsa, shundayligicha solishtiradi. Bu - hammani bir marta qoqintiradigan
qoida.

### 4. Dev overlay, uch qator farq bilan

```bash
mkdir -p k8s/overlays/dev
cat > k8s/overlays/dev/kustomization.yaml <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources: [../..]
nameSuffix: -dev
images:
  - name: myapi
    newTag: main
replicas:
  - name: api
    count: 1
EOF
diff <(kubectl kustomize k8s/overlays/dev) <(kubectl kustomize k8s/overlays/prod)
```

`diff` - mashqning butun mag’zi: ikki muhit aynan overlay’lar aytgan
qatorlarda farq qiladi, boshqa hech narsada emas.

### 5. Ikkalasini qo’llash

```bash
kubectl create ns shop
kubectl apply -k k8s/overlays/prod
kubectl apply -k k8s/overlays/dev
kubectl get deploy -n shop
# shop-api-dev    1/1
# shop-api        4/4
# shop-db-dev     1/1
# shop-db         1/1
```

Bu yerda ikkala overlay bitta namespace’ni faqat root uni qo’ygani uchun
bo’lishadi; haqiqiy sozlamada har bir overlay’ga o’zining `namespace:`i
berilardi.

:::tip
Transformer’ga har qanday o’zgartirish kiritgach, tegib chiqqan maydoningizni
`kubectl kustomize | grep` bilan qidiring. Bu butun natijani o’qishdan tez va
`images` hamda `replicas`’ning "hech narsaga mos kelmadi" sukutini ushlaydi.
:::

## O’zingizni tekshiring

1. Root `namePrefix: shop-` qo’yadi. Overlay’ning `replicas`ida `api` deb
   yozasizmi yoki `shop-api` deb? Nega?
2. Har bir `postgres` image’ini ichki registry’ga yo’naltirish uchun qaysi
   transformer’dan foydalanasiz va uning bir qatorli yozuvi qanday?
3. `diff <(kubectl kustomize dev) <(kubectl kustomize prod)` nimani
   isbotlaydi?
