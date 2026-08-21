## Shunday bo’lsin

`kubectl apply -f` - deklarativ fe’l: unga faylni berasiz va klaster o’sha
faylga mos holga keladi. Obyekt mavjud bo’lmasa yaratiladi; mavjud bo’lsa
yangilanadi; allaqachon mos bo’lsa hech nima bo’lmaydi.

```bash
kubectl apply -f deployment.yaml
kubectl apply -f ./manifests/            # katalogdagi har bir fayl
kubectl apply -f https://.../install.yaml
kubectl apply -k ./overlays/prod          # kustomization
kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: dev
EOF
```

## Uch tomonlama birlashtirish

`apply`ni takrorlashga xavfsiz qiladigan narsa - u uchta hujjatni
solishtiradi:

```
   sizning faylingiz      last-applied (annotatsiya)          jonli obyekt
  (nimani xohlaysiz)   (o'tgan safar nimani xohlagansiz)  (klasterda hozir nima bor)
```

| Maydon holati | apply nima qiladi |
|---|---|
| faylingizda bor, jonlisida yo’q | qo’shadi |
| faylingizda ham, jonlisida ham bor, lekin farq qiladi | faylingizdagi qiymatga o’rnatadi |
| last-applied’da bor, faylingizda **yo’q** | **olib tashlaydi** - siz uni ataylab o’chirgansiz |
| jonlisida bor, faylingizda ham, last-applied’da ham yo’q | tegmaydi - unga klaster yoki boshqa vosita egalik qiladi (default’lar, status, scaler) |

Oxirgi qator - eng aqllisi. API server to’ldirgan default’lar, kontroller
boshqaradigan maydonlar, `status` bloki - ularning hech biri faylingizda yo’q
va hech qachon bo’lmagan, shuning uchun apply ularga tegmaydi.

"last-applied" hujjati obyektning o’zida saqlanadi:

```bash
kubectl get deploy web -o jsonpath='{.metadata.annotations.kubectl\.kubernetes\.io/last-applied-configuration}'
```

## Server tomonidagi apply

Yangiroq kubectl birlashtirishni `--server-side` bilan **API serverda**
bajara oladi va maydon egaligini annotatsiya orqali emas, har bir *manager*
bo’yicha kuzatadi (metadata ichidagi `managedFields`). Shunda bir nechta
vosita bitta obyektga bir-birini bosib ketmasdan birga egalik qila oladi.
Mavjudligini bilish foydali; imtihon esa sukut bo’yicha klient tomonidagi
apply’ni kutadi.

```bash
kubectl apply --server-side -f deployment.yaml
kubectl apply --server-side --force-conflicts -f deployment.yaml   # ziddiyatli maydonlar egaligini olish
```

## apply qila olmaydigan narsalar

- **O’zgarmas maydonni o’zgartirish.** Pod’ning konteynerlar ro’yxati,
  Service’ning `clusterIP`si, Job’ning template’i, PVC’ning storage class’i:
  `kubectl apply` "field is immutable" deb xabar beradi. Yechim -
  `kubectl replace --force -f file.yaml`, u o’chirib qayta yaratadi.
- **Katalogdan olib tashlagan obyektlaringizni o’chirish.** `apply -f dir/`
  faqat o’sha yerda turgan fayllarni ko’radi. `--prune` bor, lekin xavfli;
  amalda `kubectl delete -f old.yaml` qilasiz.
- **`kubectl scale` yoki `edit`ni o’zi bekor qilish.** Bekor qiladi - lekin
  faqat faylingizda 3, jonli obyektda esa 5 bo’lgani uchun 3 ni qo’yadi. Bu -
  o’tgan darsdagi uslublarni aralashtirish tuzog’i.

```bash
kubectl diff -f deployment.yaml      # apply nimani o'zgartirardi? - har qanday apply oldidagi eng xavfsiz odat
```

:::exam-tip
Imperativ yaratilgan obyekt ustida `kubectl apply` oxirgi qo’llangan
annotatsiya yo’qligi haqida ogohlantirish chiqaradi va keyin shunchaki
ishlaydi, annotatsiyani qo’shib qo’yadi. Bu ogohlantirishni "tuzatish"ga
to’xtamang. Xuddi shunday, mavjud obyekt ustida `kubectl create -f`
ishlamaydi - obyekt bor-yo’qligiga ishonchingiz komil bo’lmasa `apply`ga
murojaat qiling.
:::

:::tip
`kubectl apply -f x.yaml && kubectl get -f x.yaml` - `get -f` nimani
ko’rsatishni bilish uchun faylni o’qiydi, shuning uchun siz endigina
qo’llagan obyektlarni, kind’idan qat’i nazar, aynan o’zini ko’rasiz.
:::

## O’zingizni tekshiring

1. Maydon o’tgan safar faylda bor edi, bu safar uni olib tashladingiz. apply
   jonli obyektga nima qiladi va buni qayerdan biladi?
2. apply `spec.clusterIP: Invalid value ... field is immutable` deydi. Endi
   nima qilasiz?
3. `kubectl diff -f` nimani ko’rsatadi va nega uni apply’dan oldin ishga
   tushirish kerak?
