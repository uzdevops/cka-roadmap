## Fayl bo’lishi mumkin bo’lgan uchta joy

```
  working tree  ──git add──▶  staging area (index)  ──git commit──▶  repository (tarix)
     tahrirlar               keyingi commit nimani o'z ichiga oladi        doimiy
```

Git’ning g’ayrioddiy oraliq bosqichi - **index** - o’zgarishlaringizning
*bir qismini* commit qilib, qolganini qilmaslik imkonini beradi; shu
tufayli beshta narsani tahrirlagan bo’lsangiz ham, bitta commit bitta
mantiqiy o’zgarish bo’lib qolaveradi.

```bash
git status
# Changes to be committed:      <- staged (index)
#   modified: a.conf
# Changes not staged for commit:  <- faqat working tree'da o'zgargan
#   modified: b.conf
# Untracked files:              <- Git buni hech qachon ko'rmagan
#   c.conf
```

## Staging

```bash
git add nginx.conf                 # bitta fayl
git add site1.conf site2.conf
git add .                          # joriy directory ostidagi hamma narsa
git add -A                         # repository'dagi hamma narsa, o'chirishlar bilan birga
git add '*.conf'                   # pattern bo'yicha
git add -u                         # faqat Git allaqachon kuzatayotgan fayllar
git add -p                         # interaktiv, hunk-hunk - reviewer odati
git restore --staged nginx.conf    # unstage qiladi (tahrir saqlanadi)   [eskisi: git reset HEAD file]
```

## Commit qilish

```bash
git commit -m "Increase nginx worker_connections to 4096"
git commit                          # uzunroq xabar uchun $EDITOR ochadi
git commit -a -m "message"          # barcha KUZATILAYOTGAN o'zgarishlarni stage qilib commit qiladi (untracked'ni o'tkazib yuboradi)
git commit --amend -m "better message"      # oxirgi commit'ni almashtiradi (xabar va/yoki mazmun)
git commit --amend --no-edit                # staged o'zgarishlarni oxirgi commit'ga qo'shadi, xabarni saqlaydi
```

Yaxshi xabar: qisqa, buyruq shaklidagi mavzu qatori (~50 belgidan kam),
bo’sh qator, keyin nima uchun qilingani - nima qilingani emas, uni diff
allaqachon ko’rsatib turibdi.

```
Raise nginx worker_connections to 4096

The 512 default was capping concurrent uploads during the evening
peak; ss showed the accept queue filling. 4096 fits the file
descriptor limit set in the systemd unit.
```

## Har bir bosqichda orqaga qaytarish

| Vaziyat | Buyruq |
|---|---|
| staged qilinmagan tahrirni tashlash | `git restore file` (eskisi: `git checkout -- file`) |
| unstage qilish, tahrirni saqlash | `git restore --staged file` |
| commit qilinmagan hamma narsani tashlash | `git restore .` keyin `git clean -fd` (untracked) |
| oxirgi commit’ni tuzatish | `git commit --amend` |
| oxirgi commit’ni bekor qilish, o’zgarishlar staged qolsin | `git reset --soft HEAD~1` |
| oxirgi commit’ni bekor qilish, o’zgarishlar staged bo’lmasin | `git reset HEAD~1` (mixed, sukut bo’yicha) |
| oxirgi commit’ni bekor qilish va o’zgarishlarni **tashlab yuborish** | `git reset --hard HEAD~1` |
| boshqalarda allaqachon bor commit’ni bekor qilish | `git revert a1b2c3d` (yangi, teskari commit yaratadi) |
| faylni commit paytidagi holatida qaytarib olish | `git checkout a1b2c3d -- file` / `git restore --source=a1b2c3d file` |

:::warning
`git reset --hard` va `git clean -fd` ishni butunlay o’chiradi - hech qachon
commit qilinmagan o’zgarishlar uchun undo yo’q. Avval commit qiling (hatto
tashlab yuboriladigan "wip" commit bo’lsa ham); commit qilingan xatoni esa
`git reflog` bilan doim tiklash mumkin.
:::

## Fayllarni e’tiborsiz qoldirish

```bash
cat > .gitignore <<'EOF'
*.log
*.swp
secrets.env
.cache/
EOF
git add .gitignore && git commit -m "Add gitignore"
git check-ignore -v somefile        # qaysi qoida uni e'tiborsiz qoldiryapti
git rm --cached secrets.env         # allaqachon commit qilingan faylni kuzatishni to'xtatadi (diskda qoladi)
```

`.gitignore` faqat **untracked** fayllarga ta’sir qiladi; allaqachon commit
qilingan fayl siz `git rm --cached` qilmaguningizcha kuzatilaveradi. Bir
marta commit qilingan sir esa tarixda qolib ketadi - uni o’chirishga
urinish o’rniga almashtiring.

## Ko’chirish va o’chirish

```bash
git mv old.conf new.conf           # nomini o'zgartiradi va stage qiladi
git rm old.conf                    # o'chiradi va o'chirishni stage qiladi
git rm -r olddir/
git rm --cached file               # kuzatishdan chiqaradi, diskda qoldiradi
```

## Commit nima bo’lishini ko’rish

```bash
git diff --staged                  # `git commit` aynan nimani yozib olishi
git status -sb
git commit --dry-run -a
```

:::exam-tip
LFCS’dagi Git topshiriqlari kichik: repository yaratish, fayllarni
qo’shish, berilgan xabar bilan commit qilish, log’ni ko’rsatish.
`git init`, `git add .`, `git commit -m
"..."`, `git log --oneline`. Yangi mashinada birinchi bo’lib
`git config user.email` ni eslang - usiz commit bajarilmaydi va bu
nosozlikni repository muammosi deb noto’g’ri tushunish oson.
:::

## O’zingizni tekshiring

1. Fayl bo’lishi mumkin bo’lgan uchta holat qaysilar va uni birinchi
   ikkitasi orasida qaysi buyruq ko’chiradi?
2. Tahrirni yo’qotmasdan faylni qanday unstage qilasiz?
3. Nega boshqalar allaqachon pull qilgan commit uchun `git revert` to’g’ri
   vosita?
