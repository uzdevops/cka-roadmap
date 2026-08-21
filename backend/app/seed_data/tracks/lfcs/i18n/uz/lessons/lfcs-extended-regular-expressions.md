## ERE: backslash’lari olib tashlangan o’sha til

Kengaytirilgan muntazam ifodalar oddiysi GNU escape’lari bilan ifodalay
olmaydigan hech narsa qo’shmaydi; ular keng tarqalgan operatorlarni
**escape’siz** qiladi. `grep -E`, `egrep`, `sed -E` (yoki `-r`), `awk` -
hammasi ERE ishlatadi.

| Operator | BRE | ERE | Ma’nosi |
|---|---|---|---|
| bir yoki undan ko’p | `\+` | `+` | |
| nol yoki bitta | `\?` | `?` | |
| n dan m gacha | `\{n,m\}` | `{n,m}` | |
| guruh | `\(…\)` | `(…)` | |
| alternatsiya | `\|` | `|` | **yoki** |
| harfma-harf `+ ? { } ( ) |` | `+ ? { } ( ) |` | `\+ \? \{ \} \( \) \|` | escape teskarisiga o’tadi |

`. * ^ $ [ ]` ikkalasida ham bir xil.

## Alternatsiya

```bash
grep -E 'error|warn|crit' /var/log/syslog
grep -E '^(root|admin):' /etc/passwd
grep -Ei '(jan|feb|mar) [0-9]+' log
grep -E 'colou?r' file                  # ? backslashsiz
```

Qavslar `|`ning qamrovini belgilaydi: `^root|admin:` - "root bilan
boshlanadi YOKI tarkibida admin: bor" degani; `^(root|admin):` esa -
"root: yoki admin: bilan boshlanadi" degani.

## Figurali qavslar bilan sanash

```bash
grep -E '^[0-9]{1,3}(\.[0-9]{1,3}){3}$' ips          # IPv4 ko'rinishi: 1-3 raqam, keyin uch marta ".1-3 raqam"
grep -E '^[a-f0-9]{32}$' hashes                      # MD5
grep -E '^.{80,}$' file                              # uzun qatorlar
grep -E '(ab){2,}' file                              # abab, ababab...
grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}' log            # sana bilan boshlanadigan qatorlar
```

## Guruhlar, ushlab olishlar va orqaga havolalar

```bash
grep -E '([a-z])\1' file                             # takrorlangan harf
sed -E 's/([0-9]+)\.([0-9]+)\.([0-9]+)/\3.\2.\1/' f   # nuqtali uchlikni teskari qilish
sed -E 's/^(#?)Port .*/Port 2222/' sshd_config       # izohga olingan yoki olinmagan qatorni almashtirish
echo "user=alice" | sed -E 's/^user=(.*)$/\1/'        # ajratib olish
awk '/^[0-9]+ /' file                                # awk pattern'lari - ERE
```

## Qisqartmalar (GNU)

| | |
|---|---|
| `\w`, `\W` | so’z belgisi `[A-Za-z0-9_]` / u emas |
| `\s`, `\S` | bo’sh joy / u emas |
| `\b` | so’z chegarasi; `\<` `\>` so’z boshi/oxiri |
| `\d` | grep/sed buni **qo’llab-quvvatlamaydi** - `[0-9]` yoki `[[:digit:]]` ishlating |

```bash
grep -E '\bsshd\b' log
grep -Eo '\w+@\w+\.\w+' file                         # qo'pol email ajratish
grep -Eo '[0-9]+' file | sort -n | tail -1           # fayldagi eng katta son
```

## grep -o va -E birga: ajratib olish

`-o` faqat mos kelgan qismni, har bir moslik uchun bir martadan chiqaradi
- ERE bilan bu kichkina ekstraktor:

```bash
grep -Eo '[0-9]{1,3}(\.[0-9]{1,3}){3}' access.log | sort | uniq -c | sort -rn | head    # klient IP'lari soni bo'yicha
grep -Eo 'HTTP/[0-9.]+" [0-9]{3}' access.log | awk '{print $2}' | sort | uniq -c          # status kodlari
grep -Eo '^[^:]+' /etc/passwd                                                             # foydalanuvchi nomlari (cut -d: -f1 bilan bir xil)
grep -Eo 'inet [0-9.]+' <(ip a) | awk '{print $2}'                                       # hostdagi IPv4 manzillar
```

## Tanlash

| Nimani ishlatish | Qachon |
|---|---|
| `grep 'pattern'` (BRE) | harfma-harf belgilar, anchor’lar, sinflar, `*` - ko’p hollarda |
| `grep -E 'pattern'` | sizga `+ ? {} () |` kerak va ularni escape qilishni xohlamaysiz |
| `grep -F 'string'` | "pattern" - metabelgilari bor harfma-harf satr (`$HOME`, `1.2.3.4`, `a+b`) - umuman regex yo’q |
| `grep -P` | Perl regex (`\d`, lookahead) - faqat GNU, POSIX emas; zarur bo’lmasa imtihonda ishlatmang |
| `sed -E`, `awk` | guruhlar bilan tahrirlash/ajratib olish |

:::exam-tip
Topshiriqda "X yoki Y bor qatorlar" deyilsa → `grep -E 'X|Y'`; "kamida
uch xonali son" → `grep -E '[0-9]{3,}'`; "`$PATH` harfma-harf satriga mos
qatorlar" → `grep -F '$PATH'`. Agar `+` yoki `|` bor pattern oddiy
`grep`da hech narsaga mos kelmasa, siz `-E`ni unutgansiz - bu regexdagi
eng ko’p uchraydigan nosozlik.
:::

## O’zingizni tekshiring

1. `grep 'colou\?r\|gray'`ni ERE ko’rinishida qayta yozing.
2. Faqat MAC manzildan (`aa:bb:cc:dd:ee:ff`) iborat qatorlarga mos
   keladigan ERE yozing.
3. `grep -F` qachon to’g’ri vosita va nega?
