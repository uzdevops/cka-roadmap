## User ortidagi fayllar

Buyruqlardan oldin - ular tahrirlaydigan uchta fayl:

```bash
grep ahmad /etc/passwd
# ahmad:x:1000:1000:Ahmad Maxmudov,,,:/home/ahmad:/bin/bash
#   │   │  │    │          │            │           └── login shell
#   │   │  │    │          │            └── home directory
#   │   │  │    │          └── GECOS: to'liq ism va aloqa maydonlari
#   │   │  │    └── asosiy GID
#   │   │  └── UID
#   │   └── 'x' = parol /etc/shadow ichida
#   └── username
sudo grep ahmad /etc/shadow
# ahmad:$y$j9T$...:20321:0:99999:7:::
#   │        │       │   │   │   └── tugashidan necha kun oldin ogohlantirish
#   │        │       │   │   └── maksimal yosh (parol N kundan keyin almashtirilishi shart)
#   │        │       │   └── minimal yosh
#   │        │       └── oxirgi o'zgarish (1970-01-01 dan beri kunlar)
#   │        └── hash ($y$ = yescrypt, $6$ = SHA-512); '!' yoki '*' = login o'chirilgan
#   └── username
```

`/etc/passwd` hammaga o’qish uchun ochiq (ko’p dasturlar UID’larni
nomlarga moslashtiradi); `/etc/shadow` esa `640 root:shadow` va hash’larni
saqlaydi.

## User yaratish

```bash
sudo useradd -m -s /bin/bash alice            # -m home directory yaratadi (Debian'da shart!)
sudo passwd alice                              # parolni o'rnatish
sudo useradd -m -s /bin/bash -c "Alice Karimova" -G sudo,developers alice
sudo useradd -m -u 1500 -g developers -G docker -d /srv/alice -s /bin/bash alice
sudo useradd -r -s /usr/sbin/nologin -M myapp  # SYSTEM account: login yo'q, home yo'q
sudo adduser alice                             # Debian'ning interaktiv wrapper'i - hammasini so'raydi
```

| Flag | Nimani belgilaydi |
|---|---|
| `-m` | home directory yaratish (`/etc/skel` nusxalanadi) |
| `-M` | home **yaratilmasin** |
| `-d /path` | home directory yo’li |
| `-s /bin/bash` | login shell (login’ni taqiqlash uchun `/usr/sbin/nologin` yoki `/bin/false`) |
| `-u 1500` | UID |
| `-g devs` | **asosiy** guruh |
| `-G a,b,c` | qo’shimcha guruhlar |
| `-c "Full Name"` | GECOS izohi |
| `-e 2026-12-31` | account’ning tugash sanasi |
| `-r` | system account (UID 1000’dan past, ageing yo’q) |
| `-k /etc/skel` | qaysi skeleton directory nusxalanadi |

Sukut bo’yicha qiymatlar `/etc/default/useradd` va `/etc/login.defs`
fayllaridan olinadi (`UID_MIN`, `CREATE_HOME`, `PASS_MAX_DAYS`, `UMASK`):

```bash
useradd -D                       # sukut bo'yicha qiymatlarni ko'rsatish
sudo useradd -D -s /bin/bash     # sukut qiymatini o'zgartirish
grep -E "^(UID_MIN|PASS_MAX_DAYS|CREATE_HOME|UMASK)" /etc/login.defs
```

## O’zgartirish

```bash
sudo usermod -s /usr/sbin/nologin alice        # shell'ni o'zgartirish
sudo usermod -aG docker alice                  # guruhga QO'SHISH - bu yerda -a hal qiluvchi
sudo usermod -G docker alice                   # -a BO'LMASA: HAMMA qo'shimcha guruhni almashtiradi
sudo usermod -g developers alice               # asosiy guruhni o'zgartirish
sudo usermod -l alice_k alice                  # login nomini o'zgartirish
sudo usermod -d /srv/alice -m alice            # yangi home, -m mazmunini ko'chiradi
sudo usermod -c "Alice K." alice
sudo usermod -e 2026-12-31 alice               # account muddati tugaydi
sudo usermod -L alice                          # parolni QULFLASH (hash oldiga ! qo'yadi)
sudo usermod -U alice                          # qulfni ochish
sudo usermod -L -e 1 alice                     # qulflash VA muddatini tugatish - to'g'ri "bu account'ni o'chirish"
```

:::warning
`-a` siz ishlatilgan `usermod -G` user’ni ro’yxatda ko’rsatilmagan har bir
guruhdan indamay olib tashlaydi - `sudo` ham shular ichida. Bu -
administrator’ni o’z mashinasidan qulflab qo’yishning eng keng tarqalgan
yo’li. Doim `usermod -aG` ishlating va keyin `groups alice` bilan
tekshiring.
:::

## Parollar va ageing

```bash
sudo passwd alice                # o'rnatish/o'zgartirish
sudo passwd -l alice             # qulflash; -u qulfni ochish
sudo passwd -d alice             # parolni o'chirish (bo'sh login - xavfli)
sudo passwd -e alice             # hozir muddatini tugatish: keyingi login'da almashtirish shart
sudo passwd -S alice             # holat: alice P 08/19/2026 0 99999 7 -1  (P=ishlaydi, L=qulflangan, NP=yo'q)
echo 'alice:NewPass123' | sudo chpasswd        # skript bilan, bittasiga yoki ko'piga

sudo chage -l alice              # ageing sozlamalarini ko'rsatish
sudo chage -M 90 -m 7 -W 14 alice    # maksimum 90 kun, almashtirishlar orasida minimum 7, 14 kun oldin ogohlantirish
sudo chage -E 2026-12-31 alice       # account'ning tugash sanasi
sudo chage -I 30 alice               # inactive: parol muddati tugagach N kundan keyin o'chirish
sudo chage -d 0 alice                # keyingi login'da almashtirishga majburlash
```

`passwd -l` faqat **parolni** qulflaydi (kalit asosidagi SSH baribir
ishlayveradi); `chage -E` yoki `usermod -e` esa **account** muddatini
tugatadi (hech narsa ishlamaydi). "Bu user’ni butunlay o’chirish" uchun
ikkalasini ham qiling va shell’ni `nologin` ga almashtiring.

## O’chirish

```bash
sudo userdel alice                # account'ni o'chirish, home directory'ni SAQLAB QOLISH
sudo userdel -r alice             # home directory va mail spool'ni ham o'chirish
sudo userdel -f alice             # tizimga kirgan bo'lsa ham
```

O’chirishdan oldin u nimalarga egalik qilishini toping - boshqa joydagi
fayllar yalang’och UID bilan "yetim" bo’lib qoladi:

```bash
sudo find / -xdev -user alice -ls 2>/dev/null | head
sudo find / -xdev -nouser 2>/dev/null            # egasi endi mavjud bo'lmagan fayllar
sudo pkill -u alice                               # avval uning process'larini tugating
```

## Ko’rib chiqish

```bash
id alice                          # uid, gid, guruhlar
groups alice
getent passwd alice               # lokal VA masofaviy (LDAP) user'lar uchun ishlaydi
getent passwd | wc -l
getent shadow alice
awk -F: '$3>=1000 && $3<65534 {print $1}' /etc/passwd     # odam user'lar
lslogins; lslogins -u
who; w; last alice
sudo pwck; sudo grpck                             # fayllarning izchilligini tekshirish
```

:::exam-tip
Topshiriqning so’zlarini diqqat bilan o’qing: "X user’ini home directory
**bilan** yarating" (`-m`), "**login’siz**" (`-s /usr/sbin/nologin`), "Y
guruhi a’zosi" (yaratishda `-G Y`, keyin `-aG Y`), "parol har 60 kunda
almashtirilishi kerak" (`chage -M 60`), "account DATE’da muddati tugaydi"
(`chage -E DATE` yoki `useradd -e`). Har birini `id`, `getent passwd`,
`chage -l`, `passwd -S` bilan tekshiring.
:::

## O’zingizni tekshiring

1. `/etc/passwd` qatorining yettita maydoni qaysilar?
2. Nega `usermod -aG` `usermod -G`’dan farq qiladi va nima buziladi?
3. Qaysi buyruqlar parolni qulflaydi, account muddatini tugatadi va
   keyingi login’da parolni almashtirishga majbur qiladi?
