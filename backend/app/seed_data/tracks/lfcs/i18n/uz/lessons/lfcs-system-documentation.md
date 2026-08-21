## Sizga beriladigan yagona ma’lumotnoma

Imtihonda web brauzer yo’q. Eslay olmagan hamma narsangiz tizimning o’z
hujjatlaridan kelishi kerak - va qaraydigan to’rt joyni bilsangiz, hammasi
o’sha yerda.

## man: qo’llanma

```bash
man ls                   # ls uchun sahifa
man 5 passwd             # /etc/passwd uchun FILE FORMAT sahifasi, passwd buyrugi emas
man -k "copy files"      # sahifa nomlari va bir qatorli tavsiflar bo'yicha qidiradi (apropos bilan bir xil)
man -f passwd            # qaysi bo'limlarda passwd nomli sahifa bor (whatis bilan bir xil)
man man                  # qo'llanma haqidagi qo'llanma
```

Bo’limlar - `ls(1)`, `passwd(5)`’dagi raqam:

| # | Nima | Misol |
|---|---|---|
| 1 | foydalanuvchi buyruqlari | `man 1 ls` |
| 5 | **fayl formatlari va konfiguratsiya fayllari** | `man 5 fstab`, `man 5 crontab`, `man 5 sshd_config`, `man 5 sudoers` |
| 8 | **administratsiya buyruqlari** | `man 8 mount`, `man 8 useradd`, `man 8 systemctl` |
| 2, 3 | tizim chaqiruvlari, kutubxona funksiyalari | dasturchilar uchun |
| 4 | qurilmalar | `man 4 null` |
| 7 | umumiy ko’rinishlar va kelishuvlar | `man 7 signal`, `man 7 regex`, `man 7 hier` |

Nom bir necha bo’limda uchraganda (`passwd` 1 va 5 da; `crontab` 1 va 5
da), `man name` eng kichigini ko’rsatadi; qolgani uchun raqamni bering.

Sahifa ichida (u `less`’da ochiladi): `/pattern` qidiradi, `n` keyingi
moslik, `N` oldingi, `g`/`G` boshi/oxiri, `q` chiqadi, `h` yordam. Tuzilishi
doim NAME, SYNOPSIS, DESCRIPTION, OPTIONS, keyin FILES, EXAMPLES, SEE ALSO -
EXAMPLES’ga `/^EXAMPLES` bilan o’ting.

```bash
man -k ^lv               # har bir LVM buyrugining sahifasi
man 5 fstab | grep -A3 "fourth field"
mandb                    # paket o'rnatgandan keyin man -k hech narsa topmasa, indeksni qayta quradi
```

## --help va help

```bash
ls --help | less         # ko'pchilik GNU buyruqlari: qisqacha qo'llanish, bayroq uchun man dan tezroq
tar --help | grep -- -z
help cd                  # bash BUILTIN'lari (cd, export, alias, ulimit...) o'z man sahifasiga ega emas; `help` - ularniki
help -m ulimit           # yoki `man bash` va builtin nomini qidiring
type cd                  # "cd is a shell builtin" - help ishlatish kerakligini shundan bilasiz
```

## info

```bash
info coreutils           # GNU qo'llanmalari: uzunroq, boblar va misollar bilan
info ls
```

Navigatsiya: `n`/`p` keyingi/oldingi node, `u` yuqoriga, link ustida
`Enter`, `q`. `man`’ga qaraganda kamroq ishlatiladi, lekin ba’zi GNU
vositalari (coreutils, grep, sed, bash) eng to’liq hujjatlarini shu yerda
saqlaydi.

## /usr/share/doc

```bash
ls /usr/share/doc/nginx/
zcat /usr/share/doc/nginx/README.Debian.gz
ls /usr/share/doc/sudo/examples/
```

Har bir paket uchun README’lar, changelog’lar va ko’pincha **misol
konfiguratsiya fayllari** - man sahifasi zich bo’lganda namunaviy
`chrony.conf` yoki sudoers parchasini topadigan joy.

## Qaysi biriga murojaat qilish kerak

| Savol | Murojaat qiling |
|---|---|
| "qaysi bayroq X ni bajaradi?" | `X --help`, keyin `man X` |
| "bu konfiguratsiya fayliga nima yoziladi?" | `man 5 file` |
| "qaysi buyruq Y ni bajaradi?" | `man -k Y` / `apropos Y` |
| "bu shell builtin’idan qanday foydalanaman?" | `help builtin` |
| "misol konfiguratsiya bormi?" | `/usr/share/doc/pkg/` |
| "signal raqamlari / regex qoidalari / directory tuzilishi qanday?" | `man 7 signal`, `man 7 regex`, `man 7 hier` |

:::exam-tip
Refleksni imtihonda emas, hozir mashq qiling: bundan keyingi har bir dars
o’z buyruqlari uchun man sahifasini nomlaydi. Uni oching, dars ishlatgan
bayroqni toping, atrofidagi bir paragrafni o’qing. O’n ikki haftadan keyin
`man 5 fstab` va `/` qidiruvi istalgan xotiradan tezroq bo’ladi.
:::

## O’zingizni tekshiring

1. `man passwd` va `man 5 passwd` orasidagi farq nima?
2. `man cd` nega ishlamaydi va uning o’rniga nimadan foydalanasiz?
3. Vosita nima qilishini bilsangiz-u, nomini bilmasangiz, qo’llanma
   sahifasini qaysi buyruq topadi?
