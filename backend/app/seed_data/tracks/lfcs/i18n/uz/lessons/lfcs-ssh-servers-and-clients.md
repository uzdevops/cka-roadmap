## Parol o’rniga kalitlar

```bash
ssh-keygen -t ed25519 -C "ahmad@laptop"            # zamonaviy standart; ed25519 qo'llanmasa -t rsa -b 4096
# ~/.ssh/id_ed25519       yopiq  - mashinadan HECH QACHON chiqmaydi, chmod 600
# ~/.ssh/id_ed25519.pub   ochiq  - buni istalgan joyga nusxalang
ssh-copy-id ahmad@server                            # .pub faylni serverning authorized_keys fayliga qo'shadi
ssh-copy-id -i ~/.ssh/deploy.pub deploy@server
ssh ahmad@server                                    # parolsiz
```

`ssh-copy-id` mavjud bo’lmaganda, qo’lda:

```bash
cat ~/.ssh/id_ed25519.pub | ssh ahmad@server 'mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
```

Ruxsatlarni sshd majburiy tekshiradi va kalitlar "ishlamasligi"ning eng
keng tarqalgan sababi shu:

| Yo’l | Rejim |
|---|---|
| `~` | guruh yoki hamma uchun **yozib bo’ladigan** emas |
| `~/.ssh` | `700` |
| `~/.ssh/authorized_keys` | `600` |
| yopiq kalitlar | `600` |

```bash
chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys ~/.ssh/id_*
sudo journalctl -u ssh | grep -i "authentication refused\|bad ownership"
```

## Agent va passphrase’lar

```bash
ssh-keygen -t ed25519                     # unga passphrase bering
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519                  # passphrase'ni sessiyada bir marta yozasiz
ssh-add -l                                 # yuklangan kalitlar
ssh-add -D                                 # ularni unutish
ssh -A user@bastion                        # agent forwarding - qulay, va ishonchsiz host'larda xavf
```

Passphrase va agent birgalikda sizga ham kalit xavfsizligini, **ham**
qulaylikni beradi; passphrase’siz kalit - bu faylda yotgan parol (cheklangan,
maxsus ajratilgan kalit bilan avtomatlashtirish uchun maqbul).

## sshd’ni mustahkamlash

```bash
sudo vi /etc/ssh/sshd_config          # yoki /etc/ssh/sshd_config.d/ ichidagi fayl
```

```
Port 22                              # yoki standart bo'lmagan port (yashirinish, xavfsizlik emas)
PermitRootLogin no
PasswordAuthentication no            # faqat kalitlar - eng katta yutuq
PubkeyAuthentication yes
PermitEmptyPasswords no
MaxAuthTries 3
LoginGraceTime 30
AllowUsers ahmad deploy              # yoki: AllowGroups ssh-users
X11Forwarding no
ClientAliveInterval 300
ClientAliveCountMax 2
Banner /etc/issue.net
```

```bash
sudo sshd -t                          # SINTAKSISNI TEKSHIRISH - har bir reload'dan oldin shuni qiling
sudo sshd -T | grep -Ei "permitroot|password|port|allowusers"   # AMALDAGI config
sudo systemctl reload ssh             # RHEL'da 'sshd'
```

:::warning
Sinalmagan o’zgarishdan keyin, ssh sizning yagona kirish yo’lingiz ekan,
hech qachon `systemctl restart ssh` qilmang. Buning o’rniga: `sshd -t`,
keyin `reload`, keyin **yangi terminalda ikkinchi sessiya oching** va
birinchisini yopishdan oldin uning ishlashiga ishonch hosil qiling. Yangi
sessiya ochilmasa, o’zgarishni orqaga qaytarish uchun eski sessiyangiz
qoladi. Aks holda `Match` bloki yoki `AllowUsers`’dagi bitta xato sizni
butunlay tashqarida qoldiradi.
:::

Guruh yoki manzil bo’yicha istisnolar:

```
Match Group sftponly
    ChrootDirectory /srv/sftp/%u
    ForceCommand internal-sftp
    AllowTcpForwarding no

Match Address 192.168.1.0/24
    PasswordAuthentication yes
```

`Match` bloklari faylning **oxirida** turishi kerak - `Match`’dan keyingi
hamma narsa o’shanga tegishli bo’ladi.

## Client tomoni

```bash
vi ~/.ssh/config
```

```
Host web01
    HostName 192.168.1.50
    User ahmad
    Port 2222
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60

Host *.internal
    User admin
    ProxyJump bastion.example.com          # avtomatik ravishda bastion orqali sakrash

Host bastion.example.com
    User ahmad
    IdentityFile ~/.ssh/bastion_key
```

```bash
chmod 600 ~/.ssh/config
ssh web01                                  # yuqoridagilarning hammasi, bitta so'z bilan
```

```bash
ssh -p 2222 -i ~/.ssh/key user@host
ssh -J bastion user@internal-host          # buyruq satrida jump host
ssh user@host 'uptime; df -h'              # ishga tushirib, natijani qaytaradi
ssh -t user@host 'sudo systemctl status nginx'    # masofadagi buyruqqa terminal kerak bo'lganda -t
ssh -v user@host                           # batafsil: autentifikatsiya suhbati - tiqilib qolsangiz -vvv
scp file user@host:/tmp/; rsync -av dir/ user@host:/dst/
sftp user@host
```

## Host key’lar

Birinchi ulanishda sizdan serverning fingerprint’iga ishonish so’raladi; u
`~/.ssh/known_hosts` faylida saqlanadi. Kalitning o’zgarishi yo server
qayta qurilganini, yo o’rtada odam borligini bildiradi:

```bash
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub      # serverning fingerprint'i, konsoldan tekshiriladi
ssh-keygen -R web01                                    # qayta qurishdan keyin eski host key'ni unutish
ssh-keyscan -t ed25519 web01 >> ~/.ssh/known_hosts
```

## Tunnellar

```bash
ssh -L 8080:localhost:80 user@host        # LOKAL: mening :8080 → host'ning :80  (masofadagi service'ga yetish)
ssh -L 5433:db.internal:5432 user@bastion # bastion orqali uchinchi host'ga
ssh -R 9000:localhost:3000 user@host      # MASOFAVIY: host'ning :9000 → mening :3000  (lokal service'ni ochish)
ssh -D 1080 user@host                     # host orqali SOCKS proxy
ssh -fN -L 8080:localhost:80 user@host    # fonda, shell'siz
```

`-L` masofadagi narsani sizga olib keladi; `-R` lokal narsani tashqariga
chiqaradi. (Serverdagi `GatewayPorts` va `AllowTcpForwarding` bularga
ruxsat berilishini boshqaradi.)

## Diagnostika

```bash
ssh -vvv user@host 2>&1 | grep -iE "offering|authentications|denied|permission"
sudo journalctl -u ssh -f
sudo tail -f /var/log/auth.log
sudo sshd -T | grep -i pubkeyauth
sudo ss -tulpn | grep :22
sudo lastb | head                          # muvaffaqiyatsiz urinishlar
```

| Alomat | Sababi |
|---|---|
| `Permission denied (publickey)` | kalit `authorized_keys`’da yo’q, noto’g’ri kalit taklif qilinyapti, yoki `~`, `~/.ssh`, `authorized_keys` ruxsatlari noto’g’ri |
| `Connection refused` | sshd ishlamayapti, yoki port noto’g’ri |
| `Connection timed out` | firewall yoki routing - sshd emas |
| `Host key verification failed` | host key o’zgargan - uni tekshiring, keyin `ssh-keygen -R` |
| kalit bo’lsa ham parol so’rayapti | `PasswordAuthentication yes` va kalit qabul qilinmayapti - sababini `ssh -v` ko’rsatadi |
| lokal ishlaydi, masofadan yo’q | `ListenAddress`, firewall, yoki `AllowUsers` |

:::exam-tip
Juda ehtimolli: "X foydalanuvchi kalit bilan kira olsin va parol
autentifikatsiyasini o’chiring", yoki "SSH portini N’ga o’zgartiring".
Ketma-ketlik: sshd_config’ni (yoki drop-in faylni) tahrirlash, `sshd -t`,
`systemctl reload ssh`, standart bo’lmagan portda esa yana firewall
(`ufw allow N/tcp`) va RHEL’da SELinux
(`semanage port -a -t ssh_port_t -p tcp N`). Birinchi sessiyani yopishdan
oldin ikkinchi sessiyadan tekshiring.
:::

## O’zingizni tekshiring

1. `~/.ssh` va `authorized_keys` qanday ruxsatlarga ega bo’lishi kerak va
   aks holda nima bo’ladi?
2. `ssh -L` bilan `ssh -R` orasidagi farq nima?
3. Firewall’li RHEL host’ida SSH portini o’zgartiryapsiz. Qaysi uch
   narsani o’zgartirishingiz kerak?
