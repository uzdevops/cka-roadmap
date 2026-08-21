## find: daraxtni aylanib, har bir yozuvni tekshiradi

```bash
find [where] [tests] [actions]
find /var/log -name "*.log"                 # nom bo'yicha (glob, shell kengaytirmasligi uchun qo'shtirnoqda)
find . -iname "readme*"                     # katta-kichik harfga sezgir emas
find / -type d -name "conf*" 2>/dev/null    # faqat directory'lar; ruxsat xatolarini tashlab yuboradi
```

Boshlang’ich yo’l ko’rsatilmasa - `.`; amal ko’rsatilmasa - `-print`.
Tekshiruvlar sukut bo’yicha AND bilan birlashadi; `-o` - OR; `!` yoki
`-not` inkor qiladi; `\( \)` guruhlaydi.

## Siz ishlatadigan tekshiruvlar

| Tekshiruv | Nimaga mos keladi |
|---|---|
| `-name "*.conf"`, `-iname` | basename glob (qo’shtirnoqqa oling) |
| `-path "*/log/*"` | butun yo’l |
| `-type f` / `d` / `l` / `b` / `c` / `s` | fayl, directory, symlink, block, char, socket |
| `-size +1M`, `-size -10k`, `-size 100c` | kattaroq, kichikroq, aynan; birliklar `c` bayt `k` `M` `G` (yalang’och raqam = 512 baytlik bloklar) |
| `-empty` | bo’sh fayl yoki directory |
| `-user alice`, `-group devs`, `-uid 1001`, `-nouser` | egalik (`-nouser`: egasi endi mavjud emas) |
| `-perm 644` | **aynan** 644 |
| `-perm -644` | **hech bo’lmaganda** shu bitlar (hammasi qo’yilgan) |
| `-perm /222` | shu bitlardan **biri** (har kim yoza oladi) |
| `-perm -4000`, `-perm -2000`, `-perm -o+w` | SUID, SGID, other yoza oladigan |
| `-mtime -7`, `-mtime +30`, `-mtime 0` | 7 kundan kam oldin / 30 kundan ko’p oldin / bugun o’zgargan |
| `-mmin -60` | oxirgi 60 daqiqada o’zgargan |
| `-atime`, `-ctime`, `-amin`, `-cmin` | murojaat, inode o’zgarishi |
| `-newer ref.txt`, `-newermt "2026-08-01"` | fayldan / sanadan keyin o’zgargan |
| `-links +1`, `-samefile f`, `-inum N` | hard link’lar |
| `-maxdepth 1`, `-mindepth 2` | qanchalik chuqur (bular tekshiruvlardan **oldin** turadi) |
| `-xdev` / `-mount` | bitta filesystem’da qolish |
| `-readable`, `-writable`, `-executable` | joriy user uchun |

```bash
find /home -type f -size +100M
find /etc -type f -mtime -1                          # oxirgi kunda o'zgargan
find / -type f -perm -4000 2>/dev/null               # SUID
find /var -type f -perm /o+w ! -type l 2>/dev/null   # hamma yoza oladigan fayllar
find /srv -user alice -o -group devs
find . \( -name "*.tmp" -o -name "*.bak" \) -type f
find /var/log -name "*.log" -size +10M -mtime +7
find / -maxdepth 2 -type d -name "*conf*"
find /data -type f -newermt "2026-08-01" ! -newermt "2026-08-15"
```

## Amallar: har bir moslik bilan nimadir qilish

| Amal | Nima qiladi |
|---|---|
| `-print` | sukut bo’yicha |
| `-ls` | `ls -l` uslubidagi satr |
| `-delete` | o’chiradi (**oxiriga** qo’ying; avval `-print` bilan sinang) |
| `-exec cmd {} \;` | cmd ni **har bir fayl uchun** bir marta ishga tushiradi; `{}` - nom |
| `-exec cmd {} +` | cmd ni **ko’p fayl bilan** bir marta ishga tushiradi (tezroq, xargs kabi) |
| `-ok cmd {} \;` | `-exec` kabi, lekin so’raydi |
| `-printf "%s %p\n"` | o’z formatingiz: `%p` yo’l, `%s` hajm, `%u` user, `%m` rejim, `%TY-%Tm-%Td` mtime |

```bash
find /var/log -name "*.gz" -mtime +30 -delete
find /srv -type f -name "*.sh" -exec chmod +x {} \;
find /srv -type d -exec chmod 2775 {} +
find /home -user olduser -exec chown newuser:newuser {} +
find . -name "*.log" -exec grep -l ERROR {} +
find /etc -name "*.conf" -exec cp {} /backup/etc/ \;
find /tmp -type f -atime +10 -ok rm {} \;
find / -perm -4000 -type f -printf "%m %u %p\n" 2>/dev/null
find /var -size +50M -printf "%s %p\n" | sort -n | tail
```

`{}` har bir yo’l bilan almashtiriladi; `\;` buyruqni tugatadi (shell uni
yeb qo’ymasligi uchun ekranlangan); `+` esa to’plab yuboradi. `-exec ... +`
bilan `{}` oxirida turishi shart.

## find va xargs

```bash
find . -name "*.txt" -print0 | xargs -0 grep -l "TODO"      # -print0/-0 nomlardagi bo'sh joy va yangi qatorni to'g'ri ishlaydi
find /var/log -name "*.log" | xargs ls -lS | head
```

`-exec ... +` shu ishni pipe’siz bajaradi; bosim ostida qaysi biri
esingizda bo’lsa, o’shani ishlating.

## locate: indekslangan qidiruv

```bash
sudo updatedb                 # bazani quradi/yangilaydi (buni har kuni cron job bajaradi)
locate sshd_config            # bir zumda, to'liq yo'l bo'yicha substring moslik
locate -i readme | head
locate -c "*.conf"
```

Tez, lekin oxirgi `updatedb` qanchalik yangi bo’lsa, shunchalik yangi va
undan keyin yaratilgan fayllarni bilmaydi. `find` - ishonchli manba;
`locate` - qulaylik.

## Boshqa "u qayerda" buyruqlari

```bash
which nginx                   # PATH'dagi bajariladigan fayl
whereis nginx                 # binary, manbalar, man sahifasi
type ls                       # alias, builtin yoki fayl
```

:::exam-tip
Imtihon topshiriqlari aynan `find` sintaksisidek o’qiladi: "/var ostidagi
10 MB’dan katta, root’ga tegishli barcha fayllarni toping va ro’yxatini
/root/big.txt ga saqlang" →
`find /var -type f -size +10M -user root > /root/big.txt 2>/dev/null`.
root bo’lmaganingizda doim `2>/dev/null` (ruxsat shovqini), "fayllar"
deyilganda `-type f`, `-delete`/`-exec` ni esa faqat `-print` ro’yxatini
bir marta ko’rganingizdan keyin ishlating.
:::

## O’zingizni tekshiring

1. `-perm 644`, `-perm -644` va `-perm /644` orasidagi farq nima?
2. `/var/log` ostidagi 7 kundan ko’p oldin o’zgargan `.log` fayllarni
   topib o’chiradigan buyruqni yozing.
3. `-exec cmd {} +` qachon `-exec cmd {} \;` dan afzal?
