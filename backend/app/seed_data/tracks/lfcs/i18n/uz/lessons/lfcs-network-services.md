## Ishga tushirish, to’xtatish va nima tinglayotganini tekshirish

Tarmoq servislari - oddiy systemd unit’lar; fe’llarni systemd darsi qamrab
olgan. Bu yerda o’ziga xosi - **ikkinchi** tekshiruv: shunchaki "unit
active mi" emas, balki "u tinglayaptimi, qaysi manzil va portda va unga
biror narsa yetib bora oladimi".

```bash
sudo systemctl start nginx
sudo systemctl enable --now sshd
sudo systemctl reload nginx           # ulanishlarni uzmasdan konfigni qayta o'qish
sudo systemctl status nginx
systemctl list-units --type=service --state=running | grep -Ei "ssh|nginx|named|chrony"
```

## ss: kim tinglayapti

```bash
ss -tulpn
# Netid State  Local Address:Port  Peer Address:Port  Process
# tcp   LISTEN 0.0.0.0:22          0.0.0.0:*          users:(("sshd",pid=812,fd=3))
# tcp   LISTEN 127.0.0.1:5432      0.0.0.0:*          users:(("postgres",pid=990,fd=5))
# tcp   LISTEN [::]:80             [::]:*             users:(("nginx",pid=1102,fd=6))
```

| Flag | |
|---|---|
| `-t` `-u` | TCP / UDP |
| `-l` | faqat tinglayotganlari |
| `-p` | jarayon (boshqalarnikini ko’rish uchun root kerak) |
| `-n` | raqamli portlar (`/etc/services` qidiruvisiz) |
| `-a` | hamma soketlar, o’rnatilgan ulanishlar bilan birga |
| `-s` | umumiy sanoq |
| `-4` `-6` | manzil oilasi |

```bash
ss -tulpn | grep :80
ss -tan state established
ss -tp dst 10.0.0.5              # bir hostga ulanishlar
ss -tuln sport = :22
lsof -i :8080                    # so'rashning boshqa yo'li
sudo fuser -n tcp 8080           # va uchinchisi
sudo netstat -tulpn              # eski buyruq, o'sha g'oya (net-tools)
```

Muhim tafsilot - **tinglash manzili**: `0.0.0.0`/`[::]` har bir interfeys
degani; `127.0.0.1` esa faqat loopback, ya’ni firewall qanchalik ochiq
bo’lmasin, masofadagi mijoz ulana olmaydi. "Servis ishlab turibdi, lekin
men unga yeta olmayapman" - juda ko’p hollarda aynan shu qator.

## Yetib borishni sinash

```bash
curl -I http://localhost                        # avval lokal
curl -I http://192.168.1.50                     # keyin o'z manzilidan
curl -sS -o /dev/null -w '%{http_code}\n' http://host/health
nc -zv 192.168.1.50 80                          # port shu yerdan ochiqmi?
nc -zv -u 192.168.1.50 53
telnet host 25                                  # qatorli protokollar uchun (SMTP, HTTP)
ping -c2 host                                   # TCP ishlayotganda ham ICMP to'silgan bo'lishi mumkin
traceroute host; mtr host
dig @192.168.1.53 example.com                   # aynan bitta DNS serverni sinash
openssl s_client -connect host:443 </dev/null   # TLS handshake va sertifikat
```

Nosozlikni ajratadigan tartib: **host ustida** (`curl localhost`) →
**host’ning o’z manzilidan** (`curl <its ip>`) → **boshqa mashinadan**
(`nc -zv`). Birinchisi ishlab, ikkinchisi ishlamasa, servis loopback’ga
bog’langan; ikkinchisi ishlab, uchinchisi ishlamasa - bu firewall yoki
marshrutlash.

## Keng tarqalgan tarmoq servislari

| Servis | Unit | Port | Konfiguratsiya |
|---|---|---|---|
| SSH | `sshd` / `ssh` | 22 | `/etc/ssh/sshd_config` |
| HTTP(S) | `nginx`, `httpd`, `apache2` | 80, 443 | `/etc/nginx/`, `/etc/apache2/` |
| DNS | `named`, `unbound`, `systemd-resolved` | 53 | `/etc/named.conf` |
| DHCP | `isc-dhcp-server`, `dnsmasq` | 67/68 | `/etc/dhcp/dhcpd.conf` |
| NTP | `chronyd`, `systemd-timesyncd` | 123 | `/etc/chrony/chrony.conf` |
| NFS | `nfs-server` | 2049 | `/etc/exports` |
| Mail | `postfix` | 25, 587 | `/etc/postfix/main.cf` |
| Ma’lumotlar bazasi | `postgresql`, `mariadb` | 5432, 3306 | paketga qarab |

## Reload’dan oldin konfiguratsiya testi

Ko’pchilik serverlar o’z konfiguratsiyasini tekshira oladi; buni
reload’dan **oldin** qiling, chunki buzuq fayl bilan reload servisni
to’xtatib qo’yishi mumkin:

```bash
sudo nginx -t
sudo apache2ctl configtest
sudo sshd -t                         # yoki: amaldagi konfigni chiqarish uchun sshd -T
sudo named-checkconf
sudo chronyd -Q
sudo postfix check
sudo exportfs -v
```

Keyin, servis qo’llab-quvvatlaydigan joyda, `restart` emas, `systemctl
reload` (yumshoq) ishlating.

## Ishga tushmasa

```bash
systemctl status nginx
journalctl -u nginx -n 50 --no-pager
journalctl -xeu nginx
sudo ss -tulpn | grep :80              # portda allaqachon boshqa narsa bormi?
sudo lsof -i :80
```

| Xabar | Sabab |
|---|---|
| `Address already in use` | portni boshqa jarayon egallagan - `ss -tulpn \| grep :PORT` |
| past portga bog’lanishda `Permission denied` | root emas va `CAP_NET_BIND_SERVICE` yo’q; yoki SELinux port label’i (7-hafta) |
| `Cannot assign requested address` | sozlangan manzil bu hostda mavjud emas |
| ishga tushadi, masofadan yetib bo’lmaydi | 127.0.0.1 da tinglayapti yoki firewall (keyingi dars) |
| `Failed to start ... configuration test failed` | yuqoridagi konfiguratsiya testi buni tutgan bo’lardi |

:::exam-tip
Ehtimoliy topshiriq - "X servisini hozir va boot’da ishga tushadigan, P
portida tinglaydigan qiling": `systemctl enable --now X` va
konfiguratsiyani tahrirlash; tekshirish uchun esa `ss
-tulpn | grep P` va `curl`/`nc`. Har doim faqat portni emas, **tinglash
manzilini** ham tekshiring va yodda tuting: firewall - alohida maqsad,
lekin o’sha topshiriq unga jimgina tayanishi mumkin.
:::

## O’zingizni tekshiring

1. Qaysi buyruq tinglayotgan TCP va UDP portlarni ularga tegishli jarayon
   bilan ko’rsatadi va buni qaysi flaglar qiladi?
2. Servis active, lekin boshqa hostdan unga yetib bo’lmayapti. Uchta
   mumkin bo’lgan sababni va ularni qanday ajratishni ayting.
3. Nega `systemctl reload nginx`’dan oldin `nginx -t` bajariladi?
