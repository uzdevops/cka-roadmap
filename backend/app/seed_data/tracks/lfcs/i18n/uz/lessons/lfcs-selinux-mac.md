## SELinux’ni to’g’ri tuzatish

Oldingi dars label’larni o’qidi. Bu dars ularni o’zgartiradi - deyarli har
bir haqiqiy denial’ni hal qiladigan to’rtta vosita: **restorecon**,
**semanage fcontext**, **semanage port** va **boolean’lar**.

Ularni sinash tartibi:

```
 rad etish → ausearch/audit2why → label noto'g'rimi?  → restorecon (vaqtinchalik) yoki semanage fcontext + restorecon (doimiy)
                              → port masalasimi?    → semanage port
                              → siyosat kalitimi?      → setsebool -P
                              → yuqoridagilar emasmi → audit2allow moduli (oxirgi chora)
```

## Rejimlar va paketlar

```bash
sudo dnf install policycoreutils policycoreutils-python-utils setroubleshoot-server selinux-policy-devel
getenforce; sestatus
sudo setenforce 0 / 1                    # vaqtinchalik
sudo vi /etc/selinux/config              # SELINUX=enforcing (doimiy, reboot kerak)
```

## 1. Faylni qayta belgilash: chcon va restorecon

```bash
sudo chcon -t httpd_sys_content_t /var/www/html/index.html    # hozir o'zgartiradi
sudo chcon -R -t httpd_sys_content_t /srv/web
sudo chcon --reference=/var/www/html/other.html /var/www/html/new.html
sudo restorecon -Rv /var/www                                   # POLICY sukut bo'yicha holatiga qaytaradi
```

Farq muhim: `chcon` policy bilmaydigan label yozadi, shuning uchun qayta
belgilash (`restorecon -R /`, `/.autorelabel`, paket yangilanishi) uni
orqaga qaytaradi. `chcon` - sinov uchun; doimiy yechim - keyingi vosita.

## 2. Policy’ga yo’lni o’rgatish: semanage fcontext

```bash
sudo semanage fcontext -a -t httpd_sys_content_t "/srv/web(/.*)?"
sudo restorecon -Rv /srv/web                    # qoidani allaqachon mavjud narsalarga qo'llaydi
semanage fcontext -l | grep '/srv/web'
sudo semanage fcontext -d "/srv/web(/.*)?"      # qoidani olib tashlaydi
sudo semanage fcontext -a -e /var/www /srv/web  # -e: "/srv/web ni /var/www kabi belgila" (ekvivalentlik)
```

`"(/.*)?"` regex shakli katalogning o’zini va uning ostidagi hamma narsani
anglatadi. `semanage fcontext` qoidani yozib qo’yadi; `restorecon` uni
qo’llaydi. Har safar ikkala qadam ham - qoidaning o’zi diskda hech narsani
o’zgartirmaydi.

## 3. Nostandart portga ruxsat berish: semanage port

```bash
semanage port -l | grep http_port_t
# http_port_t   tcp   80, 81, 443, 488, 8008, 8009, 8443, 9000
sudo semanage port -a -t http_port_t -p tcp 8081       # qo'shish
sudo semanage port -m -t http_port_t -p tcp 8081       # o'zgartirish, agar port boshqa tipda bo'lsa
sudo semanage port -d -t http_port_t -p tcp 8081       # o'chirish
sudo semanage port -a -t ssh_port_t -p tcp 2222        # sshd ni 2222 ga ko'chirish uchun BU VA firewall kerak
```

Sukut bo’yicha bo’lmagan portga bog’lanishdan bosh tortadigan va denial’ida
`name_bind` nomi turgan service - aynan shu. (sshd portini o’zgartirish
uchun uchta narsa kerak: config, firewall va shu.)

## 4. Boolean’lar: policy tugmachalari

```bash
getsebool -a | head
getsebool httpd_can_network_connect
sudo setsebool httpd_can_network_connect on         # hozir
sudo setsebool -P httpd_can_network_connect on      # VA doimiy  ← gap -P da
semanage boolean -l | grep httpd_can_network
sudo semanage boolean -l -C                          # faqat sukut bo'yichadan o'zgartirilganlari
```

Imtihon ham, real hayot ham doim uriladigan boolean’lar:

| Boolean | Nimani yoqadi |
|---|---|
| `httpd_can_network_connect` | web ilovaning tashqariga, ma’lumotlar bazasi yoki API’ga ulanishi |
| `httpd_can_network_connect_db` | ... aynan ma’lumotlar bazasiga |
| `httpd_enable_homedirs` | `/home/*/public_html`’ni tarqatish |
| `httpd_use_nfs` | NFS mount’idagi web kontent |
| `ftpd_full_access`, `ftpd_anon_write` | FTP yozishlari |
| `samba_enable_home_dirs` | Samba home share’lari |
| `nfs_export_all_rw` | NFS export’lari read-write |
| `ssh_sysadm_login` | imtiyozli SSH login’lari |

`-P` o’zgarishni policy’ga yozadi; usiz keyingi reboot uni unutadi.

## 5. Oxirgi chora: lokal policy moduli

Denial qonuniy bo’lsa va uni hech bir boolean yoki label qamrab olmasa:

```bash
sudo ausearch -m avc -ts recent | audit2why              # nega rad etilgani
sudo ausearch -c 'myapp' --raw | audit2allow -M myapp    # myapp.te va myapp.pp yaratadi
cat myapp.te                                              # o'rnatishdan OLDIN O'QING
sudo semodule -i myapp.pp                                 # modulni o'rnatadi
sudo semodule -l | grep myapp
sudo semodule -r myapp                                    # olib tashlaydi
```

`audit2allow` aynan nima rad etilgan bo’lsa, o’shanga ruxsat beruvchi qoida
yozadi. Yaratilgan `.te`’ni avval o’qing: agar u keng qamrovli narsa bersa,
haqiqiy muammo - noto’g’ri label, yetishmayotgan qoida emas.

## To’liq ish oqimi, bir marta

```bash
# alomat: /srv/web ni tarqatayotgan nginx 403 qaytaradi, ruxsatlar joyida ko'rinadi
sudo setenforce 0 && curl -I localhost/          # endi ishlayaptimi? → demak SELinux
sudo setenforce 1
sudo ausearch -m avc -ts recent | audit2why
# ...denied { read } ... tcontext=...:default_t
ls -Z /srv/web/index.html                        # default_t - noto'g'ri
sudo semanage fcontext -a -t httpd_sys_content_t "/srv/web(/.*)?"
sudo restorecon -Rv /srv/web
ls -Z /srv/web/index.html                        # httpd_sys_content_t
curl -I localhost/                               # 200
```

## Butun fayl tizimini qayta belgilash

```bash
sudo touch /.autorelabel && sudo reboot          # boot paytida hammasini qayta belgilaydi (sekin)
sudo fixfiles -F relabel
sudo restorecon -Rv /home                         # maqsadli qayta belgilash odatda yetarli
```

:::warning
SELinux’ni o’chirib qo’yish - tuzatish emas, bu nazoratni olib tashlash - va
u enforcing bo’lgan mashinada keyinroq qayta yoqish to’liq qayta belgilashni
talab qiladi. Diagnostika paytida uni bo’shashtirish shart bo’lsa,
**permissive**’dan foydalaning, denial’larni to’plang, label’larni tuzating
va shu sessiyaning o’zida enforcing’ga qayting.
:::

:::exam-tip
Uchta buyruq ko’p SELinux topshirig’ini qoplaydi: `semanage fcontext -a -t <type>
"<path>(/.*)?"` **va ketidan** `restorecon -Rv <path>`; `semanage port -a
-t <type> -p tcp <port>`; hamda `setsebool -P <boolean> on`. Ballar `-P` va
`restorecon`’da yo’qoladi. `ls -Z`, `semanage port
-l | grep`, `getsebool` bilan tekshiring.
:::

## O’zingizni tekshiring

1. `chcon` bilan `semanage fcontext` + `restorecon` o’rtasidagi farq nima?
2. `setsebool -P`’dagi `-P` nima qiladi va usiz nima bo’ladi?
3. Service nostandart portga bog’lana olmayapti. Buni qaysi vosita tuzatadi
   va yana nima o’zgartirilishi kerak?
