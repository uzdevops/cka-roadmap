## tar: ko’pdan bitta fayl

`tar` ("tape archive") directory daraxtini bitta faylga joylaydi, nomlar,
ruxsatlar, egalar, timestamp’lar va link’larni saqlagan holda. U o’zi
**siqmaydi** - buning uchun bayroq orqali gzip, bzip2 yoki xz ni chaqiradi.

```bash
tar -cvf backup.tar /etc/nginx          # yaratish, batafsil, fayl
tar -czvf backup.tar.gz /etc/nginx      # + gzip      (.tar.gz / .tgz)
tar -cjvf backup.tar.bz2 /etc/nginx     # + bzip2     (.tar.bz2)
tar -cJvf backup.tar.xz /etc/nginx      # + xz        (.tar.xz)
```

| Bayroq | Ma’nosi |
|---|---|
| `-c` | **c**reate - yaratadi |
| `-x` | e**x**tract - chiqaradi |
| `-t` | lis**t** contents - tarkibni ro’yxatlaydi |
| `-f FILE` | arxiv **f**ayli - guruhlangan harflar orasida doim oxirgi, nomdan bevosita oldin |
| `-v` | batafsil |
| `-z` `-j` `-J` | gzip / bzip2 / xz |
| `-C DIR` | avval DIR’ga o’tadi (**ichiga** chiqaradi yoki **ichidan** arxivlaydi) |
| `-p` | ruxsatlarni saqlaydi (chiqarishda root uchun sukut bo’yicha) |
| `--exclude=PATTERN` | mos kelganlarini o’tkazib yuboradi |
| `-r` / `-u` | qo’shadi / yangiroq bo’lsa qo’shadi (faqat siqilmagan arxivlar) |
| `--strip-components=N` | chiqarishda boshidagi N ta yo’l elementini tashlaydi |

## Uchta fe’l

```bash
tar -czf /backup/etc-$(date +%F).tar.gz /etc                  # yaratish
tar -tzf /backup/etc-2026-08-21.tar.gz | head                 # ro'yxat - chiqarishdan oldin doim qarang
tar -xzf /backup/etc-2026-08-21.tar.gz -C /restore            # directory ichiga chiqarish
tar -xzf archive.tar.gz etc/nginx/nginx.conf                   # bitta a'zoni chiqarish
tar -xzf archive.tar.gz --wildcards '*.conf'                   # pattern bo'yicha chiqarish
```

Zamonaviy tar chiqarishda siqishni o’zi aniqlaydi (`-xaf` yoki shunchaki
`-xf`), shuning uchun `tar -xf whatever.tar.xz` ishlaydi; **yaratishda**
esa qaysi ekanini aytishingiz shart.

## Yo’llar: absolyut va nisbiy

```bash
tar -czf backup.tar.gz /etc/nginx
# tar: Removing leading `/' from member names
```

tar `etc/nginx/...`’ni (nisbiy) saqlaydi, shuning uchun chiqarish tasodifan
`/etc` ustiga yoza olmaydi - u joriy directory ostiga tushadi. Joyida
tiklash uchun:

```bash
cd / && tar -xzf /backup/backup.tar.gz          # /etc/nginx ni qayta yaratadi
tar -xzf /backup/backup.tar.gz -C /             # xuddi shu, cd'siz
```

Ota-directory ichidan arxivlash daraxtni tartibli saqlaydi:

```bash
tar -czf nginx.tar.gz -C /etc nginx             # a'zolar etc/nginx/... emas, nginx/...
```

## Chiqarib tashlash va tanlash

```bash
tar -czf home.tar.gz --exclude='*.iso' --exclude='.cache' /home/ahmad
tar -czf src.tar.gz --exclude-vcs project/
tar -czf logs.tar.gz $(find /var/log -name '*.log' -mtime -1)
tar -czf sel.tar.gz -T filelist.txt             # nomlar fayldan
```

`--exclude`’ni yo’llardan **oldin** qo’ying; pattern’lar - saqlangan
(nisbiy) nomlarga solishtiriladigan globlar.

## Inkremental va snapshot’simon backup’lar

```bash
tar -czf full.tar.gz -g snapshot.snar /data          # 0-daraja: hammasi, holatni yozib qo'yadi
tar -czf inc1.tar.gz -g snapshot.snar /data          # 1-daraja: faqat shundan keyin o'zgargani
```

`-g` (`--listed-incremental`) holat faylini yuritadi; tiklash - to’liq
arxivni, so’ng har bir inkrementni tartib bilan chiqarish. Ko’p ishlar
uchun `rsync` (ikki darsdan keyin) soddaroq.

## Tekshirish va ruxsatlar

```bash
tar -tzvf backup.tar.gz | head          # uzun ro'yxat: mode'lar, egalar, hajmlar, sanalar
tar -dzf backup.tar.gz -C /             # arxivni filesystem bilan solishtiradi
sha256sum backup.tar.gz > backup.tar.gz.sha256
sha256sum -c backup.tar.gz.sha256
```

root sifatida chiqarish asl egalar va ruxsatlarni tiklaydi; oddiy user
sifatida fayllar sizniki bo’lib qoladi (`--no-same-owner` - root
bo’lmaganlar uchun sukut bo’yicha, `--same-owner` - root uchun). root
bo’lmagan user tiklagan `/etc` backup’i ishlaydigan `/etc` emas.

## Uchrashingiz mumkin bo’lgan boshqa arxivatorlar

```bash
cpio -o < list > archive.cpio; cpio -idmv < archive.cpio     # initramfs image'lari shundan foydalanadi
zip -r site.zip site/; unzip -l site.zip; unzip site.zip -d /var/www    # platformalararo
dd if=/dev/sda of=/backup/disk.img bs=4M status=progress      # xom blok nusxasi (11-hafta)
```

:::warning
Ishonchsiz arxivni avval ro’yxatlamasdan (`tar -tf`) muhim directory ichiga
hech qachon chiqarmang. Arxivlar ichida maqsad tashqarisidagi fayllar
ustiga yozish uchun tayyorlangan `../` yoki absolyut yo’llar bo’lishi
mumkin - GNU tar ularni sukut bo’yicha kesib tashlaydi, lekin avval qarash
odati bitta buyruqqa tushadi.
:::

:::exam-tip
Imtihon so’zlari to’g’ridan-to’g’ri o’giriladi: "/etc/skel ning gzip bilan
siqilgan arxivini /root/skel.tar.gz da yarating" →
`tar -czf /root/skel.tar.gz -C /etc skel`; "/tmp/data.tar.bz2 ni /srv
ichiga chiqaring" → `tar -xjf /tmp/data.tar.bz2 -C /srv`; "tarkibini
ro’yxatlang" → `tar -tf`. So’ng `tar -tf` bilan yoki maqsadni `ls` qilib
tekshiring.
:::

## O’zingizni tekshiring

1. `-c`, `-x`, `-t` va `-f` nima qiladi va nega guruhlangan bayroqlar
   orasida `-f` oxirgi bo’lishi kerak?
2. tar nega boshidagi `/`’ni kesib tashlaydi va arxivni joyida qanday
   tiklaysiz?
3. `*.log`’ni chiqarib tashlagan holda `/var/www`’ni xz bilan siqilgan
   `/backup/www.tar.xz` sifatida arxivlaydigan buyruqni yozing.
