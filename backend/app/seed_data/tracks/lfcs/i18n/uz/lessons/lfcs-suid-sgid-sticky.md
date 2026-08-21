## rwx dan tashqari uchta bit

To’rtinchi octal raqam. Har bir bit fayllarda bir narsani,
directory’larda boshqa narsani anglatadi va ulardan ikkitasi `ls -l` da
`x` turishi kerak bo’lgan joyda `s` yoki `t` sifatida ko’rinadi.

| Bit | Octal | Bajariladigan faylda | Directory’da |
|---|---|---|---|
| **SUID** (set-user-ID) | `4000` | kim ishga tushirishidan qat’i nazar, **fayl egasi nomidan** ishlaydi | hech narsa (Linux’da e’tiborga olinmaydi) |
| **SGID** (set-group-ID) | `2000` | **fayl guruhi nomidan** ishlaydi | yangi fayllar va ichki directory’lar **directory guruhini meros oladi** (ichki directory’lar SGID’ni ham oladi) |
| **sticky** | `1000` | hech narsa (tarixiy) | faylni faqat uning **egasi** (yoki directory egasi, yoki root) o’chira yoki nomini o’zgartira oladi |

## SUID: misol sifatida passwd

```bash
ls -l /usr/bin/passwd
# -rwsr-xr-x 1 root root 68208 ... /usr/bin/passwd
```

`/etc/shadow` - root’ga tegishli `rw-r-----` fayl. Oddiy user unga yoza
olmaydi, lekin `passwd` unga o’z parolini o’zgartirish imkonini beradi -
chunki `passwd` SUID root: kim ishga tushirishidan qat’i nazar, **jarayon
root’ning effective UID’i bilan ishlaydi**. Egasining `x` o’rnidagi `s` -
o’sha bit.

```bash
chmod u+s file      # yoki chmod 4755 file
ls -l file          # -rwsr-xr-x
```

Katta **`S`** - bit qo’yilgan, lekin uning ostidagi execute biti yo’q
degani; ma’nosiz, odatda xato (`chmod 4644`).

SUID binary’lar - imtiyozni oshirishning klassik sathi: shell chaqirishga
majburlash mumkin bo’lgan bittasi root beradi. Ularni audit qiling:

```bash
find / -perm -4000 -type f 2>/dev/null           # har bir SUID fayl
find / -perm -2000 -type f 2>/dev/null           # SGID fayllar
find / -perm /6000 -type f 2>/dev/null           # ikkalasidan biri
```

(`-perm -4000` = "hech bo’lmaganda shu bitlar bor"; `-perm /6000` =
"biror biri".)

## Directory’da SGID: umumiy loyiha papkalari

```bash
mkdir /srv/project; chgrp devs /srv/project; chmod 2775 /srv/project
ls -ld /srv/project
# drwxrwsr-x 2 root devs 4096 ... /srv/project
touch /srv/project/a; ls -l /srv/project/a
# -rw-rw-r-- 1 ahmad devs ...              <- guruh devs, ahmadning asosiy guruhi emas
```

SGID’siz alice yaratgan fayl alice’ning asosiy guruhini oladi va bob unga
yoza olmaydi. SGID bilan har bir fayl `devs` ni oladi va (umask `002`
bo’lganda) guruh bir-birining ishini tahrirlay oladi. Bu - "guruh
birgalikda foydalanadigan directory" so’roviga **standart javob**.

**Bajariladigan faylda** SGID uni fayl guruhi nomidan ishlatadi - kamroq
uchraydi, lekin masalan `/usr/bin/wall` SGID `tty` bo’lgani uchun
hammaning terminaliga yoza oladi.

## Sticky: /tmp

```bash
ls -ld /tmp
# drwxrwxrwt 10 root root 4096 ... /tmp
```

`/tmp` hamma yoza oladigan (`777`) - har kim fayl yarata oladi - lekin `t`
faqat **o’zingiznikini** o’chira olasiz degani. Usiz `777` istalgan
user’ga istalgan boshqa user’ning vaqtinchalik fayllarini o’chirishga
ruxsat bergan bo’lardi.

```bash
chmod +t /srv/dropbox      # yoki chmod 1777
ls -ld /srv/dropbox        # drwxrwxrwt
```

Katta **`T`**: sticky qo’yilgan, lekin other uchun `x` yo’q - bu ham
odatda xato.

## To’rtta raqamni o’qish

| Rejim | Ma’nosi |
|---|---|
| `4755` | SUID, `rwxr-xr-x` - SUID root dastur |
| `2775` | SGID, `rwxrwxr-x` - guruh loyihasi directory’si |
| `1777` | sticky, `rwxrwxrwx` - umumiy vaqtinchalik directory |
| `3775` | SGID + sticky - guruhga umumiy va faqat o’zinikini o’chirish |
| `6755` | bajariladigan faylda SUID + SGID |

Simvolik: `u+s`, `g+s`, `+t`; olib tashlash uchun `u-s`, `g-s`, `-t`.

:::exam-tip
"X guruhi birgalikda foydalanadigan, ichida yaratilgan fayllar X ga
tegishli bo’ladigan directory yarating" → `chgrp X` dan keyin `chmod 2770`
(yoki `2775`); fayl yaratib, uning guruhini o’qib tekshiring. "User’lar
yarata olsin, lekin faqat o’zinikini o’chira olsin" → `chmod 1777`.
"Barcha SUID fayllarni topib, ro’yxatini saqlang" →
`find / -perm -4000 -type f > file`. Tekshiruvingiz - `ls -l` dagi `s`/`t`.
:::

## O’zingizni tekshiring

1. `/etc/shadow` unga yozish uchun ochiq bo’lmasa ham, oddiy user nega
   o’z parolini o’zgartira oladi?
2. Directory’da SGID nima qiladi va u qaysi muammoni hal qiladi?
3. `drwxrwxrwt` sizga directory’dagi faylni kim o’chira olishi haqida
   nima aytadi?
