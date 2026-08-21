## Imtihonni band qilish

- Imtihonni training.linuxfoundation.org da sotib oling (CKA - Linux
  Foundation / CNCF imtihoni, PSI orqali o’tkaziladi). Xaridga **bitta
  bepul qayta topshirish** va, shu yozilgan paytda, killer.sh
  simulyatorining ikkita sessiyasi kiradi - ulardan mock 3’dan keyin
  foydalaning, undan oldin emas.
- Voucher bir yil amal qiladi; **imtihon sanasi** portalda alohida band
  qilinadi, istalgan kunga, deyarli istalgan soatga. O’zingiz tetik
  bo’ladigan kun vaqtiga, ikki-uch hafta oldinga band qiling, shunda sana
  haqiqiy bo’ladi.
- Bir hafta oldin **Candidate Handbook** va **Important Instructions**
  sahifasini o’qing. Qoidalar o’zgaradi (ruxsat etilgan domenlar, ID
  talablari, xona qoidalari); bu dars ularning o’rnini bosmaydi.

## Bir kun oldin

- Foydalanadigan mashinangiz va tarmog’ingizda PSI **tizim tekshiruvini**
  ishga tushiring: brauzer, veb-kamera, mikrofon, ekranni ulashish. Bitta
  tashqi monitor yoki noutbuk ekrani - ikkalasi emas.
- Band qilishdagi ism bilan aynan mos keladigan davlat **ID**’si.
- Tinch xonada **toza stol**: qog’oz yo’q, ikkinchi qurilma yo’q, devorda
  konspekt yo’q, stolda mashinadan boshqa hech nima yo’q. Proctor sizdan
  kamerani xona bo’ylab va stol ostiga aylantirishni so’raydi.
- Xohlasangiz, shaffof idishda suv.
- Mashqlarni bir marta; imperativ jadvalni bir marta; keyin to’xtang.
  Uxlang.

## O’sha kun

- **30 daqiqa oldin** ro’yxatdan o’ting; ID va xona tekshiruvi vaqt oladi.
- Imtihon PSI’ning xavfsiz brauzerida, **masofaviy ish stolida** (XFCE)
  ishlaydi: terminal va faqat ruxsat etilgan hujjat saytlari bilan
  cheklangan Firefox. Sizning brauzeringiz va xatcho’plaringiz u yerda
  yo’q. Nusxa ko’chirish-qo’yish masofaviy ish stoli ichida ishlaydi;
  terminalda `Ctrl+Shift+C/V`.
- Nolinchi daqiqa, 1-vazifadan oldin: `alias k`, `$do`, vim sozlamalari,
  terminal ishlayotganini ko’rish uchun bitta `k get
  nodes`.
- Har bir vazifada: **ikki marta o’qing**, berilganidek `kubectl config
  use-context`, bajaring, **tekshiring**, ochiq ssh’dan `exit` qiling,
  keyingisiga o’ting. O’tkazib yuborilgan vazifalar uchun ichki
  bloknotdan foydalaning.
- Qiyin savol: 5 daqiqa, keyin o’tkazib yuboring va qaytib keling. Qisman
  ball bor; tegilmagan oson vazifa qotib qolgan qiyin vazifadan qimmatroq.
- Natijalar 24 soat ichida (ko’pincha ancha erta) elektron pochtaga keladi.
  O’tish bali - **66%**.

## Agar yaxshi ketmasa

Bitta bepul qayta topshirish - uni ertasi kunga emas, ikki-uch haftadan
keyinga band qiling. Ball hisoboti domenlarni ko’rsatadi; weak-domain darsi
to’g’ridan-to’g’ri shunga tegishli. Ikkinchi urinishlarning ko’pi o’tadi va
birinchi urinish - siz topshiradigan eng yaxshi mock imtihon.

## CKA’dan keyin

Sertifikat **ikki yil** amal qiladi. PDF’dan tashqari uning qiymati: endi
siz klasterni boshqara olasiz va o’zingiz qurmagan klaster haqida qanday
savol berishni bilasiz. Keyingi yo’nalish kun bo’yi nima qilishingizga
bog’liq:

| Yo’nalish | Keyingi sertifikat | Bu platformada |
|---|---|---|
| Kubernetes’da ilovalar yozasiz va chiqarasiz | **CKAD** - Pod’lar, config’lar, probe’lar, Job’lar, Helm, Service’lar, NetworkPolicy’lar, dasturchi o’rnidan; 2 soat, 3-8-haftalar bilan kuchli kesishadi | CKAD track’i |
| klasterlarni himoyalaysiz | **CKS** - amaldagi CKA talab qilinadi; klasterni qattiqlashtirish, ta’minot zanjiri, runtime xavfsizligi, admission controller’lar; uchtasining eng qiyini | CKS track’i |
| ostidagi Linux’ni boshqarasiz | **LFCS** - Linux’da storage, tarmoq, foydalanuvchilar, xizmatlar, shell skript yozish; bu track faqat ustidan o’tgan "node nosozliklari"ning yarmi | LFCS track’i |
| productionda ko’p klaster boshqarasiz | bunga imtihon yo’q - GitOps (Argo CD, Flux), kuzatuvchanlik (Prometheus, Loki), multi-klaster, xarajat; DevOps track’ining keyingi modullari | DevOps platformasi |

Va qaysi yo’lni tanlasangiz ham qoladigan odatlar: avval Events’ni o’qish,
bitta narsani o’zgartirish, tekshirish va hech qachon bo’sh fayldan YAML
yozmaslik.

:::tip
Ilhom so’nmasdan turib keyingi narsani rejalashtiring. CKA’dan o’tgan
haftangizda sotib olingan CKAD yoki CKS voucher’i - yigirma haftalik
odatning bug’lanib ketmasligiga ishonch hosil qilishning eng arzon usuli.
:::

## O’zingizni tekshiring

1. Proctor boshlashga ruxsat berishidan oldin xonangiz va stolingiz haqida
   qaysi uchta narsa to’g’ri bo’lishi kerak?
2. Imtihon paytida hujjatlarni qayerdan qidirasiz va nega o’z
   xatcho’plaringiz yordam bermaydi?
3. Keyin qaysi sertifikatni olgan bo’lardingiz va nega?
