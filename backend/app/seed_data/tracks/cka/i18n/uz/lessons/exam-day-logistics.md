## Mock’lar nima uchun kerak

Uchta to’liq mock, har biri klasterdagi amaliy vazifalar to’plami, har
biridan keyin qadamma-qadam yechimlar darsi, har biri shu platformadagi 15
savolli takrorlash testi bilan yakunlanadi. Ular Kubernetes’ni
o’rgandingizmi degan sinov emas - o’n to’qqiz hafta davomida o’rgandingiz.
Ular buni **soat ostida, birovning klasterida, yagona manba sifatida
hujjatlar sayti bilan** qila olasizmi degan sinov. Bu alohida ko’nikma va u
mashq qilib rivojlantiriladi.

## Haqiqiy imtihon, raqamlarda

| | |
|---|---|
| Format | amaliyotga asoslangan: jonli klasterlarda 15-20 vazifa, terminal va brauzerli masofaviy ish stolida |
| Vaqt | **2 soat** |
| O’tish | **66%** |
| Klasterlar | bir nechta; har bir vazifa `kubectl config use-context <name>` bilan boshlanadi |
| Ruxsat etilgan | **kubernetes.io/docs**, **kubernetes.io/blog**, **helm.sh/docs** (va kubernetes.io’ning subdomenlari) uchun bitta brauzer tabi; boshqa hech narsa, konspekt yo’q |
| Qayta topshirish | xarid bilan birga bitta bepul qayta topshirish kiradi |
| Amal qilish muddati | sertifikat 2 yil amal qiladi |

Vazifalar og’irlangan (2%-13%); har bir vazifa ichida qisman ball bor.
Band qilishdan oldin joriy qoidalar uchun Linux Foundation’ning nomzod
qo’llanmasini ko’rib chiqing - ular o’zgarib turadi.

## Mock’ni qanday o’tkazish kerak

1. **2 soatni ajrating**. Telefon uzoqda, bitta monitor, konspekt yo’q -
   haqiqiy imtihondagi bilan bir xil cheklovlar.
2. **Terminalni imtihon kunidagidek sozlang** (keyingi darslar):
   `alias k=kubectl`, `export do="--dry-run=client -o yaml"`, vim’da
   `set ts=2 sw=2 et`.
3. **Vazifalarni tartib bilan bajaring, lekin bemalol o’tkazib yuboring.**
   5 daqiqada joyidan qimirlamagan narsa: belgilab qo’ying, oldinga o’ting,
   keyin qayting.
4. **Har bir vazifani tashlab ketishdan oldin tekshiring**: `get`,
   `describe`, `curl`. Bajarilgan, lekin tekshirilmagan vazifa - yarim
   vazifa.
5. **2 soatda to’xtang.** Hatto vazifaning o’rtasida bo’lsangiz ham. Maqsad
   - 2 soat sizga nima berishini bilib olish.

## O’zingizni baholash

Har bir mock darsi o’z vazifalarini og’irligi bilan sanab beradi. Vazifaga
ball faqat **yakuniy holat** so’ralganidek aynan bo’lsa qo’ying - nom,
namespace, image, label’lar, portlar, fayl yo’li. To’g’ri image va
noto’g’ri nomga ega Pod - 0.

```
ball = to'liq to'g'ri bajarilgan vazifalar og'irliklari yig'indisi
```

Keyin yechimlar darsi: har bir vazifaning yechimini o’qing, **to’g’ri
bajarganlaringizni ham** - tez yo’l sizning yo’lingizdan tezroq bo’lishi
mumkin.

## Noto’g’ri javob bilan nima qilish kerak

Noto’g’ri javob - mock ishlab chiqaradigan eng qimmatli narsa. Uni
tasniflang:

| Nega noto’g’ri ketdi | Bu nimani anglatadi | Tuzatish |
|---|---|---|
| buyruq / maydonni bilmadim | **bilim** bo’shlig’i | o’sha darsni qayta o’qing; labini qaytadan bajaring |
| bilardim, lekin hujjatlardan yetarlicha tez topa olmadim | **navigatsiya** bo’shlig’i | hujjat sahifasi qayerdaligini yodlang; qidiruv so’zini mashq qiling |
| bilardim, xato terdim, sezmadim | **tekshirish** bo’shlig’i | tekshiruvni odatga aylantiring: har bir `create`dan keyin `get` |
| vaqt yetmadi | **tezlik** bo’shlig’i | tezlik mashqlari darsi; imperativ buyruqlar; oldinroq o’tkazib yuboring |
| topshiriqni noto’g’ri o’qidim | **o’qish** bo’shlig’i | vazifalarni ikki marta o’qing; nomlar, namespace’lar, raqamlarni belgilang |

Har birini weak-domain-review darsining formatida yozib boring. Uchta mock
shulardan o’n beshtachasini beradi va ular qolgan kunlar uchun sizning
o’quv rejangiz.

## Mock’lar orasida

Uchalasini ketma-ket olmang. Mock 1, keyin bir-ikki kun uning bo’shliqlarini
yopish; mock 2 (qiyinroq), xuddi shunday; mock 3 (eng qiyini) imtihondan
bir necha kun oldin, ortidan yengil kun. Ko’rgan mock’ingizni qayta
bajarish birinchi martasidan kamroq foyda beradi, lekin bir hafta o’tib
ham qiymatga ega - vazifalar standart shakllarda va bu shakllar imtihonda
takrorlanadi.

:::tip
Imtihon masofaviy ish stolida sizga scratchpad (bloknot) beradi. Mock’larda
ham xuddi shunday ochiq matn fayli tuting: o’tkazib yuborgan vazifalarning
nomlari va raqamlarini hamda qayta ishlatmoqchi bo’lgan buyruqlarni tashlab
boring. Bu - sizga ruxsat etilgan yagona "konspekt", chunki uni imtihon
paytida o’zingiz yozasiz.
:::

## O’zingizni tekshiring

1. CKA’ning vaqt chegarasi va o’tish bali qancha, terminaldan tashqari nima
   ochiq tursa bo’ladi?
2. To’g’ri bajargan vazifalaringizning yechimini nega o’qishingiz kerak?
3. Noto’g’ri javobning besh turini va har birini qaysi dars yoki odat
   tuzatishini ayting.
