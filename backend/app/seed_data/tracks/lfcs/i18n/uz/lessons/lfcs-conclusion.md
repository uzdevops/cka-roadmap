## Band qilish

- LFCS’ni training.linuxfoundation.org saytidan sotib oling. Xarid bitta
  **bepul qayta topshirishni** o’z ichiga oladi va bir yil amal qiladi;
  imtihon sanasi portalda alohida band qilinadi.
- Kunning o’zingiz tetik bo’ladigan vaqtiga, ikki-uch hafta oldinga band
  qiling - shunda sana haqiqiy bo’ladi va takrorlashning muddati paydo
  bo’ladi.
- Undan oldingi haftada **Candidate Handbook** va **Important
  Instructions** sahifasini o’qing - ruxsat etilgan materiallar, ID
  talablari va xona qoidalari o’zgarib turadi.

## Bir kun oldin

- **Tizim tekshiruvini** (brauzer, veb-kamera, mikrofon, ekranni
  ulashish) o’zingiz ishlatadigan mashina va tarmoqda o’tkazing.
- Ismi band qilishga aynan mos keladigan davlat **ID**’si.
- Tinch xonada **toza stol**: qog’oz yo’q, telefon yo’q, ikkinchi ekran
  yo’q. Proctor sizdan xonani va stolni ko’rsatishni so’raydi.
- Maqsadlar ro’yxatini va mock’dagi xatolar jadvalingizni ko’zdan
  kechiring. Yangi hech narsa o’rganmang. Uxlang.

## Imtihon kuni

- **30 daqiqa oldin** kiring; shaxsni va xonani tekshirish vaqt oladi.
- Muhit - jonli Ubuntu tizimidagi terminal. Ma’lumot manbaingiz - `man`,
  `info` va `--help`, boshqa hech narsa emas. Copy va paste muhit ichida
  ishlaydi.
- Nolinchi daqiqa: `whoami`, `hostname`, `lsblk`, `ip a`. Mashinani
  o’zgartirishdan oldin qaysi mashinada ekaningizni biling.
- Har bir topshiriq: **ikki marta o’qing** ("doimiy", "barcha userlar",
  "o’zgartirmasdan" so’zlariga e’tibor bering), bajaring, **tekshiring**,
  keyingisiga o’ting. O’tkazib yuborganlaringiz uchun qoralamadan
  foydalaning.
- Besh daqiqada qimirlamagan topshiriq: uni tashlang, keyin qayting.
  Qisman ball bor; qo’l tegmagan oson topshiriqda esa yo’q.
- Soat tugashidan oldin oxirgi besh daqiqani doimiylik ro’yxatini qayta
  tekshirishga sarflang: fstab, `systemctl is-enabled`, `sysctl`,
  firewall `--permanent`, crontab.
- Natijalar email orqali, odatda 24 soat ichida keladi. O’tish - 66%.

## Agar yaxshi ketmasa

Bitta bepul qayta topshirish bor. Uni ertasi kuniga emas, ikki-uch hafta
keyinga band qiling. Ball hisoboti sohalar bo’yicha ajratib beradi;
13-haftadagi mock xatolari usuli bunga to’g’ridan-to’g’ri qo’llanadi.
Ikkinchi urinishlarning ko’pchiligi o’tadi, birinchi urinish esa - siz
topshiradigan eng aniq mock imtihon.

## Endi nima qila olasiz

O’n uch hafta oldin maqsadlar ro’yxati notanish iboralar ro’yxati edi.
Endi siz Linux tizimini o’rnata, sozlay va tuzata olasiz: storage’ni
partition qilib kengaytirish, uni tarmoqqa ulash, trafigini filtrlash,
service’larni ishga tushirish va yozish, undan foydalanadigan odamlarni
boshqarish va bularning biri to’xtaganda sababini topish. Ish - shu,
sertifikat esa faqat kvitansiya.

## LFCS’dan keyin

Sertifikat **uch yil** amal qiladi. Keyingi yo’nalish kun bo’yi nima
qilishingizga bog’liq:

| Yo’nalish | Keyingisi | Shu platformada |
|---|---|---|
| shu mashinalarda konteynerlar va klasterlar ishlatasiz | **CKA** - Kubernetes administrator imtihoni; har bir "node’ga ssh qiling va kubelet logini o’qing" topshirig’i - LFCS ko’nikmasi | CKA yo’nalishi |
| Kubernetes ustida ilovalar qurib jo’natasiz | **CKAD** | CKAD yo’nalishi |
| klasterlarni himoyalaysiz | **CKS** (joriy CKA talab qilinadi) | CKS yo’nalishi |
| chuqurroq Linux muhandislik imtihonini xohlaysiz | **LFCE** - Linux Foundation Certified Engineer | - |
| yuqoridagilarning barchasini avtomatlashtirasiz | Ansible, Terraform, CI/CD, GitOps - boshlash uchun imtihon shart emas | DevOps platformasi |

Bu yerdan tabiiy keyingi qadam - **CKA**: u aynan sizda hozir bor
Linux’ni nazarda tutadi va ikkala sertifikat birgalikda zamonaviy
infratuzilmani boshidan oxirigacha yurita oladigan odamni tasvirlaydi.

Odatlar esa baribir o’zi bilan qoladi: xatoni o’qing, bitta narsani
o’zgartiring, uni tekshiring va doimiy qiling.

:::tip
Keyingi narsani o’tgan haftangizning o’zida band qiling. Impuls saqlanib
turganda sotib olingan CKA voucher’i - o’n uch haftalik odat so’nib
ketmasligiga ishonch hosil qilishning eng arzon yo’li.
:::

## O’zingizni tekshiring

1. Proctor sizga boshlashga ruxsat berishidan oldin xonangiz va ID’ngiz
   haqida nima to’g’ri bo’lishi kerak?
2. Imtihon davomida ma’lumot manbaingiz nima va bu ishlash uslubingizda
   nimani o’zgartiradi?
3. Keyingi qaysi sertifikatni topshirasiz va uni qachon band qilasiz?
