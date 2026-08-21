## Muammo: hech qachon ko’rmagan odamga sir yuborish

Siz veb-saytga parol yozasiz. U siz nazorat qilmaydigan o’nlab tarmoqdan
o’tadi. Buning xavfsiz bo’lishi uchun ikki narsa to’g’ri bo’lishi shart:
yo’ldagi hech kim uni o’qiy olmasin va narigi uchdagi sayt haqiqatan ham
bank bo’lsin, o’zini bank qilib ko’rsatayotgan kimdir emas. TLS ikkalasini
ham hal qiladi va u ishlatadigan qismlar - aynan Kubernetes o’z komponentlari
orasida ishlatadigan qismlar.

## Simmetrik shifrlash

Bitta kalit, ham qulflash, ham ochish uchun ishlatiladi. Tez va yaxshi -
**agar** ikkala tomonda ham kalit allaqachon bo’lsa. Qiyinchilik shunda:
kalitni ochiq holda yubormasdan, ya’ni tinglovchi uni ilib olmaydigan qilib,
narigi tomonga qanday yetkazasiz?

## Assimetrik shifrlash: kalitlar juftligi

Kalitlar juftligi: siz saqlaydigan **yopiq kalit** va siz tarqatadigan
**ochiq kalit**. Ochiq kalit bilan shifrlangan narsani faqat yopiq kalit
bilan deshifrlash mumkin.

```bash
openssl genrsa -out my.key 2048            # yopiq kalit
openssl rsa -in my.key -pubout > my.pem    # undan olingan ochiq kalit
```

Endi sir almashish muammosi hal bo’ldi: server o’z ochiq kalitini e’lon
qiladi; client simmetrik kalit o’ylab topadi, uni serverning ochiq kaliti
bilan shifrlab yuboradi; uni faqat server deshifrlay oladi; endi ikkalasida
ham suhbatning qolgan qismi uchun umumiy simmetrik kalit bor. (Bu - umumiy
shakl; zamonaviy TLS kalitga kelishuv variantidan foydalanadi, lekin rollar
o’sha-o’sha.)

O’sha juftlik teskari yo’nalishda **imzolash** uchun ishlaydi: yopiq kalit
bilan shifrlangan narsani ochiq kaliti bor har kim deshifrlay oladi - bu uning
yopiq kalit egasidan kelganini isbotlaydi. SSH kalitlari shuni qiladi va
sertifikat imzosi ham aynan shu.

## Bo’shliq: bu kimning ochiq kaliti?

Buzg’unchi *o’zining* ochiq kalitini e’lon qilib, o’zini bank deb atashi
mumkin. Client ochiq kalit haqiqatan `bank.com`’ga tegishli ekanini bilishi
kerak. **Sertifikat** - bu ochiq kalit, ustiga nom, ustiga **client allaqachon
ishonadigan kimningdir imzosi** bo’lib, o’sha imzo "bu kalit shu nomga
tegishli" deydi.

```
sertifikat = { ochiq kalit, subject (nom), amal qilish sanalari, issuer } CA'ning yopiq kaliti bilan imzolangan
```

"Client allaqachon ishonadigan kimdir" - bu **Certificate Authority**. Uning
o’z sertifikati (ya’ni ochiq kaliti) clientga oldindan o’rnatilgan bo’ladi -
brauzeringiz yuzlab shundaylar bilan keladi; Kubernetes komponentiga esa
kubeconfig’ida klaster CA’sining `ca.crt` fayli beriladi. Client serverning
sertifikatidagi imzoni CA’ning ochiq kaliti bilan tekshiradi, nom o’zi
yetmoqchi bo’lgan nomga mos kelishini tekshiradi, sanalarni tekshiradi va
faqat shundan keyin ichidagi ochiq kalitga ishonadi.

```bash
openssl req -new -key my.key -subj "/CN=my-server" -out my.csr     # CSR: "shu nom uchun bu ochiq kalitni imzolang"
openssl x509 -req -in my.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out my.crt -days 365
```

O’z sertifikatini o’zi imzolaydigan CA - **root CA**; kubeadm’ning klaster
CA’si ana shunday. Haqiqiy dunyodagi CA’lar serverlarni imzolaydigan oraliq
CA’larni imzolaydi - zanjir hosil bo’ladi - lekin har bir bo’g’inda tekshiruv
bir xil.

## Handshake, tartib bilan

1. Client ulanadi; qaysi TLS versiyalari va shifrlarni qo’llashini aytadi.
2. Server o’z **sertifikatini** yuboradi.
3. Client sertifikatni tekshiradi: ishonchli CA imzolaganmi, nom mos
   keladimi, muddati o’tmaganmi.
4. Serverning ochiq kaliti yordamida kalit almashinuvi; ikkala tomon ham
   **simmetrik sessiya kalitini** hosil qiladi.
5. Shundan keyingi hamma narsa simmetrik shifrlanadi.

Ixtiyoriy ravishda, 2-3-qadamda server clientdan ham sertifikat so’rashi va
uni xuddi shu tarzda tekshirishi mumkin - bu **mutual TLS**. Kubernetes buni
hamma joyda qiladi: API server kubelet’ning client sertifikatini tekshiradi,
kubelet esa API serverning server sertifikatini tekshiradi.

## Ko’radigan fayl nomlari

| Kengaytma / nom | Odatda |
|---|---|
| `.key`, `-key.pem` | yopiq kalit - hech qachon ulashmang, hech qachon commit qilmang |
| `.crt`, `.pem`, `.cer` | sertifikat (ochiq) |
| `.csr` | sertifikat imzolash so’rovi |
| `ca.crt` | CA sertifikati - client’lar ishonadigan narsa |
| `ca.key` | CA’ning yopiq kaliti - control plane’dagi eng nozik fayl |

:::exam-tip
Sizdan TLS’ni tushuntirish so’ralmaydi. Sizdan kalit va CSR generatsiya
qilish (`openssl genrsa`, `openssl req -new`), sertifikatni o’qish
(`openssl x509 -text -noout`) va shu xatolarni tanib olish so’raladi:
`x509: certificate signed by
unknown authority` (kubeconfig yoki komponent flagida noto’g’ri CA) va `certificate
has expired`. Bu sahifadagi uchta openssl buyrug’i - butun asboblar to’plami.
:::

## O’zingizni tekshiring

1. Assimetrik shifrlash simmetrik shifrlash hal qila olmaydigan qanday
   muammoni hal qiladi?
2. Sertifikat qaysi uch narsani bir-biriga bog’laydi va bu bog’lanishga kim
   kafil bo’ladi?
3. API server bilan kubelet orasidagi mutual TLS’da qaysi sertifikatlar va
   kim tomonidan tekshiriladi?
