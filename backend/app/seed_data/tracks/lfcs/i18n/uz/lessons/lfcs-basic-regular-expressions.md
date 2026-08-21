## Pattern’lar uchun grammatika

Muntazam ifoda satrlar to’plamini tasvirlaydi. `grep`, `sed`, `awk`,
`vi`’ning `/` va `:s`, `less`, `find -regex` - hammasi shu tilda gapiradi.
**Oddiy** muntazam ifodalar (BRE) - `grep` va `sed` sukut bo’yicha
ishlatadigani; keyingi dars kengaytirilgan operatorlarni qo’shadi. Bu
dars esa - hammaga kerak bo’ladigan asos.

## Harfma-harf belgilar va nuqta

| Pattern | Nimaga mos keladi |
|---|---|
| `cat` | qatorning istalgan joyida ketma-ket kelgan c, a, t belgilari |
| `c.t` | c, **istalgan bitta belgi**, t: `cat`, `cut`, `c3t`, `c t` |
| `c\.t` | c, harfma-harf nuqta, t |

Regexda ma’noga ega belgilar - `. * [ ] ^ $ \` - harfma-harf bo’lishi
uchun backslash talab qiladi. Qolgan hammasi o’zicha.

## Anchor’lar

| Pattern | Nimaga mos keladi |
|---|---|
| `^root` | qator **boshidagi** `root` |
| `bash$` | **oxiridagi** `bash` |
| `^$` | bo’sh qator |
| `^#` | izoh qatori |
| `^\s*$` | bo’sh ko’ringan qator (faqat probel/tab; `\s` - GNU kengaytmasi) |

```bash
grep '^root' /etc/passwd
grep 'bash$' /etc/passwd
grep -v '^#' /etc/ssh/sshd_config | grep -v '^$'
```

## Belgi sinflari: to’plamdan bitta belgi

| Pattern | Qanday bitta belgiga mos keladi |
|---|---|
| `[abc]` | a, b yoki c |
| `[a-z]`, `[A-Z]`, `[0-9]`, `[a-zA-Z0-9]` | diapazondagi belgi |
| `[^0-9]` | raqam **bo’lmagan** belgi (qavs ichidagi `^` inkor qiladi) |
| `[[:digit:]]`, `[[:alpha:]]`, `[[:alnum:]]`, `[[:space:]]`, `[[:upper:]]`, `[[:lower:]]`, `[[:punct:]]` | POSIX nomli sinflar - locale uchun xavfsiz |
| `[.]`, `[$]` | harfma-harf nuqta / dollar (ko’p metabelgilar qavs ichida ma’nosini yo’qotadi) |

```bash
grep '^[A-Z]' file                 # bosh harf bilan boshlanadigan qatorlar
grep '[0-9][0-9][0-9]' file        # ketma-ket uchta raqam
grep 'gr[ae]y' file                # gray yoki grey
grep '^[^#]' file                  # birinchi belgisi # bo'lmagan qatorlar
```

## Takrorlash: oldingi narsadan nechta

| BRE | Ma’nosi |
|---|---|
| `*` | oldingi elementdan **nol yoki undan ko’p** |
| `\+` | bir yoki undan ko’p (BRE’dagi GNU kengaytmasi; `+` - kengaytirilgan) |
| `\?` | nol yoki bitta (GNU; `?` - kengaytirilgan) |
| `\{n\}` | aynan n ta |
| `\{n,\}` | n yoki undan ko’p |
| `\{n,m\}` | n va m orasida |

`*` **o’zidan oldingi bitta elementga** tegishli: `ab*` - bu `a`, keyin
istalgan sondagi `b` (`a`, `ab`, `abbb`) - "ab takrorlangan" emas. `.*` -
"istalgan narsa, istalgan uzunlikda" - eng keng tarqalgan idioma.

```bash
grep 'ab*c' file                    # ac, abc, abbc...
grep 'colou\?r' file                # color, colour
grep '^[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}$' ips     # IPv4 ko'rinishi
grep 'error.*timeout' log           # bir qatorda error, keyinroq timeout
grep '^.\{80,\}' file               # 80+ belgi uzunlikdagi qatorlar
grep '^-' file                      # tire bilan boshlanadigan qatorlar (qator boshida ^ dan keyin escape shart emas; yoki -e ishlating)
```

## Guruhlar va orqaga havolalar

| BRE | Ma’nosi |
|---|---|
| `\(...\)` | guruh (BRE’da "guruh" ma’nosini berish uchun qavslar escape qilinadi) |
| `\1`, `\2` | 1- va 2-guruh nimaga mos kelgani - shu pattern ichida yoki sed’ning almashtirish qismida |
| `\<word\>`, `\bword\b` | so’z chegaralari (GNU) |

```bash
grep '\(ab\)\{2\}' file             # abab
grep '\([a-z]\)\1' file             # takrorlangan harf: ll, ss, oo
sed 's/\([0-9]*\)-\([0-9]*\)/\2-\1/' file      # tire atrofidagi ikki sonni almashtirish
sed -n 's/^User=\(.*\)$/\1/p' unit.service      # User= dan keyingi qiymatni ajratib olish
grep '\<cat\>' file                 # so'z sifatida cat (grep -w cat bilan bir xil)
```

## To’g’ri qilish kerak bo’lgan beshta narsa

1. Pattern’ni bitta tirnoq ichiga **oling**.
2. `.` - istalgan belgi; `\.` - nuqta.
3. `*` - "oldingisidan nol yoki undan ko’p", `.*` esa - "istalgan narsa".
4. `^`/`$` bog’laydi; `[^...]` sinfni inkor qiladi.
5. **BRE**’da `+ ? { } ( ) |` - harfma-harf belgilar va operator bo’lishi
   uchun `\` talab qiladi - yoki ular `\`’siz operator bo’lgan `grep -E`’dan
   (keyingi dars) foydalaning.

:::exam-tip
Imtihondagi ko’pchilik regex - anchor va sinf bilan `grep`: raqam bilan
boshlanadigan qatorlar (`'^[0-9]'`), `.conf` bilan tugaydigan qatorlar
(`'\.conf$'`), izoh bo’lmagan qatorlar (`'^[^#]'`). Pattern’ni avval
ekranda sinab ko’ring, keyin yo’naltiring. Pattern’ga `+` yoki `|` kerak
bo’lganda `grep -E`’ga o’ting - backslash’lar yo’qoladi.
:::

## O’zingizni tekshiring

1. `ab*c` nimaga mos keladi va nimaga mos kelmaydi?
2. Raqam bilan boshlanib, nuqtali vergul bilan tugaydigan qatorlar uchun
   BRE yozing.
3. BRE’da "bir yoki undan ko’p raqam"ni qanday yozasiz?
