## Kundalik fe’llar

Yaratish, qarash, nusxalash, ko’chirish, o’chirish. Buyruqlar kichik;
ularni tezlashtiradigan narsa - bayroqlar va globlar.

```bash
pwd; cd /var/log; cd -; cd ~; cd ..          # qayerdaman, orqaga, uyga, yuqoriga
ls -la; ls -lh; ls -lt; ls -ltr; ls -R; ls -d */   # uzun, o'qiladigan hajmlar, vaqt bo'yicha, teskari, rekursiv, faqat directory'lar
```

## Yaratish

```bash
touch notes.txt                  # bo'sh fayl yoki mavjudining mtime'ini yangilaydi
touch a.txt b.txt c.txt
mkdir reports                    # bitta directory
mkdir -p projects/2026/q3        # kerak bo'lgan ota-directory'lar bilan, mavjud bo'lsa xato yo'q
mkdir -m 750 private             # mode bilan
mkdir {dev,stage,prod}           # brace expansion: uchta directory
```

## Nusxalash

```bash
cp file.txt copy.txt
cp file.txt /tmp/                # directory ichiga, xuddi shu nom bilan
cp -r projects/ /backup/         # directory'lar uchun rekursiv
cp -a projects/ /backup/         # arxiv: rekursiv + mode, egasi, timestamp'lar, link'lar saqlanadi
cp -i a b                        # ustiga yozishdan oldin so'raydi
cp -n a b                        # hech qachon ustiga yozmaydi
cp -v *.conf /etc/app/           # batafsil
cp -p file.txt /tmp/             # mode/egalik/timestamp'larni saqlaydi (bitta fayl)
```

`cp dir/ dst/` va `cp dir dst/`: `-r` bilan **maqsad** oxiridagi qiya chiziq
"ichiga" degani; `dst` allaqachon mavjudmi-yo’qmi - `dst/dir` ni yoki `dir`
nusxasi bo’lgan `dst` ni olishingizni shu hal qiladi. Shubhalansangiz, keyin
`ls dst` qiling.

## Ko’chirish va nomini o’zgartirish

```bash
mv old.txt new.txt               # nomini o'zgartirish
mv file.txt /archive/            # ko'chirish
mv -i a b; mv -n a b             # so'raydi / hech qachon ustiga yozmaydi
mv dir1 dir2                     # directory nomini o'zgartiradi yoki dir2 mavjud bo'lsa, uning ichiga ko'chiradi
mv *.log /var/log/old/
```

`mv` bitta filesystem ichida atomar (bu rename), filesystem’lar o’rtasida
esa nusxalash+o’chirish.

## O’chirish

```bash
rm file.txt
rm -i *.tmp                      # har birini so'raydi
rm -r olddir/                    # rekursiv
rm -rf build/                    # rekursiv, so'roqsiz, yo'q fayllar uchun xatosiz - xavflisi
rmdir emptydir                   # faqat bo'sh directory'lar - xavfsiz
rmdir -p a/b/c                   # hammasi bo'sh bo'lsa, zanjirni o'chiradi
rm -- -weird-name                # - bilan boshlanadigan fayl
rm ./-weird-name
```

:::warning
Bo’sh o’zgaruvchi bilan yoki o’zingiz mo’ljallagandan ko’prog’iga mos
keladigan glob bilan `rm -rf` istalgan hujumchidan ko’ra ko’proq serverni
yo’q qilgan. `rm -rf
$DIR/*` dan oldin `echo rm -rf $DIR/*` - nima ochilishiga qarang. Va hech
qachon `rm` ni `rm -i` ga alias qilib, unga tayanmang; bu odat keyingi
mashinaga o’tmaydi.
:::

## Globlar: shell ochadigan pattern’lar

| Pattern | Nimaga mos keladi |
|---|---|
| `*` | istalgan satr, bo’sh satr ham (boshidagi `.` dan tashqari) |
| `?` | roppa-rosa bitta belgi |
| `[abc]`, `[a-z]`, `[0-9]` | to’plam/diapazondan bitta belgi |
| `[!abc]` yoki `[^abc]` | to’plamda yo’q bitta belgi |
| `{a,b,c}` | brace expansion: har bir variant (bu glob emas - mos fayl bo’lmasa ham ochiladi) |
| `{1..5}`, `{a..e}`, `{01..10}` | ketma-ketliklar |
| `.*` | dot-fayllar (yashirin) - yolg’iz `*` ularni o’tkazib yuboradi; `ls -A` ko’rsatadi |

```bash
ls *.log                         # shu directory'dagi har bir .log
ls file?.txt                     # file1.txt, fileA.txt, lekin file10.txt emas
ls [a-c]*                        # a, b yoki c bilan boshlanadigan nomlar
cp report_{2024,2025}.pdf /tmp/  # ikkita fayl
mkdir day{01..07}                # yettita directory
rm -- *.tmp                      # `--` opsiyalarni tugatadi; - bilan boshlanadigan nomlardan himoya qiladi
echo *                           # rm ichida ishlatishdan oldin glob nimaga ochilishini ko'ring
```

Globlarni buyruq ishga tushishidan oldin **shell** ochadi: `rm *.txt`
`rm a.txt b.txt c.txt` ga aylanadi. Buyruq pattern’ning o’zini ko’rishi
kerak bo’lsa, uni qo’shtirnoqqa oling (`'*.txt'`) - keyingi darsda
`find -name '*.txt'`.

## Sakrashdan oldin qarash

```bash
ls -l target/                    # u yerda nima bor
file something                   # bu qanday fayl (matn, ELF, directory, gzip...)
stat file.txt                    # hajm, inode, ruxsatlar, uchta timestamp
du -sh dir/                      # qanchalik katta
tree -L 2 dir/                   # o'rnatilgan bo'lsa
```

:::exam-tip
Topshiriqlarda "Y/Z subdirectory’lari bilan X directory yarating" deyiladi -
`mkdir -p X/Y/Z`; "A directory’ni ruxsatlarni saqlagan holda B ga
nusxalang" - `cp -a`; "/var/app ostidagi barcha `.tmp` fayllarni o’chiring" -
`rm -r` emas, `find` (keyingi dars). Natijani doim `ls` qiling; tekshiruvchi
buyruqni emas, yakuniy holatni ko’radi.
:::

## O’zingizni tekshiring

1. `cp -r` va `cp -a` orasidagi farq nima?
2. `proj/src`, `proj/test` va `proj/docs` ni yaratadigan bitta buyruq yozing.
3. `rm -rf $DIR/*` dan oldin `echo rm -rf $DIR/*` nega yaxshi odat?
