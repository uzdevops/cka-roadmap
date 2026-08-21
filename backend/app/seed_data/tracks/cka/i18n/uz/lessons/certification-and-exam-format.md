## CKA aslida nima

Certified Kubernetes Administrator - **amaliyotga asoslangan** imtihon:
variantli savollar yo’q. Sizga terminal, bir nechta haqiqiy klaster va
vazifalar ro’yxati beriladi - buni yarat, buni tuzat, bu nega ishlamayotganini
aniqla - va vaqt to’xtaganda klasterlarning holati bo’yicha baholanasiz.

| | |
|---|---|
| Format | Amaliy, brauzerdagi masofaviy ish stolida |
| Davomiyligi | 2 soat |
| Vazifalar | 15-20 ta, har biri har xil og’irlikda |
| O’tish bali | 66 % |
| Qayta topshirish | Bitta bepul qayta topshirish kiradi |
| Amal qilish muddati | 2 yil |
| Ruxsat etilgan manbalar | kubernetes.io/docs, kubernetes.io/blog, helm.sh/docs, kubernetes.github.io/ingress-nginx, gateway-api.sigs.k8s.io |

Ruxsat etilgan manbalar qatori ko’ringanidan muhimroq: imtihon paytida rasmiy
hujjatlarni ocha olasiz - va ochishingiz kerak. Qila olmaydiganingiz - uni
qidirib o’n daqiqa yo’qotish. Imtihon mukofotlaydigan ko’nikma - sizga *qaysi
sahifa* kerakligini bilish va to’g’ridan-to’g’ri o’sha yerga borish.

## Domenlar va ularning og’irliklari

| Domen | Og’irlik |
|---|---|
| Nosozliklarni bartaraf etish | 30 % |
| Klaster arxitekturasi, o’rnatish va sozlash | 25 % |
| Service’lar va tarmoq | 20 % |
| Workload’lar va rejalashtirish | 15 % |
| Saqlash | 10 % |

Bu og’irliklarni o’quv rejasi sifatida o’qing. Nosozliklarni bartaraf etish va
klaster administratsiyasi birgalikda ballarning yarmidan ko’pi - aynan shuning
uchun bu yo’l xaritasi keyingi bosqichlarini o’sha yerga sarflaydi va mock
imtihonlar ham o’sha tomonga og’adi.

:::exam-tip
Har bir vazifa qaysi klasterdan foydalanishni aytadi - `kubectl config
use-context <name>` har bir javobning birinchi qatori. Uni o’tkazib yuborish -
aslida yechgan vazifangizni yo’qotishning eng keng tarqalgan usuli.
:::

## Imtihon qanday baholanadi

Har bir vazifa belgilangan foizga ega. Vazifa ichida qisman ball bor: agar
savolda 80-portda ochilgan, uchta replikali Deployment so’ralsa va siz
Deployment’ni to’g’ri qilib, Service’ni noto’g’ri qilsangiz, Deployment’ning
ulushi sizda qoladi. Bundan ikkita xulosa:

- **Har bir vazifaning oson qismini bajaring.** Bitta ichki qadam qiyin
  ko’ringani uchun vazifaga umuman tegmasdan qoldirmang.
- **Belgilang va oldinga o’ting.** Interfeys vazifani belgilash imkonini
  beradi; 9 % lik savol kutib turganda 4 % lik savol o’n ikki daqiqaga
  arzimaydi.

## Yaxshi imtihon soati qanday ko’rinadi

1. Birinchi o’tish - har bir vazifani o’qing, uch daqiqadan kam vaqtda
   tugata oladiganlaringizni bajaring, qolganini belgilab qo’ying. Ko’p
   nomzodlar shu yerda ballarning 40 % ini oladi.
2. Ikkinchi o’tish - belgilangan vazifalar, eng qiyini oxirida.
3. Oxirgi o’n daqiqa - yaratgan har bir obyektingiz haqiqatan ham to’g’ri
   klasterda, to’g’ri namespace’da mavjudligini qayta tekshiring. Har bir
   kontekstda `kubectl get all -A` - arzon sug’urta.

:::tip
Terminalni birinchi daqiqada sozlang: `alias k=kubectl`, `export
do="--dry-run=client -o yaml"` va `export now="--force --grace-period 0"` -
o’zini oqlaydigan uchtasi. Imtihon muhiti `.bashrc`’ni tahrirlashga ruxsat
beradi.
:::

## Bu yo’l xaritasi unga qanday mos keladi

Yigirma hafta, o’n bitta bosqich - tuzilgan video kursdan oladigan tartibda,
lekin platformaning o’z ritmi bilan: dushanbadan jumagacha darslar, shanbada
lab, yakshanbada takrorlash testi. Dashboard’dagi tayyorlik ballari yuqoridagi
jadval bo’yicha og’irlangan, shuning uchun u "qancha o’qidim" degan emas,
"imtihonni band qila olamanmi" degan savolga javob beradi.

## O’zingizni tekshiring

1. Vazifa 7 % turadi va uchta narsa so’raydi; siz faqat ikkitasini qila
   olasiz. Nima qilasiz va nega?
2. Qaysi ikki domen birgalikda ballarning yarmidan ko’pini tashkil qiladi?
3. Har bir vazifa uchun yozadigan eng birinchi buyruq qaysi?
