## Sysadmin’ga Git nega kerak

Konfiguratsiya - bu matn, versiya nazorati ostidagi matn esa siz diff qila
oladigan, qaytara oladigan va tushuntira oladigan matn. Repository’dagi
`/etc` "o’tgan seshanba nima o’zgardi va buni kim qildi" degan savolga
arxeologiyasiz javob beradi. LFCS obyektivlari asoslarni so’raydi:
repository yaratish yoki clone qilish, uning holatiga qarash, tarixini
o’qish.

```bash
sudo apt install git          # yoki: dnf install git
git --version
```

## Git’ga o’zingiz kimligingizni ayting

```bash
git config --global user.name "Ahmad Maxmudov"
git config --global user.email "ahmad@example.com"
git config --global init.defaultBranch main
git config --global core.editor vim
git config --list --show-origin        # har bir sozlama va u qaysi fayldan kelgani
```

Uchta daraja, har biri o’zidan oldingisini bekor qiladi: system
(`/etc/gitconfig`), global (`~/.gitconfig`), lokal (bitta repository’dagi
`.git/config`). Ism va email bo’lmasa, `git commit` bajarilmaydi.

## Yo’qdan repository

```bash
mkdir /srv/configs && cd /srv/configs
git init
# Initialized empty Git repository in /srv/configs/.git/
ls -a          # .git/ hammasini saqlaydi: objects, refs, config, HEAD
```

Working tree - siz ko’rib turgan fayllar; `.git/` - ular yonidagi
ma’lumotlar bazasi. `.git` ni o’chirsangiz, yana oddiy fayllar qoladi;
directory’ni nusxalasangiz, butun tarixni ham u bilan birga nusxalaysiz.

## Birovnikidan repository

```bash
git clone https://github.com/uzdevops/cka-roadmap.git
git clone git@github.com:uzdevops/cka-roadmap.git         # SSH orqali, o'z kalitingiz bilan
git clone https://github.com/org/repo.git /opt/repo       # tanlangan directory ichiga
git clone --depth 1 https://github.com/org/repo.git       # sayoz: faqat oxirgi commit, tez
git clone --branch v2.1 https://github.com/org/repo.git   # muayyan branch yoki tag
```

`clone` directory yaratadi, to’liq tarixni yuklab oladi, sukut bo’yicha
branch’ni checkout qiladi va manbani **origin** remote’i sifatida yozib
qo’yadi.

## Men qayerdaman? git status

```bash
git status
# On branch main
# Your branch is up to date with 'origin/main'.
# Changes not staged for commit:
#   modified:   nginx.conf
# Untracked files:
#   new-site.conf
git status -s          # qisqa: ' M nginx.conf', '?? new-site.conf'
git status -sb         # qisqa + branch qatori
```

`git status` - siz qolgan har bir buyruq orasida ishga tushiradigan
buyruq. U doim branch’ni, nima o’zgarganini, nima staged ekanini va Git
nimadan bexabar ekanini aytib turadi.

## Nima bo’ldi? git log

```bash
git log                                    # to'liq yozuvlar, eng yangisi birinchi
git log --oneline                          # har bir commit uchun bitta qator: qisqa hash + mavzu
git log --oneline --graph --all --decorate # branch'lar shakli
git log -5                                 # oxirgi beshtasi
git log --since="2 weeks ago" --until=yesterday
git log --author="Ahmad"
git log -p nginx.conf                      # bitta faylga kiritilgan har bir o'zgarish, diff'lari bilan
git log --stat                             # qaysi fayllar va qanchaga o'zgargani
git log --grep="fix"                       # commit xabarlari ichidan qidiradi
git show HEAD                              # eng yangi commit to'liq holda
git show a1b2c3d:nginx.conf                # fayl o'sha commit paytida qanday bo'lgan bo'lsa
```

`HEAD` - siz hozir turgan joy; `HEAD~1` - bitta commit orqada, `HEAD~3` -
uchta. Commit SHA hash bilan aniqlanadi; dastlabki 7-8 belgi yetarli.

## Farqlarga qarash

```bash
git diff                     # working tree staged'ga nisbatan (staged qilinmagan o'zgarishlar)
git diff --staged            # staged oxirgi commit'ga nisbatan (commit nimani yozib olishi)
git diff HEAD                # working tree oxirgi commit'ga nisbatan (hammasi)
git diff a1b2c3d..e4f5g6h    # ikkita commit orasida
git diff main..feature       # branch'lar orasida
git diff --stat
```

## Bu qatorni kim yozgan

```bash
git blame nginx.conf         # har bir qator o'z commit'i, muallifi va sanasi bilan
git blame -L 20,40 nginx.conf
```

Konfiguratsiyadagi biror qator jumboqqa aylanganda eng foydali buyruq.

:::tip
O’zingiz boshqaradigan mashinada `/etc` ni Git ostiga qo’ying (`etckeeper`
buni avtomatlashtiradi) - shunda har bir paket o’rnatilishi va har bir
qo’lda tahrirning changelog’ini tekinga olasiz. Usiz ham: qo’lda
tahrirlaydigan istalgan directory ishni boshlashdan oldin `git
init` va bitta commit’ga arziydi.
:::

## O’zingizni tekshiring

1. Working tree bilan `.git` directory orasidagi farq nima?
2. Qaysi buyruq nima o’zgarganini va Git qaysi fayllarni kuzatmasligini
   ko’rsatadi?
3. Bitta faylga kiritilgan har bir o’zgarishni diff’lari bilan qanday
   ko’rasiz?
