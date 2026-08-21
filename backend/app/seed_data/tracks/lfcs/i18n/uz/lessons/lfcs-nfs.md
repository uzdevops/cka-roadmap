## Directory’ni tarmoq orqali ulashish

NFS serverdagi directory’ni export qiladi; klientlar uni xuddi lokal
narsadek mount qiladi. Unix ruxsatlari fayllar bilan birga ko’chadi -
aynan shu NFS’ni Linux hostlar orasida tabiiy tanlovga aylantiradi
(CIFS/Samba - Windows bilan mos keladigan muqobil).

## Server

```bash
sudo apt install nfs-kernel-server        # Debian/Ubuntu
sudo dnf install nfs-utils                # RHEL
sudo systemctl enable --now nfs-server    # (Debian'da nfs-kernel-server)
```

```bash
sudo mkdir -p /srv/nfs/shared
sudo chown nobody:nogroup /srv/nfs/shared     # yoki klientlarning UID'lariga mos keladigan haqiqiy egasi
sudo chmod 2775 /srv/nfs/shared
sudo vi /etc/exports
```

```
/srv/nfs/shared   192.168.1.0/24(rw,sync,no_subtree_check)
/srv/nfs/ro       192.168.1.0/24(ro,sync,no_subtree_check)
/srv/nfs/admin    192.168.1.10(rw,sync,no_root_squash,no_subtree_check)
/srv/nfs/home     *.example.com(rw,sync,root_squash,no_subtree_check)
```

Sintaksis: `directory client(options)` - klient bilan ochiluvchi qavs
orasida **bo’sh joy yo’q**. Bo’sh joy "sukut bo’yicha option’lar bilan
hammaga export qil, va yana o’sha klientga ham" degani bo’ladi - bu
klassik tasodifiy world-export.

| Option | Ma’nosi |
|---|---|
| `rw` / `ro` | yozish mumkin / faqat o’qish |
| `sync` | ma’lumot diskka tushgandan keyingina javob beradi (xavfsiz; sukut bo’yicha) |
| `async` | erta javob beradi - tezroq, crash paytida ma’lumot yo’qotish xavfi bor |
| `root_squash` | **sukut bo’yicha**: masofadagi root `nobody`’ga o’tkaziladi |
| `no_root_squash` | masofadagi root bu yerda **root bo’ladi** - xavfli, faqat aniq admin hostlar uchun ishlating |
| `all_squash` | har bir masofadagi foydalanuvchi `nobody` bo’ladi - ochiq, faqat o’qish uchun share’larga yaxshi |
| `anonuid=`/`anongid=` | squash qilingan foydalanuvchilar qaysi lokal identifikatsiyani oladi |
| `no_subtree_check` | tavsiya etiladi: fayllar nomi o’zgarganda kamroq muammo bo’ladi |
| `secure` | manba porti 1024’dan past bo’lishini talab qiladi (sukut bo’yicha) |

```bash
sudo exportfs -arv          # /etc/exports ni qayta o'qib qo'llaydi
sudo exportfs -v            # hozir nima export qilingan
sudo exportfs -u 192.168.1.0/24:/srv/nfs/shared     # bittasini unexport qilish
showmount -e localhost      # klientlar nimani ko'rardi
```

Firewall: NFSv4 uchun faqat **TCP 2049** kerak.

```bash
sudo ufw allow from 192.168.1.0/24 to any port nfs
sudo firewall-cmd --permanent --add-service=nfs && sudo firewall-cmd --reload
# NFSv3 uchun rpc-bind va mountd ham kerak - ularning portlarini qotiring yoki shunchaki v4 ishlating
```

## Klient

```bash
sudo apt install nfs-common          # yoki: dnf install nfs-utils
showmount -e 192.168.1.10             # server nimani taklif qiladi?
sudo mkdir -p /mnt/shared
sudo mount -t nfs 192.168.1.10:/srv/nfs/shared /mnt/shared
df -h /mnt/shared; findmnt /mnt/shared
touch /mnt/shared/test && ls -l /mnt/shared
sudo umount /mnt/shared
```

Doimiy qilib:

```
192.168.1.10:/srv/nfs/shared  /mnt/shared  nfs  defaults,_netdev,rw  0  0
# yoki, mavjud bo'lmasligi mumkin bo'lgan share uchun yaxshirog'i:
192.168.1.10:/srv/nfs/shared  /mnt/shared  nfs  rw,soft,timeo=30,retrans=3,_netdev,nofail  0  0
```

```bash
sudo mount -a
findmnt -t nfs4
```

`_netdev` tarmoqni kutadi; usiz boot manzil paydo bo’lishidan oldin mount
qilishga urinishi mumkin. `nofail` esa yo’q server boot’ni to’sib
qo’yishiga yo’l qo’ymaydi.

| Klient option’i | Ta’siri |
|---|---|
| `hard` (sukut bo’yicha) | server yo’qolsa **abadiy** qayta urinadi - jarayonlar `D` holatida osilib qoladi, lekin ma’lumot yo’qolmaydi |
| `soft` | `timeo`×`retrans`’dan keyin voz kechadi - osilish o’rniga I/O xatolari; yozishda ma’lumot yo’qotish xavfi bor |
| `intr` | (eskirgan) signallar uzishiga ruxsat beradi; zamonaviy kernel’lar buni o’zi hal qiladi |
| `timeo=`, `retrans=` | har bir urinishga soniyaning o’ndan bir ulushlari, va nechta urinish bo’lishi |
| `rsize=`/`wsize=` | uzatish o’lchamlari; tuning qilmasangiz, kelishuvga qoldiring |
| `noatime`, `nodev`, `nosuid` | har qanday fayl tizimidagi kabi - NFS mount’ida `nosuid` oqilona |
| `vers=4.2` | protokol versiyasini qotirish |

Qoida: **yozadigan har qanday narsangiz uchun `hard`** (ma’lumot
yaxlitligi), `soft` esa faqat osilish xatodan yomonroq bo’lgan faqat
o’qishli yoki ixtiyoriy mount’lar uchun.

## Identifikatsiya: kimning UID’i?

NFS **raqamli UID’larni** yuboradi. Agar `alice` klientda 1001, serverda
1005 bo’lsa, fayllar noto’g’ri foydalanuvchiga tegishlidek ko’rinadi.
Yechimlar: UID’larni bir xil saqlash (LDAP, 8-hafta), yoki `anonuid`
bilan `all_squash` ishlatish, yoki mos domenlar sozlangan NFSv4’dagi
`idmapd`.

```bash
id alice           # ikkala mashinada ham - ular mos kelishi kerak
ls -ln /mnt/shared # raqamli egalar, server aslida nimani saqlayotganini ko'rish uchun
```

## Diagnostika

```bash
# server
sudo systemctl status nfs-server
sudo exportfs -v
sudo ss -tulpn | grep 2049
sudo journalctl -u nfs-server -n 30

# klient
showmount -e <server>            # bu ishlamasa, muammo NFS option'larida emas, tarmoq/firewall'da
sudo mount -v -t nfs server:/path /mnt/x
nfsstat -c; nfsstat -m
findmnt -t nfs4
```

| Belgi | Sababi |
|---|---|
| `access denied by server` | klient `/etc/exports`’da yo’q, yoki `exportfs -ra` ishga tushirilmagan |
| yozishda `Permission denied` | `ro` bilan export qilingan, yoki Unix ruxsatlari, yoki `root_squash` va siz root’siz |
| `No route to host` / timeout | firewall (2049), yoki server o’chgan |
| `mount: wrong fs type` | klientda `nfs-common`/`nfs-utils` o’rnatilmagan |
| egasi `nobody` bo’lgan fayllar | UID mos kelmasligi yoki NFSv4 idmap domeni mos kelmasligi |
| mount’da buyruqlar abadiy osilib qoladi | `hard` mount va server yo’q - `umount -l`, yoki mos joyda `soft` ishlating |
| boot osilib qoladi | fstab’da `_netdev`/`nofail` yo’q |

:::warning
`no_root_squash` masofadagi root’ga share ichiga root sifatida SUID
binary’lar yozish imkonini beradi - bu amalda klientda root bo’la
oladigan har kimga serverda root berish demak. Uni faqat nomi
ko’rsatilgan admin host uchun ishlating, hech qachon subnet yoki `*`
bilan emas.
:::

:::exam-tip
Ikkala yarmi ham so’ralishi mumkin: berilgan option’lar bilan directory’ni
export qilish (`/etc/exports` + `exportfs -arv` + firewall, `showmount -e
localhost` bilan tekshiriladi) va uni klientda doimiy qilib mount qilish
(fstab’da `_netdev`, `mount -a`, `df -h` bilan tekshiriladi).
`/etc/exports`’dagi bo’sh joy yo’q qoidasiga e’tibor bering va har bir
tahrirdan keyin `exportfs -arv`’ni unutmang.
:::

## O’zingizni tekshiring

1. `root_squash` nima qiladi va nega `no_root_squash` xavfli?
2. `hard` va `soft` NFS mount orasidagi farq nima, va yozish uchun
   qaysi birini tanlaysiz?
3. Qaysi ikkita fstab option’i NFS mount’ining boot’ni buzishiga yo’l
   qo’ymaydi?
