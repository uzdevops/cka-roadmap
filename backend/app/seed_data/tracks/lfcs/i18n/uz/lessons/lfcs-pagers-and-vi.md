## Pager’lar: bir ekrandan ko’pini o’qish

```bash
less /var/log/syslog
journalctl -u nginx | less           # less - man va journalctl allaqachon ishlatadigani
more file                            # eskisi: faqat oldinga, chiqish uchun q
```

`less` ichida:

| Klavish | Nima qiladi |
|---|---|
| `Space` / `b` | sahifa pastga / yuqoriga |
| `j` `k` yoki strelkalar | qator pastga / yuqoriga |
| `g` / `G` | boshiga / oxiriga |
| `/pattern` / `?pattern` | oldinga / orqaga qidirish; `n` `N` keyingi / oldingi |
| `F` | kuzatish (`tail -f` kabi); to’xtatish uchun Ctrl-C, keyin `q` |
| `-N` (yoki `less -N` bilan boshlash) | qator raqamlari |
| `-S` | uzun qatorlarni o’ramaslik; `-i` registrga sezgir bo’lmagan qidiruv |
| `h` | yordam; `q` chiqish |
| `v` | faylni shu pozitsiyada `$EDITOR` ichida ochish |

`less -R` ranglarni saqlaydi (`ls --color=always | less -R`); `less +F file`
kuzatish rejimida boshlanadi; `less +/pattern file` birinchi moslikdan
boshlanadi.

## vi: omon qolishga yetadigani

Imtihon mashinasida `vi`/`vim` bor (odatda `nano` ham). Topshiriqda
"/etc/fstab’ni tahrirlang" deyiladi va siz kirib, bitta qatorni
o’zgartirib, xatosiz chiqib ketishingiz kerak. Uchta rejim:

```
   NORMAL  ──i, a, o──▶  INSERT  (matn yoziladi)
     ▲                       │
     └────────Esc────────────┘
   NORMAL  ──:──▶  COMMAND-LINE  (:w, :q, :s)
```

Siz **normal** rejimda boshlaysiz (klavishlar - buyruqlar). `i` kursordan
oldin insert rejimiga kiradi, `a` keyin, `o` pastda yangi qator ochadi,
`O` yuqorida. **Esc** doim normal rejimga qaytaradi. `:` buyruqni
boshlaydi.

### Saqlash va chiqish

| | |
|---|---|
| `:w` | saqlash |
| `:q` | chiqish (saqlanmagan bo’lsa rad etadi) |
| `:wq` yoki `ZZ` | saqlash va chiqish |
| `:q!` | saqla**masdan** chiqish |
| `:w newname` | boshqa nom bilan saqlash |
| `:wq!` | majburan saqlash (masalan, o’zingizga tegishli read-only fayl); sudo’siz ochilgan root fayli uchun `:w !sudo tee %` |

### Harakatlanish (normal rejim)

`h j k l` (yoki strelkalar), `0` / `$` qator boshi/oxiri, `w` / `b` so’z
oldinga/orqaga, `gg` / `G` boshi/oxiri, `:42` 42-qator, `Ctrl-f` /
`Ctrl-b` sahifa.

### Tahrirlash (normal rejim)

| Klavish | Nima qiladi |
|---|---|
| `x` | belgini o’chirish |
| `dd` | qatorni o’chirish (kesish); `5dd` besh qator; `dw` bir so’z; `D` qator oxirigacha |
| `yy` | qatordan nusxa olish (yank); `5yy` |
| `p` / `P` | keyin / oldin qo’yish |
| `u` | undo; `Ctrl-r` redo |
| `.` | oxirgi o’zgarishni takrorlash |
| `r` | bitta belgini almashtirish; `R` ustiga yozish rejimi |
| `cw` | so’zni o’zgartirish (o’chirish + insert); `cc` butun qator |
| `J` | qatorlarni birlashtirish |
| `>>` / `<<` | chekintirish / chekinishni kamaytirish |

### Qidirish va almashtirish

| | |
|---|---|
| `/pattern` `n` `N` | qidirish; keyingi; oldingi |
| `:s/old/new/` | shu qatordagi birinchisi |
| `:s/old/new/g` | shu qatordagi hammasi |
| `:%s/old/new/g` | **butun fayl** |
| `:%s/old/new/gc` | tasdiqlash bilan |
| `:10,20s/^/#/` | 10-20-qatorlarni izohga aylantirish |
| `:g/pattern/d` | mos keladigan har bir qatorni o’chirish |
| `:noh` | qidiruv belgilashini tozalash |

### Yordam beradigan sozlamalar

```
:set nu            qator raqamlari      :set nonu
:set paste         qo'yishdan oldin     :set nopaste
:set ts=2 sw=2 et  tab → 2 bo'sh joy (YAML uchun)
:set list          tab va oxirgi bo'sh joylarni ko'rsatish
:syntax on
```

Ularni `~/.vimrc` fayliga yozib doimiy qiling: `set nu ts=4 sw=4 et`.

### Ikki fayl va yordam

`:e other` boshqasini ochadi, `:bn` keyingi buffer, `vimdiff a b`,
`:help :s`, `vimtutor` (30 daqiqa, bu yo’nalishdagi eng yaxshi sarmoya).

## nano, agar boshqa iloj bo’lmasa

`nano file`: yozing; **Ctrl-O** saqlash, **Ctrl-X** chiqish, **Ctrl-W**
qidirish, **Ctrl-K** qatorni kesish, **Ctrl-U** qo’yish, **Ctrl-\**
almashtirish. Yorliqlar ekranda turadi. Fayl bo’ylab tahrirlash uchun
sekinroq, bitta qator uchun yetarli.

:::exam-tip
Aynan shularni refleksga aylanguncha mashq qiling: `vi file` → `/pattern`
→ `cw` yoki `dd` yoki `o` → Esc → `:wq`. Va biror narsa noto’g’ri
ketganda `:q!`. Imtihondagi ko’pchilik tahrir - config fayldagi bitta
qator; `:%s/^#Port 22/Port 2222/` keyin `:wq` - besh soniya. Agar vi
o’zini noto’g’ri tutsa, siz noto’g’ri rejimdasiz - Esc’ni ikki marta
bosing va buyruqni qaytadan boshlang.
:::

## O’zingizni tekshiring

1. `less` ichida pattern’ni qanday qidirasiz va keyingi moslikka qanday
   o’tasiz?
2. vi’da: qatorni o’chirish, undo qilish va saqlamasdan chiqish
   klavishlari.
3. Butun fayl bo’yicha har bir `foo` o’rniga `bar` yozadigan buyruq.
