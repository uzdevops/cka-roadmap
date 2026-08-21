## Klaster bilan gaplashishning ikki usuli

**Imperativ**: klasterga nima *qilishni* aytasiz.

```bash
kubectl run web --image=nginx
kubectl create deployment api --image=myapi:1.2 --replicas=3
kubectl expose deployment api --port=80
kubectl scale deployment api --replicas=5
kubectl set image deployment/api myapi=myapi:1.3
kubectl edit deployment api
kubectl delete pod web
```

**Deklarativ**: klasterga faylda nimani *xohlashingizni* aytasiz, qadamlarni
esa u o’zi hisoblab chiqadi.

```bash
kubectl apply -f api.yaml          # yo'q bo'lsa yaratadi, bor bo'lsa yangilaydi, bir xil bo'lsa hech nima
kubectl apply -f ./manifests/      # butun katalog
```

Ikkalasi ham etcd’da bir xil obyektlarga aylanadi. Farqi - kutilgan holatni
kim yuritishida: imperativ buyruqlarda u sizning boshingizda va shell
tarixingizda; `apply` bilan esa ko’rib chiqish, versiyalash va qayta ishga
tushirish mumkin bo’lgan fayllarda.

## Imperativ obyekt konfiguratsiyasi - o’rta yo’l

```bash
kubectl create -f pod.yaml        # mavjud bo'lsa xato
kubectl replace -f pod.yaml       # mavjud bo'lmasa xato; butun obyektni almashtiradi
kubectl delete -f pod.yaml
```

Fayllarni baribir yozasiz, lekin har bir buyruq bitta amal va to’g’risini
o’zingiz tanlashingiz kerak. `apply` bu tanlovni yo’q qiladi.

## `apply` aslida nima qiladi

`apply` - uchta narsa orasidagi uch tomonlama birlashtirish:

1. siz bergan **fayl**,
2. klasterdagi **jonli obyekt**,
3. **oxirgi qo’llangan konfiguratsiya** - o’tgan safar qo’llaganingizdagi
   fayl, kubectl uni obyektdagi annotatsiyada saqlaydi:

```bash
kubectl get deployment api -o jsonpath='{.metadata.annotations.kubectl\.kubernetes\.io/last-applied-configuration}' | jq .
```

Uchtasi bilan apply "siz bu maydonni faylingizdan olib tashladingiz, demak
uni obyektdan o’chir" bilan "bu maydon faylingizda hech qachon bo’lmagan, uni
klaster qo’shgan, tegma" o’rtasidagi farqni ajrata oladi. Aynan shu takroriy
apply’ni xavfsiz qiladi va aynan shuni `create`/`replace` qila olmaydi.

:::warning
Bitta obyektda ikkala uslubni aralashtirish - kutilmagan holatlar manbasi.
`kubectl scale` klasterdagi replikalarni o’zgartiradi, faylingizdagini emas;
keyingi `apply` uni jimgina orqaga qaytaradi. `kubectl edit` ham shunday. Har
bir obyektga bitta egani tanlang: yo fayl unga egalik qiladi (va siz faylni
tahrirlaysiz), yo CLI.
:::

## Qachon qaysi biri

| Vaziyat | Foydalaning |
|---|---|
| imtihon, bir martalik obyektlar, tezlik | imperativ - `run`, `create`, `expose` |
| bayroqlar qo’ya olmaydigan maydon kerak bo’lsa | imperativ **generatsiya**, keyin tahrir, keyin `apply` |
| real muhitlar, saqlab qolmoqchi bo’lgan hamma narsa | deklarativ - Git’dagi fayllar, `apply` |
| jonli obyektni ko’rish yoki biroz o’zgartirish | `describe`, `get -o yaml`, `edit`, `scale`, `set image` |

Hammasini qamrab oladigan imtihon odati:

```bash
kubectl create deployment api --image=myapi:1.2 --replicas=3 --dry-run=client -o yaml > api.yaml
# api.yaml'ni tahrirlang: resources, volume, probe - topshiriq nima so'rasa
kubectl apply -f api.yaml
```

`--dry-run=client` "yuborma, faqat nima yuborishingni chop et" degani.
`--dry-run=server` esa saqlamasdan validatsiya va admission uchun yuboradi -
haqiqiy apply’dan oldin webhook rad etishini ushlash uchun foydali.

:::exam-tip
`kubectl create` yoki `run` bilan yaratilgan obyektda `kubectl apply`
ishlaydi - u faqat bir marta oxirgi qo’llangan annotatsiya yo’qligi haqida
ogohlantiradi va uni yaratadi. Obyektlarni "o’tkazish"ga vaqt sarflamang;
apply kechirimli.
:::

## Fe’llarni o’qish

- `create` / `run` / `expose` - yangi obyekt yaratadi; mavjud bo’lsa xato.
- `apply` - shunday bo’lsin; yaratadi yoki yangilaydi.
- `replace` - butun obyektni almashtiradi; `--force` o’chirib qayta yaratadi.
- `edit` - jonli obyektni `$EDITOR`’da ochadi; chiqishda saqlaydi.
- `patch` - bitta yo’lni o’zgartiradi:
  `kubectl patch deployment api -p '{"spec":{"replicas":2}}'`.
- `set` - keng tarqalgan patch’lar uchun qisqartmalar: `set image`,
  `set env`, `set resources`, `set serviceaccount`.

## O’zingizni tekshiring

1. `kubectl apply` qaysi uchta narsani solishtiradi va uchinchisi qayerda
   saqlanadi?
2. Siz Deployment’ni `kubectl scale` bilan 5 ga o’zgartirdingiz, keyin uning
   3 deb yozilgan faylini `kubectl apply` qildingiz. Nima bo’ladi va nega?
3. `--dry-run=server` qachon `--dry-run=client`’dan yaxshiroq?
