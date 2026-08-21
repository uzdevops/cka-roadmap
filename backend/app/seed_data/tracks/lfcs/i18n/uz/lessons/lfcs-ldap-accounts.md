## Ko’plab host’lar bo’ylab bitta shaxs

Lokal account’lar kengaymaydi: ellikta server - har bir user’ning ellikta
nusxasi, ellikta parol almashtirish, kimnidir olib tashlashni unutish
uchun ellikta joy demakdir. **Directory** (LDAP yoki LDAP tilida
gapiradigan Active Directory) user’lar va guruhlarni markazlashgan holda
saqlaydi; har bir host `/etc/passwd`’ni o’qish o’rniga directory’dan
so’raydi.

```
 login → PAM (autentifikatsiya) ─┐
                                 ├→ SSSD ──cache──▶ LDAP / AD server
 id, ls -l → NSS (kimlik) ───────┘
```

Ikkita quyi tizim, bitta daemon:

- **NSS** (Name Service Switch) "uid 1234 kim, alice qaysi guruhlarda"
  degan savolga javob beradi - `/etc/nsswitch.conf`’da sozlanadi.
- **PAM** "bu parol to’g’rimi, bu user kira oladimi" degan savolga javob
  beradi - `/etc/pam.d/*`’da sozlanadi.
- **SSSD** ikkalasini ham directory bilan ishlab bajaradi va javoblarni
  **keshlaydi**, shuning uchun tarmoq ishlamaganda ham loginlar
  ishlayveradi.

## O’rnatish

```bash
sudo apt install sssd sssd-tools libnss-sss libpam-sss ldap-utils oddjob-mkhomedir
sudo dnf install sssd sssd-ldap oddjob-mkhomedir openldap-clients
```

## SSSD’ni sozlash

```bash
sudo vi /etc/sssd/sssd.conf
```

```ini
[sssd]
services = nss, pam
domains = example.com

[domain/example.com]
id_provider = ldap
auth_provider = ldap
ldap_uri = ldaps://ldap.example.com:636
ldap_search_base = dc=example,dc=com
ldap_default_bind_dn = cn=sssd,ou=services,dc=example,dc=com
ldap_default_authtok = <bind password>
ldap_tls_reqcert = demand
ldap_tls_cacert = /etc/ssl/certs/company-ca.crt
cache_credentials = true
enumerate = false
override_homedir = /home/%u
default_shell = /bin/bash
ldap_id_use_start_tls = false
access_provider = simple
simple_allow_groups = linux-admins, developers
```

```bash
sudo chmod 600 /etc/sssd/sssd.conf         # aks holda SSSD ishga tushishni RAD ETADI - unda bind paroli bor
sudo chown root:root /etc/sssd/sssd.conf
sudo systemctl enable --now sssd
sudo systemctl status sssd
```

`cache_credentials = true` - noutbukka oflayn kirish imkonini beradigan
narsa; `simple_allow_groups` bilan birga `access_provider = simple` esa
"bu host’ga faqat shu directory guruhlari kira oladi" deyishning eng
oddiy usuli.

## NSS va PAM’ni ulash

```bash
sudo pam-auth-update                       # Debian: "SSS authentication" va "create home directory" ni belgilang
sudo authselect select sssd with-mkhomedir --force     # RHEL oilasi
grep -E "^(passwd|group|shadow)" /etc/nsswitch.conf
# passwd:  files sss
# group:   files sss
# shadow:  files sss
```

`files sss` "avval `/etc/passwd` ichiga qara, so’ng SSSD’dan so’ra"
degani - lokal account’lar ishlayveradi va ziddiyatda ustun chiqadi.

Directory user’lari uchun home directory’lar kimdir tizimga kirmaguncha
mavjud bo’lmaydi; `pam_mkhomedir` (`oddjob-mkhomedir` yoki
`pam-auth-update` orqali) ularni birinchi login’da `/etc/skel`’dan
yaratadi.

```
# /etc/pam.d/common-session
session optional pam_mkhomedir.so skel=/etc/skel umask=0077
```

## Tekshirish

```bash
getent passwd alice                # NSS orqali hal bo'ladi: bu ishlasa, shaxs bilan hammasi joyida
getent group developers
id alice
su - alice                         # PAM'ni sinaydi: getent ishlab, bu ishlamasa - muammo autentifikatsiyada
sudo sssctl domain-status example.com
sudo sssctl user-checks alice -a auth
ldapsearch -x -H ldaps://ldap.example.com -b "dc=example,dc=com" "(uid=alice)"     # to'g'ridan-to'g'ri serverdan so'rash
sudo systemctl restart sssd
sudo rm -rf /var/lib/sss/db/* && sudo systemctl restart sssd    # ma'lumot eskirgan ko'rinsa keshni tozalash
sudo journalctl -u sssd -f
```

Tashxis tartibi doim bir xil: `getent passwd` (NSS) → `su -` (PAM) →
`ldapsearch` (server va bind ma’lumotlari) → SSSD loglari.

## Active Directory’ga qo’shilish

```bash
sudo apt install realmd sssd adcli krb5-user samba-common-bin
realm discover example.com
sudo realm join --user=Administrator example.com
realm list
sudo realm permit --groups 'EXAMPLE\linux-admins'
id 'EXAMPLE\alice'; id alice@example.com
sudo realm leave example.com
```

`realm join` SSSD va Kerberos konfiguratsiyasini siz uchun yozadi - AD
uchun odatiy yo’l shu, unda `sssd.conf`’ni qo’lda yozish shart emas.

## Keng tarqalgan nosozliklar

| Belgi | Sababi |
|---|---|
| `getent passwd alice` bo’sh | NSS `sss`’ga yo’naltirilmagan, SSSD ishlamayapti, `search_base` noto’g’ri |
| shaxs aniqlanadi, login ishlamaydi | PAM sozlanmagan (`pam-auth-update`/`authselect`) yoki `access_provider` qoidalari |
| `Could not start TLS ... peer certificate` | CA `ldap_tls_cacert` ichida yo’q yoki hostname mos kelmayapti |
| SSSD ishga tushishni rad etadi | `sssd.conf` rejimi 0600 emas yoki sintaksis xatosi - `journalctl -u sssd` |
| login’da home directory yo’q | `pam_mkhomedir` yoqilmagan |
| ishlaydi, parol almashgandan keyin to’xtaydi | eskirgan kesh - SSSD’ni qayta ishga tushiring yoki `/var/lib/sss/db`’ni tozalang |
| sudo directory user’lariga amal qilmaydi | nsswitch’ga `sudoers: files sss` qo’shing yoki guruh uchun lokal `/etc/sudoers.d` qoidasi |

:::warning
`ldap_default_authtok` - bu konfiguratsiya faylidagi parol, shuning uchun
rejim 0600 va minimal subtree ustidan **faqat o’qish** huquqiga ega
service account kerak. Production’ni hech qachon TLS’siz `ldap://`’ga
yo’naltirmang: bind parollari va user ma’lumotlari tarmoq bo’ylab ochiq
holda o’tadi. `ldap_tls_reqcert = never` esa LDAPS’ni ma’noli qiladigan
yagona tekshiruvni o’chirib qo’yadi.
:::

:::exam-tip
To’liq LDAP sozlamasi uzoq topshiriq, shuning uchun imtihon varianti
odatda torroq bo’ladi: paketlarni o’rnating, berilgan `sssd.conf`’ni
yozing, uning ruxsatlarini 0600 qiling, service’ni yoqing, home directory
yaratishni yoqing va buni `getent passwd <directory-user>` hamda `id`
bilan isbotlang. Odamlar unutadigan ikkita tafsilot -
`/etc/sssd/sssd.conf` ruxsatlari va nsswitch’dagi `files sss` qatori.
:::

## O’zingizni tekshiring

1. NSS va PAM’ning har biri qaysi savolga javob beradi va har birini
   qaysi fayl sozlaydi?
2. Qaysi buyruq shaxs aniqlanishi ishlayotganini isbotlaydi va qaysi biri
   autentifikatsiya ishlayotganini?
3. Nega `/etc/sssd/sssd.conf` rejimi 0600 bo’lishi kerak va aks holda
   nima bo’ladi?
