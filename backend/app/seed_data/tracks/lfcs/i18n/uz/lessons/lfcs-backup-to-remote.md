## Boshqa mashinaga nusxalash

Ikkita vosita: `scp` fayllarni nusxalaydi, `rsync` daraxtlarni
sinxronlaydi. Ikkalasi ham SSH ustida ishlaydi, shuning uchun ikkalasi ham
sizning SSH kalitlaringiz, portlaringiz va `~/.ssh/config` faylingizdan
foydalanadi.

## scp: oddiy nusxalar

```bash
scp file.txt user@host:/tmp/                    # lokal → uzoq host
scp user@host:/etc/nginx/nginx.conf ./          # uzoq host → lokal
scp -r site/ user@host:/var/www/                # rekursiv
scp -P 2222 file user@host:/tmp/                # sukut bo'yicha bo'lmagan port (katta P!)
scp -p file user@host:/tmp/                     # vaqt/mode'larni saqlaydi
scp -i ~/.ssh/deploy_key file user@host:/tmp/
scp user@host1:/f user@host2:/f                 # ikkita uzoq host o'rtasida (sizning mashinangiz orqali yoki -3)
```

`scp` har safar hamma narsani qaytadan nusxalaydi va davom ettirish imkoni
yo’q. Bitta fayl uchun bu yetarli; bir martadan ko’p nusxalanadigan
directory uchun rsync ishlating.

## rsync: faqat o’zgargani nusxalanadi

```bash
rsync -av /data/ user@host:/backup/data/         # kundalik shakl
rsync -avz /data/ user@host:/backup/data/        # + tarmoqda siqish bilan
rsync -av --delete /data/ user@host:/backup/data/    # maqsadni manbaga MOSLASHTIRADI (ortiqchasini o'chiradi)
rsync -av --dry-run --delete /data/ host:/backup/    # --delete ni DOIM avval dry-run qiling
rsync -av -e 'ssh -p 2222' /data/ host:/backup/
rsync -av --progress big.iso host:/tmp/          # progress, --partial bilan davom ettiriladi
rsync -av --exclude='*.tmp' --exclude='.cache/' /home/ /backup/home/
rsync -av --include='*.conf' --exclude='*' /etc/ /backup/etc-conf/
rsync -avn /data/ /backup/data/                  # -n = dry run, nima bo'lishini ko'rsatadi
```

| Bayroq | Ma’nosi |
|---|---|
| `-a` | arxiv: rekursiv + ruxsatlar, vaqtlar, symlink’lar, egalar, guruhlar saqlanadi (`-rlptgoD`) |
| `-v` | batafsil; `--progress` har bir fayl bo’yicha progress |
| `-z` | uzatish paytida siqadi |
| `--delete` | manbada endi mavjud bo’lmagan fayllarni maqsaddan o’chiradi |
| `-n` / `--dry-run` | ko’rsatadi, hech nima qilmaydi |
| `--exclude` / `--include` | pattern’lar, tartib bo’yicha baholanadi |
| `-e` | uzoq host uchun shell buyrug’i |
| `--partial` / `-P` | qayta urinish davom etishi uchun qisman fayllarni saqlaydi (`-P` = `--partial --progress`) |
| `--link-dest=DIR` | DIR’dagi o’zgarmagan fayllarni hard link qiladi - arzon snapshot’lar |
| `--bwlimit=5000` | KB/s ni cheklaydi |

## Oxiridagi qiya chiziq

rsync’dagi eng muhim tafsilot:

```bash
rsync -av /data  /backup/     # → /backup/data/...     (DIRECTORY'ni nusxalaydi)
rsync -av /data/ /backup/     # → /backup/...          (uning MAZMUNINI nusxalaydi)
```

Manbadagi qiya chiziq "ning mazmuni" degani; qiya chiziqsiz esa
"directory’ning o’zi". Maqsaddagi qiya chiziq ahamiyatsiz. Buni
chalkashtirsangiz, `/backup/data/data/` yoki yassilangan tartibsizlik
chiqadi - `--dry-run` buni bir soniyada ko’rsatadi.

## --link-dest bilan snapshot backup’lar

```bash
DEST=/backup/$(date +%F)
rsync -a --delete --link-dest=/backup/latest /data/ "$DEST/"
ln -sfn "$DEST" /backup/latest
```

O’zgarmagan fayllar kechagi nusxaga hard link bo’lib qoladi (hard-link
darsiga qarang): asosan o’zgarmaydigan 100 GB daraxtning o’ttizta kunlik
snapshot’i 100 GB’dan sal ko’proq joy egallaydi va har bir snapshot to’liq,
ko’rib chiqsa bo’ladigan daraxt bo’lib qolaveradi.

## Pull, push va pipe orqali

```bash
rsync -av user@host:/var/log/ /local/logs/        # pull
ssh host 'tar -czf - /etc' > etc-$(date +%F).tar.gz    # uzoq host'ni lokal arxivlash
tar -czf - /data | ssh host 'cat > /backup/data.tar.gz'
```

## Avtomatlashtirish

```bash
ssh-keygen -t ed25519 -f ~/.ssh/backup_key -N ''       # parol iborasiz, cron uchun
ssh-copy-id -i ~/.ssh/backup_key.pub backup@host
crontab -e
# 0 2 * * * rsync -a --delete -e 'ssh -i /home/ahmad/.ssh/backup_key' /data/ backup@host:/backup/data/ >> /var/log/backup.log 2>&1
```

(Kalitlar va `sshd`’ni qattiqlashtirish - 10-hafta; cron - 6-hafta.
Pattern - parol iborasiz kalit, cheklangan user, logga yozilgan chiqish -
standart hisoblanadi.)

:::warning
`--delete` maqsadni manbaga moslashtiradi, o’chirishlar bilan birga. Manba
yo’lidagi xato (bo’sh yoki noto’g’ri directory) va `--delete` birgalikda
backup’ni bo’shatib qo’yadi. Uni har safar avval `-n` bilan ishga tushiring
va yomon ishga tushirish qaytarib olinadigan bo’lishi uchun
`--delete-after` va snapshot’larni ko’rib chiqing.
:::

:::exam-tip
"/var/www ni host2:/var/www ga ruxsatlarni saqlab sinxronlang" →
`rsync -av /var/www/ host2:/var/www/` (oxiridagi qiya chiziqqa e’tibor
bering). "Faylni uzoq host’ga 2222-portda nusxalang" → `scp -P 2222 file
user@host:/path`. Maqsadda `ls -l` bilan yoki hech nima uzatilmasligini
xabar qiladigan ikkinchi rsync ishga tushirishi bilan tekshiring.
:::

## O’zingizni tekshiring

1. `rsync -av /data /backup/` va `rsync -av /data/ /backup/` orasidagi
   farq nima?
2. `-a` nimalarni o’z ichiga oladi va nega u sukut bo’yicha odat?
3. Nega `--delete`’dan oldin doim dry run bo’lishi kerak?
