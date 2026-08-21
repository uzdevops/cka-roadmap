## Qatorlarni topish

`grep` o’z inputidan pattern’ga mos keladigan qatorlarni chiqaradi. Bu -
shu yo’nalishda `ls`dan keyin eng ko’p yozadigan buyrug’ingiz.

```bash
grep root /etc/passwd                   # "root" bor qatorlar
grep -i error /var/log/syslog           # registrga sezgir emas
grep -n Listen /etc/apache2/ports.conf  # qator raqamlari bilan
grep -v '^#' /etc/ssh/sshd_config       # mos KELMAYDIGAN qatorlar (invert)
grep -c failed /var/log/auth.log        # mos qatorlarni sanash
grep -r "server_name" /etc/nginx/       # katalog bo'ylab rekursiv
grep -rn TODO src/                      # rekursiv, file:line bilan
grep -l "PermitRootLogin" /etc/ssh/*    # faqat mos kelgan fayl nomlari
grep -L "PermitRootLogin" /etc/ssh/*    # mos KELMAGAN fayl nomlari
grep -w cat file                        # faqat butun so'z ("concatenate" emas)
grep -o '[0-9]\+' file                  # faqat mos kelgan qismni chiqaradi, har biri bir qatorda
grep -A3 -B1 "panic" log                # 3 qator keyin, 1 qator oldin; -C2 ikkalasi
grep -E 'warn|error' log                # kengaytirilgan regex (keyingi ikki dars); egrep bilan bir xil
grep -F '$HOME' file                    # qat'iy satr, regex yo'q (fgrep bilan bir xil)
grep -e '-x' file; grep -- -x file      # - bilan boshlanadigan pattern
grep -q pattern file && echo found      # jim: faqat exit status (0 mos, 1 yo'q, 2 xato) - skriptlar uchun
grep -h pattern *.log                   # fayl nomi prefiksisiz
grep -s pattern *                       # "cannot open" xatolarisiz
```

## Pipe qilingan inputni o’qish

```bash
ps aux | grep nginx | grep -v grep      # (yoki: pgrep -a nginx)
journalctl -u sshd | grep -i "failed password"
dmesg | grep -i usb
ss -tulpn | grep :22
env | grep -i proxy
```

## Pattern’lar: aslida nima yozayotganingiz

grep pattern’i - bu **muntazam ifoda**, glob emas. `grep *.log file`
".log fayllari" degani emas - shell avval `*.log`ni yoyadi, qolgani esa
`.` "istalgan belgi" ma’nosini beradigan regex. Regex darslarigacha
chalkashlikdan saqlaydigan uchta qoida:

1. **Pattern’ni tirnoq ichiga oling** (`'...'`), toki shell `*`, `$` va
   bo’sh joylarni yoymasin.
2. `.` istalgan belgiga mos keladi; harfma-harf nuqta uchun `\.`.
3. `^` qator boshini, `$` oxirini bog’laydi: `'^root'`, `'bash$'`.

```bash
grep '^root' /etc/passwd                # root bilan boshlanadigan qatorlar
grep 'bash$' /etc/passwd                # bash bilan tugaydigan qatorlar
grep '^$' file | wc -l                  # bo'sh qatorlar
grep '192\.168\.1\.' /var/log/syslog    # harfma-harf nuqtalar
grep -v '^\s*#' /etc/fstab | grep -v '^$'    # izohlar va bo'shlarni olib tashlash
```

## Foydali kombinatsiyalar

```bash
grep -rl "old.example.com" /etc | xargs sed -i 's/old\.example\.com/new.example.com/g'   # fayllarni topib, keyin tahrirlash
grep -c "" file                                  # qatorlarni sanash (wc -l kabi)
grep -n . file | tail -1                         # oxirgi bo'sh bo'lmagan qator, raqami bilan
grep -E -o '\b[0-9]{1,3}(\.[0-9]{1,3}){3}\b' log | sort | uniq -c | sort -rn | head     # IP'lar chastotasi bo'yicha
grep -i "failed password" /var/log/auth.log | awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head   # kim brute-force qilyapti
```

## Exit status

`0` biror narsa mos keldi, `1` hech narsa mos kelmadi, `2` xato. Skriptlar
va `&&`/`||` zanjirlari shunga tayanadi:

```bash
if grep -q '^alice:' /etc/passwd; then echo "alice exists"; fi
grep -q nameserver /etc/resolv.conf || echo "no DNS configured"
```

:::exam-tip
"Y fayldagi X bor barcha qatorlarni Z fayliga saqlang" → `grep X Y > Z`;
"qatorlarni sanang" → `grep -c`; "registrni e’tiborsiz qoldiring" → `-i`;
"tarkibida bo’lmagan qatorlar" → `-v`; "katalog ostidagi har bir faylda
qidiring" → `-r`. Pattern’ni har safar tirnoq ichiga oling. Keyingi regex
darslari pattern’ning o’zini aniq qiladi.
:::

## O’zingizni tekshiring

1. `-v`, `-c`, `-l` va `-o` nima qiladi?
2. Nega grep pattern’i tirnoq ichiga olinishi kerak va unda `.` nimani
   anglatadi?
3. Skriptda grep’ning exit status’idan qanday foydalanasiz?
