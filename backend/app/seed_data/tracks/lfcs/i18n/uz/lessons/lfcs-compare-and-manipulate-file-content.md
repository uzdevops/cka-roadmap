## Matn vositalari to’plami

Konfiguratsiya, loglar, CSV eksportlari, buyruq chiqishi - Linux’da
bularning hammasi matn va bir-biriga pipe qilingan shu kichik buyruqlar
elektron jadval yoki skript bajaradigan ishning ko’pini qiladi. Ularni
fe’l sifatida o’rganing: ko’rsat, kes, sarala, sana, almashtir,
solishtir.

## Ko’rsatish

```bash
cat file                      # butun fayl; cat a b > c ularni qo'shadi
cat -n file                   # raqamlangan satrlar; -A tab va satr oxirlarini ko'rsatadi
tac file                      # teskari tartibda
head -n 5 file; head -5 file  # birinchi satrlar (sukut bo'yicha 10)
tail -n 5 file; tail -f /var/log/syslog   # oxirgi satrlar; -f o'sishni kuzatadi; -F rotatsiyadan keyin ham ishlaydi
tail -n +20 file              # 20-satrdan oxirigacha
less file                     # sahifalab ko'rish (keyingi dars)
wc -l file; wc -w; wc -c      # satrlar, so'zlar, baytlar
```

## Kesib olish

```bash
cut -d: -f1 /etc/passwd               # ikki nuqta bilan ajratilgan 1-maydon
cut -d: -f1,7 /etc/passwd             # 1 va 7-maydonlar
cut -d, -f2- data.csv                 # 2-maydondan boshlab
cut -c1-10 file                       # 1-10 belgilar
awk -F: '{print $1, $3}' /etc/passwd  # cut yetmaganda: raqam bo'yicha maydonlar, istalgan ajratgich, shartlar
awk -F: '$3 >= 1000 {print $1}' /etc/passwd        # uid >= 1000 bo'lgan userlar
awk '{print $NF}' file                # oxirgi maydon
```

`cut` bitta belgidan iborat ajratgichni talab qiladi va ketma-ket bo’sh
joylar bilan yaxshi ishlay olmaydi; `awk` sukut bo’yicha bo’sh joy
bo’yicha ajratadi hamda tekshirish va hisoblash qila oladi.

## Saralash va sanash

```bash
sort file                 # alifbo bo'yicha
sort -n file              # raqamli
sort -r file              # teskari
sort -k2 file             # 2-maydon bo'yicha (bo'sh joy bilan ajratilgan)
sort -t: -k3 -n /etc/passwd        # 3-maydon bo'yicha, raqamli, ikki nuqta ajratgich
sort -u file              # takrorlanmas (saralangan)
sort -h sizes             # inson o'qiydigan hajmlar: 1K 2M 3G
uniq file                 # faqat YONMA-YON dublikatlarni yig'adi - avval sort qiling!
uniq -c file              # sanoq bilan
uniq -d file              # faqat takrorlangan satrlar
uniq -u                   # faqat noyoblari
sort file | uniq -c | sort -rn | head      # klassik "eng ko'p uchraydigan N ta"
```

```bash
cut -d' ' -f1 access.log | sort | uniq -c | sort -rn | head -5     # eng ko'p uchragan 5 ta klient IP
awk '{print $9}' access.log | sort | uniq -c                        # HTTP status sanoqlari
```

## O’zgartirish

```bash
tr a-z A-Z < file                 # belgilarni almashtiradi
tr -d '\r' < dos.txt > unix.txt   # belgilarni o'chiradi
tr -s ' ' < file                  # takrorlarni siqadi
tr ':' '\t' < /etc/passwd
sed 's/old/new/' file             # har bir satrdagi birinchi uchrashi, stdout ga
sed 's/old/new/g' file            # har bir uchrashi
sed -i 's/old/new/g' file         # joyida (-i.bak backup qoldiradi)
sed -n '10,20p' file              # faqat 10-20 satrlarni chop etadi
sed '/^#/d' file                  # izoh satrlarini o'chiradi
sed '/^$/d' file                  # bo'sh satrlarni o'chiradi
sed -i 's/^#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed 's#/old/path#/new/path#g'     # naqshda slash bo'lganda istalgan ajratgich
```

`sed` - skriptlar uchun satr muharriri: `s/pattern/replacement/flags`,
adreslar (`10,20`, `/regex/`), `d` o’chiradi, `-n` bilan `p` chop etadi,
`-i` esa faylga qaytarib yozadi.

```bash
paste a.txt b.txt                 # yonma-yon, tab bilan ajratilgan
paste -d, a b
join -t: a.txt b.txt              # umumiy birinchi maydon bo'yicha birlashtiradi (ikkalasi saralangan)
split -l 1000 big.log part_       # 1000 satrli fayllarga bo'ladi
rev file; nl file; fold -w 80 file; column -t file; expand/unexpand
```

## Solishtirish

```bash
diff a.conf b.conf                # ed uslubida: 3c3 (o'zgargan), 5a6 (qo'shilgan), 8d7 (o'chirilgan)
diff -u a.conf b.conf             # unified: kontekst bilan -/+ satrlar - patch va git ko'rsatadigani
diff -r dir1 dir2                 # directory'lar
diff -q a b                       # faqat "farq qiladi" yoki hech narsa
diff -y a b; sdiff a b            # yonma-yon
cmp a.bin b.bin                   # birinchi farq qiluvchi bayt; binary'lar uchun
comm -12 <(sort a) <(sort b)      # ikkalasidagi satrlar; -23 faqat a dagi; -13 faqat b dagi
md5sum file; sha256sum file; sha256sum -c SUMS     # mazmuni bir xilmi?
```

## Hammasini birlashtirish

```bash
grep -v '^#' /etc/ssh/sshd_config | grep -v '^$'                  # amaldagi konfiguratsiya
awk -F: '$7 ~ /bash/ {print $1}' /etc/passwd | sort               # bash ishlatadigan userlar
du -sh /var/* 2>/dev/null | sort -rh | head                        # /var ostidagi eng kattalari
journalctl -p err -o cat | sort | uniq -c | sort -rn | head        # eng tez-tez uchraydigan xatolar
ps aux --sort=-%mem | head -5 | awk '{print $2, $4, $11}'           # xotira bo'yicha eng yuqori PID'lar
```

:::exam-tip
Bu sohadagi topshiriqlar "Z dan Y ni o’z ichiga olgan X faylni hosil
qiling" ko’rinishida bo’ladi: javob - `> X` bilan tugaydigan pipeline.
Uni chapdan o’ngga quring, har bir bosqich chiqishini ekranda tekshirib
boring, keyin redirect’ni qo’shing. `uniq`’dan oldin `sort`, raqamlar
uchun `-n`, ajratgichlar uchun `-t`/`-d`, `sed -i`’ni esa faqat `sed`
chiqishini `-i`’siz ko’rganingizdan keyin.
:::

## O’zingizni tekshiring

1. `sort` nega `uniq`’dan oldin turishi kerak?
2. `/etc/passwd`’dagi eng ko’p uchraydigan beshta shell’ni sanoq bilan
   ro’yxatlaydigan pipeline’ni yozing.
3. `sed 's/a/b/' f` va `sed -i 's/a/b/g' f` orasidagi farq nima?
