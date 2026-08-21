## Soft link - ichida yo’l saqlaydigan fayl

**Symbolic (soft) link** - bu mazmuni boshqa nomga olib boradigan **yo’l**
bo’lgan alohida kichik fayl. Linkni ochish shu yo’lga ergashadi. U maqsad
bilan inode’ni bo’lishmaydi; u ma’lumotga emas, *nom*ga ishora qiladi.

```bash
ln -s /var/log/syslog currentlog          # ln -s TARGET LINKNAME
ls -l currentlog
# lrwxrwxrwx 1 ahmad ahmad 15 Aug 19 10:05 currentlog -> /var/log/syslog
```

Boshida `l`, oxirida `-> target`, hajm (15) esa yo’l satrining uzunligi.
Symlink’da ko’rsatilgan ruxsatlar doim `rwxrwxrwx` bo’ladi va hech nimani
anglatmaydi - **maqsadning** ruxsatlari amal qiladi.

## Soft link qila oladigan, hard link qila olmaydigan narsalar

| | hard link | soft link |
|---|---|---|
| directory’ga | yo’q | **ha** - keng tarqalgan holat: `/usr/lib/jvm/default -> java-17` |
| filesystem’lar orasida | yo’q | **ha** |
| (hali) mavjud bo’lmagan maqsadga | yo’q | ha - **osilgan** (dangling) link |
| maqsad o’chirilganda ham yashaydi | ha (u *aynan* faylning o’zi) | yo’q - osilib qoladi |
| maqsad almashtirilganda ham yashaydi (rm + yangi fayl) | yo’q (eski inode’ga ishora qiladi) | ha - nomga ergashadi |
| o’z inode’i, o’z ruxsatlari | yo’q | ha (lekin ruxsatlar ishlatilmaydi) |

## Nisbiy va absolyut maqsadlar

Link ichida saqlangan yo’l **so’zma-so’z**, link’ning o’z directory’siga
nisbatan ishlatiladi:

```bash
cd /opt/app
ln -s releases/v2 current              # nisbiy: /opt/app/current -> releases/v2 ; /opt/app/releases/v2 ga yechiladi
ln -s /opt/app/releases/v2 current     # absolyut
```

Nisbiy linklar butun daraxt ko’chirilganda saqlanib qoladi
(`mv /opt/app /srv/app` - `current` yonidagi `releases/v2` ni baribir
topadi); absolyut linklar esa link yolg’iz ko’chirilganda saqlanadi. Birga
ko’chadigan daraxt ichidagi linklar uchun nisbiyni, qat’iy tizim joylariga
ishoralar uchun absolyutni tanlang.

Klassik xato - nisbiy linkni noto’g’ri directory’dan yasash:

```bash
ln -s releases/v2 /opt/app/current     # / dan, lekin yo'l /opt/app ga nisbiy - bu yerda joyida
ln -s /opt/app/releases/v2 /opt/app/current   # /opt/app da bo'lmaganingizda eng xavfsizi
```

## Tekshirish va tuzatish

```bash
readlink current                       # nimaga ishora qilishi, so'zma-so'z
readlink -f current                    # to'liq yechilgan, absolyut, hamma linklarga ergashilgan
ls -l current                          # -> ko'rinadi; ko'p terminallarda qizil/miltillovchisi = osilgan
file current                           # "symbolic link to releases/v2" / "broken symbolic link to ..."
find /opt -xtype l                     # /opt ostidagi har bir osilgan symlink
ln -sfn releases/v3 current            # -f mavjudini almashtiradi; -n link-to-directory ichiga tushmaydi
rm current                             # linkni o'chiradi, maqsadni hech qachon (diqqat: oxirida qiya chiziq yo'q!)
```

:::warning
Directory’ga link ustida oxirida qiya chiziq bilan `rm current/` yoki
`rm -r
current` - ikkalasi ham maqsadning ichiga yetib borishi mumkin. `rm current`
(qiya chiziqsiz) faqat linkni o’chiradi. Va `current` allaqachon
directory’ga link bo’lganda `ln -s new current` maqsadning *ichida*
`current/new` yaratadi - `ln -sfn` dan foydalaning.
:::

## Linklarni tabiiy muhitda ko’rish

```bash
ls -l /etc/alternatives/ | head          # Debian'ning alternatives'i: versiyalar orasidan tanlaydigan symlink'lar
ls -l /etc/systemd/system/multi-user.target.wants/   # "enabled" unit'lar unit fayllariga symlink (5-hafta)
ls -l /dev/disk/by-uuid/                 # disklarning barqaror nomlari - /dev/sdX ga symlink'lar (11-hafta)
ls -l /bin                               # merged-/usr tizimlarda /bin -> usr/bin
```

Tizim konfiguratsiyasining yarmi - symlink’lar; `->` ni ravon o’qish -
kundalik ko’nikma.

:::exam-tip
"`/opt/app/bin/app-2.1` ga ishora qiluvchi `/usr/local/bin/app` symbolic
link yarating": `ln -s /opt/app/bin/app-2.1 /usr/local/bin/app`.
`ls -l /usr/local/bin/app` va `readlink -f` bilan tekshiring. Tartibni
eslang: **avval maqsad, keyin link nomi** - xuddi `cp source dest` kabi.
:::

## O’zingizni tekshiring

1. Soft link aslida nimani saqlaydi va uning maqsadi o’chirilganda nima
   bo’ladi?
2. Qachon nisbiy, qachon absolyut maqsadni ishlatasiz?
3. `ln -s new current` nega ba’zan `current/new` yaratadi va qaysi
   bayroqlar bunga yo’l qo’ymaydi?
