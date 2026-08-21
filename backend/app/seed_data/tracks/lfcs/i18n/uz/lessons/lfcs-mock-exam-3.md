## LFCS mock imtihon 3

Ikki soat. O’n beshta topshiriq, jami 100. Networkingga og’ir bo’lgani:
NAT, reverse proxy, bridge, shuningdek konteynerlar, SELinux/AppArmor va
kvotalar. 4- va 8-topshiriq uchun ikkita VM qo’l keladi; qolganiga ikkita
NIC’li bitta VM yetarli. Avval snapshot.

---

**1.** (8) Bu hostni `192.168.150.0/24`’dan kelgan trafikni asosiy
interfeys orqali masquerade qiladigan qilib sozlang, IP forwarding doimiy
ravishda yoqilgan bo’lsin. NAT qoidalarini `/root/nat.txt`’da ko’rsating.

**2.** (8) Bu hostdagi kiruvchi TCP 8080-portni xuddi shu hostdagi
80-portga doimiy ravishda yo’naltiring. `curl -I http://localhost:8080`
bilan tekshiring.

**3.** (8) nginx’ni o’rnating va uni reverse proxy sifatida sozlang:
80-portdagi `/app/`’ga kelgan so’rovlar `http://127.0.0.1:8000`’ga borsin.
Buni isbotlash uchun 8000-portda oddiy listener ishga tushiring
(`python3 -m http.server 8000`). `curl -I` chiqishini `/root/proxy.txt`’ga
saqlang.

**4.** (7) Ikkinchi interfeysni o’z ichiga olgan, `192.168.160.1/24`
manzilini ushlab turadigan `br0` bridge’ini doimiy qilib yarating.
`/root/bridge.txt`’da `ip -br a` va `bridge link` chiqishini ko’rsating.

**5.** (7) `nginx:alpine` image’idan `web` nomli konteyner ishga tushiring:
host’ning 8081-porti konteynerning 80-portiga chiqarilgan, (o’zingiz
yaratgan `index.html` bilan) `/srv/site` `/usr/share/nginx/html`’ga faqat
o’qish uchun mount qilingan, avtomatik qayta ishga tushadigan. `curl`
bilan tekshiring.

**6.** (6) `ops` nomli user yarating, uning jarayonlari doimiy ravishda
100 ta jarayon va 4096 ta ochiq fayl bilan cheklangan bo’lsin. Yangi
login’dan olingan amaldagi limitlarni `/root/limits.txt`’da ko’rsating.

**7.** (7) `/mnt/quota`’ga mount qilingan, `/dev/sdb1`’da o’zingiz
yaratadigan fayl tizimida user kvotalarini yoqing va `ops` useri uchun
100 MB soft / 120 MB hard blok limitini o’rnating. `repquota` chiqishini
`/root/quota.txt`’da ko’rsating.

**8.** (7) Boshqa hostdagi NFS export’ini (yoki 2-mock’da bittasini export
qilgan bo’lsangiz, `localhost` dagini) `/mnt/remote`’ga doimiy qilib mount
qiling, shunday qilibki, server yo’q bo’lsa ham boot to’xtab qolmasin.

**9.** (7) `chrony`’ni `pool.ntp.org`’dan foydalanadigan va
`192.168.150.0/24`’ga vaqt beradigan qilib sozlang. `chronyc sources`
chiqishini `/root/chrony.txt`’da ko’rsating.

**10.** (6) `server.local` uchun 365 kun amal qiladigan o’z-o’zini
imzolagan sertifikatni `/etc/ssl/certs/server.crt`’da, kalitini esa
`/etc/ssl/private/server.key`’da (rejim 600) yarating. Subject, issuer va
sanalarni `/root/cert.txt`’da ko’rsating.

**11.** (6) `signed-by` keyring usulidan foydalanib, o’zingiz tanlagan
istalgan uchinchi tomon repozitoriysi uchun repozitoriy kalitini va
manbasini qo’shing, keyin undagi biror paket uchun `apt-cache policy`
chiqishini `/root/repo.txt`’da ko’rsating.

**12.** (6) `/var` ostidagi symbolic link bo’lmagan har bir
world-writable faylni toping va ro’yxatni `/root/worldwritable.txt`’ga
yozing.

**13.** (6) Har kuni 02:30 da `report.service` oneshot service’ini ishga
tushiradigan systemd **timer**’ini `Persistent=true` bilan sozlang. Unga
filtrlangan `systemctl list-timers` chiqishini `/root/timer.txt`’da
ko’rsating.

**14.** (5) `/etc/myapp` ostidagi barcha `.conf` fayllarda (bir nechtasini
yarating) `oldhost.example.com`’ning har bir uchrashini
`newhost.example.com`’ga joyida almashtiring, har birining `.bak`
nusxasini saqlab qolgan holda.

**15.** (6) `/root/netcheck.txt`’da ko’rsating: sukut bo’yicha marshrut,
ishlatilayotgan DNS serverlar va jarayoni bilan birga tinglayotgan har bir
TCP port.

---

:::exam-tip
1-, 2- va 4-topshiriq noto’g’ri bajarilsa o’z ulanishingizni uzadi - SSH
orqali emas, VM konsolidan (`virsh console`) ishlang. Haqiqiy imtihon
aynan shu cheklovni olib tashlaydi (uning terminaliga sizning firewall
qoidalaringiz ta’sir qilmaydi), lekin "bu o’zgarish menga kiradigan
yo’lni o’zgartiradimi?" deb o’ylash odati saqlashga arziydi.
:::

## O’zingizni tekshiring

1. Qaysi topshiriqning o’zgarishi sizni tashqarida qoldirish ehtimoli eng
   yuqori edi va bundan qanday himoyalandingiz?
2. 2-topshiriqda filtr qoidalari qaysi portga ruxsat berishi kerak edi va
   nega?
3. Bu o’n beshta topshiriqdan qaysilarini `man`’ga murojaat qilmasdan
   tugatdingiz?
