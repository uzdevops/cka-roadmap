## /etc/skel: yangi home nimadan boshlanadi

`useradd -m` home directory yaratganda, u `/etc/skel` mazmunini uning
ichiga **nusxalaydi** va hammasining egasini yangi user’ga o’zgartiradi.
Skel ichida nima bo’lsa, kelajakdagi har bir user o’shandan boshlaydi.

```bash
ls -la /etc/skel/
# .bash_logout  .bashrc  .profile
sudo useradd -m -s /bin/bash newuser
ls -la /home/newuser/          # o'sha uchta fayl, egasi newuser
```

Faqat **yangi** user’larga ta’sir qiladi - mavjud home’lar
o’zgartirilmaydi.

## Shablonni moslashtirish

```bash
sudo cp /etc/skel/.bashrc /etc/skel/.bashrc.orig       # asl nusxani saqlab qo'ying

sudo tee -a /etc/skel/.bashrc <<'EOF'

# --- kompaniya sukut sozlamalari ---
alias ll='ls -alF'
alias ..='cd ..'
export EDITOR=vim
export HISTTIMEFORMAT="%F %T "
EOF

sudo mkdir -p /etc/skel/.ssh /etc/skel/bin /etc/skel/Documents
sudo chmod 700 /etc/skel/.ssh
sudo tee /etc/skel/.vimrc <<'EOF'
set nu ts=4 sw=4 et ai
syntax on
EOF
sudo tee /etc/skel/README.txt <<'EOF'
Welcome. Company policy: no shared accounts, no passwords in files.
Support: helpdesk@example.com
EOF
```

Ruxsatlar fayllar bilan birga nusxalanadi, shuning uchun shablondagi
`chmod 700 /etc/skel/.ssh` har bir yangi user’ga to’g’ri qulflangan `.ssh`
beradi.

Uni sinab ko’ring:

```bash
sudo useradd -m -s /bin/bash testuser
sudo ls -la /home/testuser
sudo userdel -r testuser
```

## Qaysi skeleton va u qayerda sozlanadi

```bash
grep SKEL /etc/default/useradd
# SKEL=/etc/skel
grep -E "CREATE_HOME|UMASK|HOME_MODE" /etc/login.defs
sudo useradd -m -k /etc/skel-developers -s /bin/bash dev1     # bu user uchun boshqa shablon
```

Bir nechta shablon - `/etc/skel-developers`, `/etc/skel-contractors` -
ustiga `-k`: bitta mashina turli toifadagi user’larga aynan shu yo’l
bilan xizmat qiladi.

## Home directory ruxsatlari

```bash
grep HOME_MODE /etc/login.defs        # ko'p tizimlarda 0750; aks holda UMASK'dan olinadi
ls -ld /home/*
sudo chmod 750 /home/alice            # boshqalar uni ko'rib chiqa olmaydi
sudo chmod 700 /home/alice            # alice (va root) dan boshqa hech kim
```

`/etc/login.defs`’dagi `HOME_MODE` (yoki `UMASK`) `useradd -m` nimani
o’rnatishini hal qiladi. Sukut bo’yicha `755` home’lar har bir user
boshqa har bir user’ning fayllarini o’qiy oladi degani - umumiy mashinada
account’larni yaratishdan oldin `HOME_MODE 0750` qo’ying.

## Mavjud user’larni tuzatish

skel o’tmishga yeta olmaydi. Yangi faylni hammaga yoyish uchun:

```bash
for h in /home/*; do
    u=$(basename "$h")
    id "$u" &>/dev/null || continue
    sudo cp /etc/skel/.vimrc "$h/.vimrc"
    sudo chown "$u:$u" "$h/.vimrc"
done
```

Yoki yaxshirog’i, umumiy sozlamalarni `/etc/profile.d/` va
`/etc/bash.bashrc` ichiga qo’ying (oldingi dars) - tizim bo’ylab fayllar
hamma uchun, hozir ham, keyin ham amal qiladi va home’larga umuman
tegmaydi.

| Qayerga qo’yish | Qachon |
|---|---|
| `/etc/skel` | user tahrirlashi yoki o’chirishi mumkin bo’lgan **boshlang’ich nuqta** |
| `/etc/profile.d/`, `/etc/bash.bashrc` | hamma uchun, har doim amal qilishi kerak bo’lgan **siyosat** |

:::warning
`/etc/skel` ichiga hech qachon maxfiy SSH kaliti, token yoki parol
qo’ymang - kelajakdagi har bir user nusxa oladi va `/etc/skel`’ning o’zi
hammaga o’qish uchun ochiq. `/etc/skel/.ssh/authorized_keys` ichidagi
ochiq kalit qonuniy (administrator’ning yangi account’larga kirishi);
maxfiy kalit esa hech qachon emas.
:::

:::exam-tip
"Har bir yangi yaratilgan user home directory’sida X faylini olishini
ta’minlang" → X’ni `/etc/skel` ichiga qo’ying, so’ng test user yaratib,
home’ni ro’yxatlab va user’ni `userdel -r` bilan o’chirib buni isbotlang.
Agar topshiriqda "hamma user’lar, jumladan mavjudlari ham" deyilgan
bo’lsa, faqat skel yetarli emas - uni mavjud home’larga ham nusxalang va
shuni aytib qo’ying.
:::

## O’zingizni tekshiring

1. `/etc/skel` qachon ishlatiladi va undagi o’zgarish qaysi user’larga
   ta’sir qiladi?
2. Developer’larga boshqa user’lardan farqli shablonni qanday berasiz?
3. Sozlama mavjudlari bilan birga har bir user’ga amal qilishi kerak
   bo’lsa, u qayerda turishi kerak?
