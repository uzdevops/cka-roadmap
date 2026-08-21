## Qaysi fayl qachon o’qiladi

Shell **qanday** ishga tushganiga qarab turli startup fayllarni o’qiydi.
Buni to’g’ri bilish "PATH’im SSH’da ishlaydi, lekin cron’da yo’q" holati
bilan o’zgaruvchilar siz kutgan joyda turadigan tizim orasidagi farqdir.

| Shell turi | Nima ishga tushiradi | Nimani o’qiydi (tartib bilan) |
|---|---|---|
| **login** | `ssh user@host`, TTY login, `su -`, `bash -l` | `/etc/profile` → `/etc/profile.d/*.sh` → `~/.bash_profile`, `~/.bash_login`, `~/.profile`’dan birinchisi |
| **interaktiv, login emas** | desktop’da terminal ochish, `bash` | `/etc/bash.bashrc` → `~/.bashrc` |
| **interaktiv emas** | skript, cron, `ssh host 'cmd'` | **hech qaysisi** - faqat o’rnatilgan bo’lsa `$BASH_ENV` |

Aynan uchinchi qator tufayli cron topshiriqlariga absolyut yo’llar kerak:
sizning fayllaringizdan birortasi ham o’qilmaydi.

```bash
shopt -q login_shell && echo "login shell" || echo "not a login shell"
echo $0            # -bash (boshida chiziqcha) = login shell
```

## Tizim bo’ylab amal qiladigan fayllar

| Fayl | Nima uchun |
|---|---|
| `/etc/profile` | login shell’lar, butun tizim bo’ylab. Uni tahrirlamang - u keyingisini source qiladi |
| `/etc/profile.d/*.sh` | **tizim bo’ylab sozlamalaringiz uchun joy**, har bir mavzuga bitta fayl |
| `/etc/bash.bashrc` (Debian) / `/etc/bashrc` (RHEL) | interaktiv, login bo’lmagan shell’lar: alias’lar, prompt |
| `/etc/environment` | **skript emas**: oddiy `KEY=value` qatorlari, har bir login uchun PAM o’qiydi (grafik login va su ham) |

```bash
cat /etc/environment
# PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
# LANG="en_US.UTF-8"
```

`export` yo’q, `$VAR` kengaytirilmaydi, shell sintaksisi yo’q - PAM uni
so’zma-so’z o’qiydi. Bu `LANG` va statik `PATH` uchun to’g’ri joy,
hisoblanadigan har qanday narsa uchun esa noto’g’ri joy.

```bash
sudo tee /etc/profile.d/company.sh <<'EOF'
export EDITOR=vim
export HISTTIMEFORMAT="%F %T "
export PATH="$PATH:/opt/company/bin"
umask 027
EOF
sudo chmod 644 /etc/profile.d/company.sh
```

O’zgarishlar **keyingi login’da** kuchga kiradi; hozir esa `source
/etc/profile.d/company.sh` bilan sinab ko’ring.

## Har bir user’ning o’z fayllari

| Fayl | Kim o’qiydi |
|---|---|
| `~/.bash_profile` yoki `~/.profile` | login shell’lar |
| `~/.bashrc` | interaktiv, login bo’lmagan shell’lar - va odatda uni `~/.profile` ham source qiladi |
| `~/.bash_logout` | logout paytida |
| `~/.bash_history` | tarix, chiqishda yoziladi |

Debian konvensiyasi: `~/.profile` ichida

```bash
if [ -n "$BASH_VERSION" ] && [ -f "$HOME/.bashrc" ]; then . "$HOME/.bashrc"; fi
```

bo’ladi, shuning uchun `~/.bashrc` ikkala holatda ham o’qiladi.
**export**’larni `~/.profile`’ga qo’ying (ular baribir bolalarga meros
bo’ladi), **alias’lar, prompt, shell parametrlari**ni esa `~/.bashrc`’ga
(ular meros bo’lmaydi, shuning uchun har bir shell’da o’rnatilishi kerak).

## O’zgaruvchilar

```bash
VAR=value                   # faqat shu shell
export VAR=value            # shu shell VA uning bolalari
export PATH="$PATH:/opt/bin"
unset VAR
env | sort | less           # eksport qilingan o'zgaruvchilar
set | less                  # hamma o'zgaruvchilar va funksiyalar
printenv PATH
echo "${EDITOR:-vim}"       # sukut qiymati bilan
```

Keng tarqalganlari: `PATH`, `HOME`, `USER`, `SHELL`, `PWD`, `LANG`,
`LC_ALL`, `EDITOR`, `PS1`, `TERM`, `TZ`, `HISTSIZE`, `HISTCONTROL`.

```bash
export PS1='\u@\h:\w\$ '            # user@host:dir$
export HISTSIZE=10000 HISTFILESIZE=20000 HISTCONTROL=ignoredups:erasedups
export TZ=Asia/Tashkent              # shu shell uchun vaqt zonasi
```

## Locale

```bash
locale                       # joriy sozlamalar
locale -a | head             # mavjud locale'lar
sudo locale-gen en_US.UTF-8  # Debian
sudo update-locale LANG=en_US.UTF-8
localectl status; sudo localectl set-locale LANG=en_US.UTF-8      # systemd, /etc/locale.conf ga yozadi
```

Locale saralashni (`sort`), o’nlik ajratgichlarni va buyruq xabarlarini
o’zgartiradi - chiqishni tahlil qiladigan skriptlar barqarorlik uchun
`LC_ALL=C` o’rnatgani ma’qul.

## Qo’llash va nosozlikni bartaraf etish

```bash
source ~/.bashrc          # yoki: . ~/.bashrc  - joriy shell'da qayta o'qish
exec bash -l              # shell'ni yangi login shell bilan almashtirish
bash -x -l -c exit 2>&1 | head -40      # qaysi startup fayllar o'qilishini kuzatish
env -i bash --noprofile --norc          # HECH NARSAsiz shell - cron muhitini takrorlaydi
ssh localhost 'echo $PATH'              # interaktiv bo'lmagan PATH - ko'pincha sizdagidan qisqaroq
```

:::warning
`/etc/profile` yoki `/etc/profile.d/*.sh` ichidagi sintaksis xatosi har
bir user uchun login’ni buzishi mumkin - SSH orqali kiradigan root ham
shular ichida. Saqlashdan oldin `bash -n file` bilan sinang, tahrirlash
vaqtida ikkinchi root sessiyasini ochiq qoldiring va `/etc/profile`’ning
o’zini tahrirlagandan ko’ra `profile.d` ichida yangi fayl yarating.
:::

:::exam-tip
"X o’zgaruvchisini hamma user’lar uchun tizim bo’ylab o’rnating" →
`/etc/profile.d/` ichida `export X=...` yozilgan fayl (yoki statik qiymat
uchun `/etc/environment`’dagi qator). "Bitta user uchun" →
`~/.profile`/`~/.bashrc`. Tekshirishni qaytadan login qilib (yoki
`su - user -c 'echo $X'`) bajaring, joriy shell’dagi `echo $X` bilan emas
- u hech narsani qayta o’qimagan.
:::

## O’zingizni tekshiring

1. Login shell qaysi fayllarni o’qiydi va cron topshirig’i qaysilarini?
2. `/etc/environment` `/etc/profile.d/*.sh`’dan nimasi bilan farq qiladi?
3. Alias’lar qayerga yoziladi va nega `~/.profile`’ga emas?
