## Nimani qayta ko’rishni ma’lumotga tayanib hal qiling

Sizda uchta mock bali, uchta takrorlash testi, o’n to’qqiz haftalik dars
testlari va lablar, hamda dashboard’dagi tayyorlik taqsimoti bor. Ular
birgalikda qolgan kunlar qayerga ketishini aytadi. Bu dars - o’sha metod.

## Imtihonning og’irliklari

| Domen | Og’irlik | Bu yo’ldagi haftalar |
|---|---|---|
| **Nosozliklarni bartaraf etish** | **30%** | 19, va 6-8, 14-16 dagi nosozlik jadvallari |
| **Klaster arxitekturasi, o’rnatish va sozlash** | **25%** | 1, 9, 10-12 (RBAC, sertifikatlar), 17, 18 (Helm/Kustomize) |
| **Service’lar va tarmoq** | **20%** | 14-16 |
| **Workload’lar va rejalashtirish** | **15%** | 4-5, 6-8 |
| **Saqlash** | **10%** | 13 |

Ko’paytiring: og’irligi 30% bo’lgan domendan 50% olsangiz, bu sizga
imtihonning 15 balliga tushadi; og’irligi 10% bo’lganidan 50% olsangiz - 5
ballga. O’tish bali 66%. Kunlaringizni qayerga sarflashingiz zaiflikning
o’zi bo’yicha emas, zaiflik va og’irlikning **ko’paytmasi** bo’yicha
bo’lishi kerak.

## 1-qadam: jadvalni tuzing

Noto’g’ri yoki sekin bajargan har bir mock vazifasi va har bir test savoli
uchun bitta qator:

```
| # | nima so'ralgan | domen | nega noto'g'ri ketdi (bilim/navigatsiya/tekshirish/tezlik/o'qish) | qaytiladigan dars |
```

Beshta "nega" toifasi mock-intro darsidan olingan. **tekshirish** haqida
halol bo’ling - "to’g’ri qildim, lekin tekshirmadim va noto’g’ri chiqdi" -
eng ko’p uchraydigani va eng oson tuzatiladigani.

## 2-qadam: dashboard’ni o’qing

Dashboard’dagi tayyorlik taqsimoti har bir bosqichni dars testlari, lablar
va takrorlash testlari bo’yicha baholaydi. Bularni qidiring:

- **70% dan past bosqich** → o’sha bosqichning lablarini qayta bajaring
  (darslarni emas: imtihon shakli - lablarda);
- **ikkinchi urinishda o’tgan test** → o’sha darsning "O’zingizni
  tekshiring" savollari, ovoz chiqarib, konspektsiz;
- **tashlab ketilgan lab** → uni hozir bajaring; tashlab ketilgan lablar
  aynan odamlar yiqiladigan domenlarda to’planadi.

## 3-qadam: reja, ko’paytma bo’yicha

Qatorlarni `og'irlik × necha marta noto'g'ri ketgani` bo’yicha tartiblang.
Yuqoridagi beshtasi - reja. Odatiy beshliklar:

| Agar shu zaif bo’lsa | Buni qiling |
|---|---|
| control plane / node nosozliklari | o’z klasteringizni beshta usulda buzing (scheduler flag’i, kubelet porti, CA yo’li, kube-proxy config yo’li, CoreDNS loop) va har birini vaqt bilan tuzating |
| tarmoq | NetworkPolicy labini ikki marta; Pod’dan DNS mashqi; ingress labi; Service endpoint’lari ro’yxati |
| RBAC / sertifikatlar | CSR’dan foydalanuvchigacha bo’lgan oqim boshdan-oxir, uch marta; har bir identity nomidan `auth can-i` |
| etcd backup/tiklash | backup qiling, Deployment’ni o’chiring, tiklang, qaytganini tasdiqlang - zerikarli bo’lib qolguncha |
| JSONPath | JSONPath darsidagi o’nta so’rov, yoddan |
| imperativ tezlik | o’nta mashq, taymer bilan, har kuni |
| saqlash | ataylab yaratilgan va tuzatilgan PV/PVC bog’lanish nomuvofiqliklari (class, hajm, rejim) |

## 4-qadam: nima qilmaslik kerak

- Yigirma haftaning hammasini qaytadan o’qimang. Siz ularni o’qigansiz;
  qayta o’qish samarali tuyuladi va hech narsani o’zgartirmaydi.
- Qulay bo’lgani uchun allaqachon 90% olayotgan narsangizni o’rganmang.
- Yangi material o’rganmang (operatorlar, service mesh, eBPF) - u imtihonda
  yo’q va imtihonda borini siqib chiqaradi.
- Oxirgi ikki kunda mock 3’ni ikki marta ishlamang. Bitta qiyin mock, keyin
  yengil kun, keyin imtihon.

## Ishlaydigan bir haftalik jadval

| Kun | Nima qilinadi |
|---|---|
| -7 | mock 2 (yoki 1’ni qayta bajaring); jadvalni tuzing |
| -6, -5 | rejaning yuqori ikkita qatori: lablar, vaqt bilan |
| -4 | mock 3; jadvalni yangilang |
| -3, -2 | keyingi qatorlar; har kuni 20 daqiqa tezlik mashqlari |
| -1 | yengil: mashqlarni bir marta, imperativ jadvalni bir marta, kerak bo’ladigan hujjat sahifalari (ularni xayolan belgilab qo’ying: etcd, CSR, NetworkPolicy, DNS, kubeadm upgrade); uyqu |
| 0 | imtihon |

:::tip
Tayyorlik - bu "men hamma narsani bilaman" degani emas. Bu "jadvalda hal
qilinmagan narsa qolmadi va oxirgi mock o’n daqiqa vaqt qolgan holda 66%
dan yuqori edi" degani. Buni ayta olganingizda, o’qishni to’xtating -
keyingi dars imtihon kunining o’zi haqida.
:::

## O’zingizni tekshiring

1. Nega zaif domenlarni faqat zaiflik bo’yicha emas, og’irlik × zaiflik
   bo’yicha tartiblash kerak?
2. "nega noto’g’ri ketdi" toifalaridan qaysi biri eng ko’p uchraydi va uni
   qaysi odat tuzatadi?
3. O’qishga o’xshab tuyuladigan, lekin oxirgi haftaga arzimaydigan uchta
   narsani ayting.
