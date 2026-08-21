## Uchta siquvchi

Har biri faylni oladi, uning o’rniga siqilganini qo’yadi va so’ralganda
ortga qaytaradi. Ular tezlik va siqish nisbati bilan farq qiladi, tar’da
esa har biri uchun bayroq bor.

| Vosita | Kengaytma | tar bayrog’i | Tezlik | Nisbat | Izohlar |
|---|---|---|---|---|---|
| `gzip` | `.gz` | `-z` | eng tez | yaxshi | hamma joyda sukut bo’yicha |
| `bzip2` | `.bz2` | `-j` | sekin | yaxshiroq | eskiroq, o’rnini boshqasi egallamoqda |
| `xz` | `.xz` | `-J` | eng sekin | eng yaxshi | kernel/distributiv arxivlari |
| `zstd` | `.zst` | `--zstd` | tez | juda yaxshi | mavjud bo’lgan joyda zamonaviy tanlov |

## gzip

```bash
gzip file.txt                # → file.txt.gz, ASL FAYL O'RNIGA QO'YILADI
gzip -k file.txt             # aslini saqlaydi
gzip -9 file.txt             # eng kuchli siqish (-1 eng tez)
gzip -r logs/                # daraxtdagi har bir faylni alohida
gunzip file.txt.gz           # yoki: gzip -d
zcat file.txt.gz             # diskka ochmasdan o'qish
zless, zgrep 'ERROR' f.gz, zdiff a.gz b.gz     # z-vositalari .gz bilan to'g'ridan-to'g'ri ishlaydi
gzip -l archive.gz           # siqilgan/siqilmagan hajmlar va nisbat
gzip -t archive.gz           # butunligini tekshiradi
```

Boshlovchilar uchun kutilmagani: `gzip file` `file`’ni **o’chiradi**.
`-k`’dan foydalaning, yoki nusxani siqing, yoki (yaxshirog’i) asl ma’lumotni
emas, arxivni siqing.

## bzip2 va xz

```bash
bzip2 -k big.log; bunzip2 big.log.bz2; bzcat big.log.bz2; bzgrep ERROR big.log.bz2
xz -k big.log;    unxz big.log.xz;     xzcat big.log.xz;  xzgrep ERROR big.log.xz
xz -9 -T0 big.log            # maksimal siqish, barcha CPU thread'lari
zstd -k -19 big.log; unzstd big.log.zst; zstdcat big.log.zst
```

Interfeyslar ataylab gzip’nikini takrorlaydi: `-k` saqlash, `-d` ochish,
`-1..-9` daraja, `-t` tekshirish, ustiga `*cat`, `*grep`, `*less` oilasi.

## zip va unzip: platformalararosi

```bash
zip archive.zip file1 file2          # zip HAM arxivlaydi, HAM siqadi (tar'dan farqli)
zip -r site.zip site/                # rekursiv
zip -e secret.zip file               # parol (kuchsiz - haqiqiy shifrlash emas)
unzip archive.zip                    # joriy directory ichiga
unzip -l archive.zip                 # ro'yxat
unzip archive.zip -d /var/www        # directory ichiga
unzip -o archive.zip                 # so'ramasdan ustiga yozadi
```

Boshqa uchida Windows bo’lsa zip’dan foydalaning; Unix bilan bog’liq hamma
narsa uchun tar+gzip - zip egalarni, ruxsatlarni yoki symlink’larni
ishonchli saqlamaydi.

## Amalda tanlash

- **Loglar, backup’lar, shoshib kerak bo’lishi mumkin bo’lgan hamma
  narsa**: `gzip` (`tar -czf`).
- **Uzoq muddatli arxivlar, distributiv image’lari, CPU vaqti arzon,
  baytlar esa qimmat bo’lgan joy**: `xz` (`tar -cJf`).
- **Linux’da bo’lmagan foydalanuvchiga yuborish**: `zip`.
- **Allaqachon siqilgan ma’lumot** (jpg, mp4, .gz, rpm/deb): qayta
  siqmang - CPU sarflab, ustiga bayt qo’shasiz.

```bash
ls -lh big.log*                       # natijalarni solishtiring
for c in gzip bzip2 xz; do cp big.log t; $c -9 t; ls -lh t.*; rm -f t.*; done
```

## Fayllarsiz siqish: pipe’lar

```bash
tar -cf - /data | gzip -9 > data.tar.gz               # tar stdout'ga, siqish pipe ichida
mysqldump db | gzip > db.sql.gz                        # stream'ni siqadi, diskka siqilmagan holda tegmaydi
gzip -dc data.tar.gz | tar -xf - -C /restore
ssh host 'tar -czf - /etc' > etc-remote.tar.gz         # masofadagi host'ni lokal faylga arxivlaydi
dd if=/dev/sda bs=4M | gzip > disk.img.gz
```

Fayl nomi sifatida `-` stdin/stdout degani; backup’lar disk hajmini ikki
baravar band qilmasdan shunday olinadi.

:::exam-tip
Uchalasi uchun ham ikkala yo’nalishni biling: `gzip`/`gunzip`,
`bzip2`/`bunzip2`, `xz`/`unxz` va mos tar bayroqlari `-z -j -J`.
Topshiriqda "faylni asl nusxasini saqlagan holda siqing" deyilsa - bu `-k`.
"Siqilgan logni chiqarmasdan o’qing" deyilsa - bu `zcat`/`zgrep`.
:::

## O’zingizni tekshiring

1. `gzip report.txt`’ni ishga tushirganingizda `report.txt`’ga nima
   bo’ladi va bundan qanday qochasiz?
2. Uzoq muddatli arxiv uchun qaysi siquvchi, tungi log rotatsiyasi uchun
   qaysi biri va nega?
3. `.gz` log faylini diskka ochmasdan qanday grep qilasiz?
