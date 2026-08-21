## Sertifikat nima

**Kalitlar juftligi**: siz saqlaydigan yopiq kalit va siz e’lon qiladigan
ochiq kalit. **Sertifikat** - bu o’sha ochiq kalit, ustiga identifikatsiya
(hostname) va client ishonadigan kimningdir - Certificate Authority’ning -
imzosi. TLS undan "bu server haqiqatan ham example.com" ekanini isbotlash
va shifrlashni kelishish uchun foydalanadi.

```
 yopiq kalit (server.key)  ──▶  CSR (so'rov: ochiq kalit + subject)  ──▶  CA imzolaydi  ──▶  sertifikat (server.crt)
        serverda qoladi                     CA'ga yuboriladi                             client'larga tarqatiladi
```

## Yopiq kalit generatsiya qilish

```bash
openssl genrsa -out server.key 2048             # RSA 2048 (uzoqroq muddat uchun 3072/4096)
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out server.key   # zamonaviy shakl
openssl ecparam -genkey -name prime256v1 -out server-ec.key                     # elliptik egri chiziq
chmod 600 server.key                            # DOIMO - o'qish mumkin bo'lgan kalit - buzilgan kalit
openssl rsa -in server.key -noout -text | head  # ko'rib chiqish
openssl rsa -in server.key -pubout -out server.pub   # ochiq kalitni ajratib olish
```

## CSR yaratish

```bash
openssl req -new -key server.key -out server.csr
# Country Name (2 letter code) [AU]:UZ
# ...
# Common Name (e.g. server FQDN) []:www.example.com
```

Interaktiv emas, subject buyruq satrida beriladi:

```bash
openssl req -new -key server.key -out server.csr \
  -subj "/C=UZ/ST=Tashkent/L=Tashkent/O=Example LLC/OU=IT/CN=www.example.com"
openssl req -in server.csr -noout -text        # subject va kalitni tekshirish
openssl req -in server.csr -noout -verify      # imzo o'z-o'ziga mos keladi
```

Zamonaviy brauzerlar CN’ni e’tiborsiz qoldiradi va **Subject Alternative
Names** talab qiladi:

```bash
openssl req -new -key server.key -out server.csr \
  -subj "/CN=www.example.com" \
  -addext "subjectAltName=DNS:www.example.com,DNS:example.com,IP:10.0.0.5"
```

## O’zi imzolagan sertifikatlar

Ichki service’lar va lablar uchun - CA ishtirok etmaydi, shuning uchun
client’larga unga ishonishni ochiq aytish kerak:

```bash
openssl req -x509 -newkey rsa:2048 -nodes -keyout server.key -out server.crt \
  -days 365 -subj "/CN=server.internal" -addext "subjectAltName=DNS:server.internal"
```

`-x509` "so’rov emas, sertifikat chiqar" degani; `-nodes` "yopiq kalitni
shifrlama" degani (nazoratsiz ishga tushadigan service uchun kerak);
`-days` amal qilish muddatini belgilaydi. Bitta buyruq, kalit ham,
sertifikat ham.

CSR’ni o’zingizning kichik CA’ngiz bilan imzolash uchun:

```bash
openssl req -x509 -newkey rsa:4096 -nodes -keyout ca.key -out ca.crt -days 3650 -subj "/CN=My Internal CA"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365 \
  -extfile <(printf "subjectAltName=DNS:www.example.com")
```

## Sertifikatni o’qish

```bash
openssl x509 -in server.crt -noout -text                    # hammasi
openssl x509 -in server.crt -noout -subject -issuer -dates  # uchta savol: kim, kim tomonidan, qachongacha
# subject=CN = www.example.com
# issuer=CN = My Internal CA
# notBefore=Aug 21 10:00:00 2026 GMT
# notAfter=Aug 21 10:00:00 2027 GMT
openssl x509 -in server.crt -noout -ext subjectAltName
openssl x509 -in server.crt -noout -fingerprint -sha256
openssl x509 -in server.crt -noout -checkend 2592000        # 30 kun ichida muddati tugaydimi? exit 1 = ha
```

**Kalit va sertifikat bir-biriga mos keladimi?** Ochiq kalit hash’larini
solishtiring - bu uchtasi farq qilsa, service ishga tushishdan bosh
tortadi:

```bash
openssl x509 -in server.crt -noout -modulus | openssl sha256
openssl rsa  -in server.key -noout -modulus | openssl sha256
openssl req  -in server.csr -noout -modulus | openssl sha256
```

## Jonli serverni tekshirish

```bash
openssl s_client -connect example.com:443 -servername example.com </dev/null
openssl s_client -connect example.com:443 -showcerts </dev/null | openssl x509 -noout -dates
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -subject -issuer -dates
curl -vI https://example.com                    # curl sertifikat zanjirini va har qanday xatoni ko'rsatadi
```

## Formatlar va konvertatsiya

| Format | Kengaytma | Nima |
|---|---|---|
| PEM | `.pem` `.crt` `.key` `.csr` | `-----BEGIN ...-----` qatorlari orasidagi base64 matn - Linux’dagi sukut bo’yicha format |
| DER | `.der` `.cer` | binar |
| PKCS#12 | `.p12` `.pfx` | kalit + sertifikat + zanjir bitta parol bilan himoyalangan faylda (Windows, Java) |

```bash
openssl x509 -in cert.der -inform DER -out cert.pem -outform PEM
openssl pkcs12 -export -out bundle.p12 -inkey server.key -in server.crt -certfile ca.crt
openssl pkcs12 -in bundle.p12 -nodes -out all.pem
```

## Ular qayerda turadi va CA’ga ishonish

```bash
/etc/ssl/certs/      /etc/ssl/private/          # Debian/Ubuntu
/etc/pki/tls/certs/  /etc/pki/tls/private/      # RHEL oilasi

sudo cp my-ca.crt /usr/local/share/ca-certificates/my-ca.crt && sudo update-ca-certificates   # Debian
sudo cp my-ca.crt /etc/pki/ca-trust/source/anchors/ && sudo update-ca-trust                    # RHEL
```

:::warning
Yopiq kalitlar `chmod 600` bo’ladi, egasi root yoki service user’i bo’ladi
va host’dan hech qachon chiqmaydi. Git’ga commit qilingan yoki chat orqali
uzatilgan kalit - buzilgan kalit: bekor qiling va qayta chiqaring.
`-nodes` (parol iborasi yo’q) serverlar uchun odatiy holat, aynan shuning
uchun butun yuk fayl ruxsatlari zimmasiga tushadi.
:::

:::exam-tip
Ehtimoliy topshiriqlar: berilgan subject bilan kalit va CSR generatsiya
qilish (`openssl genrsa` + `openssl req -new -subj`), N kun amal qiladigan
o’zi imzolagan sertifikat yaratish (`openssl req -x509 -days N -nodes`) va
sertifikatning subject/issuer/muddatini o’qish (`openssl x509 -noout -subject
-issuer -dates`). Shu uchta buyruq shaklini yodlang; qolganini
`man openssl-req` va `man openssl-x509` to’ldiradi.
:::

## O’zingizni tekshiring

1. CSR qaysi uchta narsani o’z ichiga oladi va CA nimani qo’shadi?
2. Yopiq kalit bilan sertifikat bir-biriga tegishli ekanini qanday
   tekshirasiz?
3. Qaysi buyruq sertifikatning muddati tugash sanasini ko’rsatadi va qaysi
   biri jonli serverning sertifikatini sinaydi?
