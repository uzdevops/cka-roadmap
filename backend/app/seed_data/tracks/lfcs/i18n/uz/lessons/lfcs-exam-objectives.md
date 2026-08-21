## Oldindan talab qilinadigan bilimlar

Rasmiy talab yo’q. Amalda esa 1-haftagacha siz terminal ocha olishingiz,
`cd` va `ls` bilan harakatlana olishingiz va *biror* editor bilan fayl
tahrirlay olishingiz kerak. Agar `vi` yangi bo’lsa, 2-haftadagi dars omon
qolish uchun yetarlicha beradi; agar shell butunlay yangi bo’lsa, avval
istalgan boshlang’ich darslikka bir kun ajrating - bu yo’nalish "buyruq
yoza olasiz" nuqtasidan boshlanadi va tez harakatlanadi.

Mashq qilish uchun bitta mashina kerak: yangi **Ubuntu LTS** - imtihon
distributivi - ishlab turgan virtual mashina (VirtualBox, KVM, bulut
instance’i), unda sizda `sudo` bo’lsin va uni buzishdan qo’rqmang.
Ayniqsa 11-hafta (storage) va 10-hafta (firewall) oldidan uning
snapshot’ini oling.

## Imtihon, raqamlarda

| | |
|---|---|
| Format | amaliy, masofadagi Linux tizimida brauzerdagi terminal orqali; bir nechta topshiriq ikkinchi host’ni talab qilishi mumkin |
| Davomiyligi | **2 soat** |
| Topshiriqlar | taxminan 15-20 ta, og’irlik bilan |
| O’tish bali | **66%** |
| Distributiv | Ubuntu LTS (aniq relizni joriy handbook’dan tekshiring) |
| Ma’lumot manbai | **faqat imtihon tizimidagi `man` sahifalari va `--help`** - brauzer yo’q, hujjatlar sayti yo’q |
| Proctoring | masofadan, veb-kamera, toza stol, ID |
| Qayta topshirish | bitta bepul qayta topshirish kiradi |
| Amal qilish muddati | 3 yil |

"Hujjatlar sayti yo’q" qoidasi - Kubernetes imtihonlaridan eng katta farq:
sizga faqat `man` beriladi. Shuning uchun bu yerdagi har bir dars ochish
kerak bo’lgan `man` sahifasini ko’rsatadi va shuning uchun tizim hujjatlari
darsi shu haftada turadi.

## Maqsadlar

Linux Foundation sohalarni bir satrli kompetensiyalar ro’yxati sifatida
e’lon qiladi ("Create, delete, copy, and move files and directories";
"Configure packet filtering"). Bu yo’nalishning dars sarlavhalari **aynan**
o’sha satrlar, har bir darsga bittadan, sohalar ro’yxatidagi tartibda.
Rasmiy ro’yxatni o’qib, har bir satr uchun qanday buyruqlar yozishingizni
ayta olsangiz - tayyorsiz; va ro’yxat - imtihondan oldingi kechada qayta
o’qiladigan narsa.

## Unda nima yo’q

Yo’q: desktop muhitlari, shell skriptlardan nariga o’tgan dasturlash,
muayyan bulut provayderlari, Kubernetes, ma’lumotlar bazalari, mail
server’lar, veb-ilova stack’lari. Agar bu yerdagi dars maqsad satridan
uzoqroqqa ketsa, buni aytadi; ortiqchasi - kontekst, imtihon materiali
emas.

## Ro’yxatdan o’tish va imtihon kuni

Xarid imtihonni va bitta qayta topshirishni o’z ichiga oladi, bir yil amal
qiladi; sanani alohida band qilasiz. Oldindan tizim tekshiruvini
o’tkazing, band qilishga mos ID tayyorlang, stolni tozalang. 13-haftadagi
xulosa darsida to’liq ro’yxat bor; hozircha shuni bilib qo’ying: terminal
brauzerda va copy/paste uning ichida ishlaydi.

:::tip
Beshta soha nomini kartochkaga yozing va har haftani tugatganingizda u
qamrab olgan maqsad satrlarini belgilab boring. Ko’rinadigan progress o’n
uch haftani harakatda tutadi, kartochka esa sizning takrorlash varag’ingiz.
:::

## O’zingizni tekshiring

1. Imtihon davomida qanday ma’lumot manbai mavjud va bu o’qish uslubingiz
   uchun nimani anglatadi?
2. Imtihonning davomiyligi va o’tish bali qancha?
3. LFCS’da **bo’lmagan** ikkita narsani ayting.
