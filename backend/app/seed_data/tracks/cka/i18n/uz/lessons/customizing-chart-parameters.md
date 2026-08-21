## Value’ni o’zgartirishning uchta yo’li

Chart’ning `values.yaml` fayli - uning standart qiymatlari. Siz ularni install
yoki upgrade paytida qayta belgilaysiz va aynan shu qayta belgilashlar
release’ni sizniki qiladi.

```bash
helm show values bitnami/wordpress > wp-defaults.yaml      # avval sozlagichlarni o'qing
grep -n "wordpressBlogName\|replicaCount" wp-defaults.yaml
```

### 1. --set, bir yoki ikki value uchun

```bash
helm install my-site bitnami/wordpress \
  --set wordpressBlogName="Helm Tutorials" \
  --set wordpressEmail=john@example.com \
  --set replicaCount=2
```

Ichma-ich kalitlar nuqta bilan yoziladi; ro’yxat elementlari kvadrat qavs
bilan; vergul juftliklarni ajratadi; haqiqiy vergul yoki nuqtaga teskari slash
kerak; Helm raqam deb o’qiydigan joyda `--set-string` uni satr sifatida
majburlaydi; `--set-file key=path` esa fayl mazmunini value ichiga o’qiydi:

```bash
--set image.tag=1.27.1
--set ingress.hosts[0].host=shop.example.com
--set "annotations.nginx\.ingress\.kubernetes\.io/rewrite-target=/"
--set-string podAnnotations.version=123
--set-file tls.crt=./tls.crt
```

`--set` - imtihon va terminal uchun; u uchtadan ortiq value’da qulay emas va
Git’da hech qanday iz qoldirmaydi.

### 2. -f values.yaml, qolgan hamma narsa uchun

```yaml
# my-values.yaml
wordpressBlogName: Helm Tutorials
wordpressEmail: john@example.com
replicaCount: 2
resources:
  requests: {cpu: 250m, memory: 256Mi}
ingress:
  enabled: true
  hostname: shop.example.com
```

```bash
helm install my-site bitnami/wordpress -f my-values.yaml
helm install my-site bitnami/wordpress -f base.yaml -f prod.yaml    # keyingi fayllar oldingilarini bosadi
helm upgrade my-site bitnami/wordpress -f my-values.yaml            # har safar o'sha faylning o'zi
```

Faqat siz belgilagan kalitlar qayta belgilanadi; qolgani chart’ning standart
qiymatida qoladi. Bu faylni boshqa manifestlaringiz yoniga commit qiling - u
release’ning konfiguratsiyasining **o’zi**.

### 3. Chart’ni pull qilib tahrirlash

```bash
helm pull bitnami/wordpress --untar
cd wordpress
vim values.yaml                     # standart qiymatlarning o'zini o'zgartiring
helm install my-site ./             # lokal, o'zgartirilgan chart'dan o'rnating
```

Bir martalik ish uchun yoki shablonga value’lar ruxsat bermaydigan o’zgarish
kerak bo’lganda foydali. Narxi: endi sizda o’z fork’ingiz bor va keyingi
upstream chart versiyasiga `helm upgrade` qilish tahrirlaringizni qaytadan
qo’llash demakdir. Value mavjud bo’lgan har qanday holatda `-f` ni afzal
ko’ring.

## Ustuvorlik, yana bir bor

```
chart values.yaml  <  -f file1  <  -f file2  <  --set
```

Keyingisi yutadi. `upgrade` esa yana **chart standartlaridan** boshlanadi,
ustiga bu safar uzatganingiz qo’shiladi - o’sha `-f` faylni uzating yoki
`--reuse-values` ishlating.

## Nima belgilaganingizni tekshirish

```bash
helm get values my-site                  # faqat foydalanuvchi bergan value'lar
helm get values my-site --all            # standartlar bilan birlashtirilgani
helm get values my-site --revision 1     # 1-reviziyada nima bo'lgani
helm diff upgrade my-site bitnami/wordpress -f my-values.yaml    # helm-diff plagini: nima o'zgarishi MUMKINligi
```

:::exam-tip
Topshiriqlar buni "X value’ni Y ga qo’ying" deb ifodalaydi: bu install yoki
upgrade’dagi `--set X=Y`. Agar topshiriq sizga values fayl bersa - `-f`. Kalit
to’g’rimi-yo’qmi ishonchingiz bo’lmasa, `helm show values <chart> | grep <key>` -
xato yozilgan kalitni ko’pchilik chart’lar jimgina e’tiborsiz qoldiradi va
release standart qiymat bilan ko’tariladi; qo’rqish kerak bo’lgan nosozlik shu.
:::

## O’zingizni tekshiring

1. `ingress.hosts[0].host=shop.example.com` uchun `--set` yozing.
2. Ikkita `-f` fayl va bitta `--set` `replicaCount` ni belgilaydi. Qaysi biri
   yutadi?
3. Nega pull qilingan chart’ning `values.yaml` faylini tahrirlash odatda `-f`
   uzatishdan yomonroq?
