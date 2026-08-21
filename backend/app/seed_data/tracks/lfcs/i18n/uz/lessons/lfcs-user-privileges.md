## sudo: root, bir vaqtda bitta buyruq

`sudo` buyruqni boshqa user nomidan (sukut bo’yicha root) `/etc/sudoers`
ichidagi qoidalarga muvofiq bajaradi. U har bir ishlatilishini logga
yozadi, **chaqirayotgan user’ning** o’z parolini so’raydi va bitta
binary’gacha toraytirilishi mumkin - shuning uchun u root parolini
bo’lishishning o’rnini egalladi.

```bash
sudo apt update                    # root sifatida
sudo -u postgres psql              # boshqa user sifatida
sudo -i                            # root LOGIN shell (root muhiti, root home'i)
sudo -s                            # sizning muhitingizni saqlagan root shell
sudo -l                            # menga nimani bajarishga ruxsat bor?
sudo -l -U alice                   # alice'ga nimaga ruxsat bor?
sudo -k                            # keshlangan ma'lumotlarni hozir unutish
sudo -v                            # timestamp'ni yangilash
sudo !!                            # oldingi buyruqni sudo bilan qayta bajarish (bash tarixi)
```

## Qoidalarni tahrirlash: doim visudo

```bash
sudo visudo                                    # /etc/sudoers ni saqlashda SINTAKSIS TEKSHIRUVI bilan tahrirlaydi
sudo visudo -f /etc/sudoers.d/developers       # drop-in fayl, afzal ko'riladigan joy
sudo visudo -c                                 # butun konfiguratsiyani tekshirish
```

:::warning
`/etc/sudoers`’ni hech qachon oddiy tahrirlagich bilan tahrirlamang.
Sintaksis xatosi `sudo`’ni **umuman** ishlamaydigan qilib qo’yadi va agar
root’da parol bo’lmasa (Ubuntu’da sukut holat), siz administratsiyadan
butunlay uzilib qolasiz - keyin tiklash rescue boot orqali bo’ladi.
`visudo` buzuq faylni saqlashdan bosh tortadi, uning butun vazifasi shu.
Tahrirlayotganda ikkinchi root shell’ini ochiq qoldiring.
:::

## Qoida sintaksisi

```
user    host = (runas_user:runas_group)  NOPASSWD:  command
alice   ALL  = (ALL:ALL)                            ALL
%sudo   ALL  = (ALL:ALL)                            ALL
%wheel  ALL  = (ALL)                     NOPASSWD:  ALL
bob     ALL  = (root)                               /usr/bin/systemctl restart nginx
carol   ALL  = (root)                    NOPASSWD:  /usr/bin/apt update, /usr/bin/apt upgrade
deploy  ALL  = (www-data)                           /usr/local/bin/deploy.sh
```

| Maydon | Ma’nosi |
|---|---|
| user / `%group` | qoida kimga tegishli |
| host | qaysi host (`ALL` - bu maydon faqat umumiy sudoers fayli uchun muhim) |
| `(runas)` | ular qaysi shaxsga aylana oladi |
| `NOPASSWD:` | parol so’ralmasin (kam ishlating) |
| command | absolyut yo’llar, vergul bilan ajratilgan; `ALL` = hamma narsa |

Alias’lar uzun fayllarni o’qishga qulay saqlaydi:

```
User_Alias  ADMINS = alice, bob
Cmnd_Alias  SERVICES = /usr/bin/systemctl start *, /usr/bin/systemctl stop *, /usr/bin/systemctl restart *
Cmnd_Alias  PKG = /usr/bin/apt, /usr/bin/apt-get
ADMINS  ALL = (ALL) SERVICES, PKG
```

Bilib qo’yishga arziydigan Defaults’lar:

```
Defaults    env_reset                       # toza muhitdan boshlash
Defaults    secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Defaults    timestamp_timeout=15            # qayta so'ragunicha necha daqiqa (0 = har safar)
Defaults    logfile="/var/log/sudo.log"
Defaults:alice  !authenticate               # alice'dan hech qachon so'ralmaydi (uning hamma qoidalari uchun NOPASSWD bilan bir xil)
Defaults    requiretty                      # terminalsiz sudo'ni rad etish (ba'zi skriptlarni to'sadi)
```

## Admin huquqlarini berish, odatiy yo’l

```bash
sudo usermod -aG sudo alice            # Debian/Ubuntu: sudo guruhi uchun /etc/sudoers da qoida bor
sudo usermod -aG wheel alice           # RHEL oilasi
groups alice                            # tasdiqlash
sudo -l -U alice
```

Guruhda allaqachon qoida bo’lsa, guruhga qo’shish to’g’ri yechim; qoidani
faqat torroq narsa kerak bo’lgandagina yozing.

## Tor ruxsatlar: sudo’ning mohiyati

```bash
sudo visudo -f /etc/sudoers.d/webops
```

```
%webops  ALL = (root) NOPASSWD: /usr/bin/systemctl restart nginx, /usr/bin/systemctl status nginx, /usr/bin/nginx -t
```

```bash
sudo chmod 440 /etc/sudoers.d/webops       # sudoers fayllari guruh/hamma uchun yoziladigan bo'lmasligi kerak
sudo visudo -c
```

Bunday ruxsat to’liq root’ga aylanib ketmasligi uchun qoidalar:

- **Faqat absolyut yo’llar**; yalang’och `systemctl` PATH’dagi hamma
  narsaga mos kelardi.
- **Argumentlarni yutadigan wildcard’lardan voz keching**:
  `/usr/bin/systemctl restart *` ba’zi shell’larda `restart -- ; bash`
  uslubidagi hiylalarga ham yo’l qo’yadi; aniq buyruqlarni afzal ko’ring.
- **Hech qachon tahrirlagich, shell yoki shell escape’i bor narsani
  bermang**: sudo ostidagi `vi`, `less`, `find`, `awk`, `python`, `tar`,
  `git` - hammasi root beradi. (Fayllarni xavfsiz tahrirlash uchun aynan
  `sudoedit` / `sudo -e file` mavjud.)
- `NOPASSWD` faqat skriptga u chindan kerak bo’lgan joyda.

## su va uning farqi

```bash
su - alice              # alice sifatida LOGIN shell: uning muhiti, uning home'i  (ALICE parolini so'raydi)
su alice                # uning shaxsi, SIZNING muhitingiz - deyarli har doim noto'g'ri
su -                    # root login shell (ROOT parolini so'raydi)
sudo su -               # sudo orqali root login shell (SIZNING parolingiz) - root'da parol yo'q bo'lganda ham ishlaydi
sudo -i                 # xuddi shu narsa, to'g'riroq yo'l - shuni afzal ko'ring
exit
```

`su` maqsadli user’ning parolini so’raydi; `sudo` esa sizningkini
so’raydi, logga yoziladi va toraytiriladi. Shuning uchun `sudo` standart
hisoblanadi va root’ning paroli ko’pincha o’rnatilmay qoldiriladi.

## Audit qilish

```bash
sudo grep sudo /var/log/auth.log | tail          # Debian
sudo journalctl _COMM=sudo --since today
sudo grep -i "NOT in the sudoers file" /var/log/auth.log      # suiiste'molga urinish
sudo -l -U alice
sudo journalctl -u sudo
```

```
Aug 19 10:22:01 web01 sudo: alice : TTY=pts/0 ; PWD=/home/alice ; USER=root ; COMMAND=/usr/bin/systemctl restart nginx
```

Har bir sudo chaqiruvi shu qatorni qoldiradi - ruxsat `ALL` bo’lganda ham
sudo umumiy root parolidan afzal ekanining sababi shu.

:::exam-tip
Ikki xil shakl uchraydi: "X user’iga to’liq sudo bering" →
`usermod -aG sudo X`; "Y guruhi faqat Z buyrug’ini parolsiz bajara
olsin" → `/etc/sudoers.d/` ichida `%Y ALL=(root) NOPASSWD: /full/path/Z`
yozilgan, rejimi 440 bo’lgan, `visudo -f` bilan yaratilgan fayl.
`sudo -l -U X` bilan va buyruqni o’sha user nomidan bajarib
(`sudo -u X sudo -n /full/path/Z`) tekshiring.
:::

## O’zingizni tekshiring

1. Nega sudoers fayllari `visudo` bilan tahrirlanishi kerak va shunday
   qilinmasa nima bo’ladi?
2. `su -`, `su` va `sudo -i` o’rtasidagi farq nima va ularning har biri
   kimning parolini so’raydi?
3. Nega `sudo vi` berish amalda to’liq root berish bilan barobar?
