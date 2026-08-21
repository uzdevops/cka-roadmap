## Paketlar yetarli bo’lmaganda

Ba’zan paket umuman bo’lmaydi: repository’dagidan yangiroq versiya,
paketchi o’chirib qo’ygan opsiya bilan qurilgan variant yoki faqat source
tarqatadigan dastur. Klassik ketma-ketlik - uchta buyruq, va uni keyin
o’chira oladigan qilmoqchi bo’lsangiz, to’rtinchisi: `checkinstall` yoki
paket.

```bash
./configure && make && sudo make install
```

## Avval build bog’liqliklari

```bash
sudo apt install build-essential          # gcc, g++, make, libc-dev  (Debian/Ubuntu)
sudo dnf groupinstall "Development Tools" # (RHEL oilasi)
sudo apt install pkg-config autoconf automake libtool cmake
sudo apt build-dep nginx                  # paketlangan dasturning aniq build bog'liqliklari (deb-src qatorlari kerak)
```

Har bir `configure` xatosi yetishmayotgan kutubxona nomini aytadi:
`libssl-dev`, `zlib1g-dev`, `libpcre3-dev` - `-dev`/`-devel` paketlari
kompilyatorga kerak bo’lgan header’larni olib keladi, runtime paketida esa
ular yo’q.

## To’liq yo’l

```bash
cd /usr/local/src
sudo wget https://nginx.org/download/nginx-1.26.1.tar.gz
sudo wget https://nginx.org/download/nginx-1.26.1.tar.gz.asc     # imzo, agar e'lon qilingan bo'lsa
tar -xzf nginx-1.26.1.tar.gz
cd nginx-1.26.1
ls                       # README, INSTALL, configure, Makefile.in, src/
less INSTALL             # BUNI O'QING - unda opsiyalar va talablar sanab o'tilgan
```

```bash
./configure --help | less
./configure --prefix=/usr/local/nginx --with-http_ssl_module
# checking for OS ... Linux
# checking for C compiler ... found
# ./configure: error: the HTTP rewrite module requires the PCRE library.   ← libpcre3-dev'ni o'rnating va qayta ishga tushiring
make -j"$(nproc)"        # har bir CPU'dan foydalanib kompilyatsiya qiladi
make test                # yoki `make check`, agar loyihada testlar bo'lsa
sudo make install
```

| Qadam | Nima qiladi |
|---|---|
| `./configure` | tizimingizda kompilyator va kutubxonalarni tekshiradi, `--options`’laringizni o’qiydi, `Makefile` yozadi |
| `make` | kompilyatsiya qiladi - root kerak emas va tizimga hali hech narsa tegmagan |
| `sudo make install` | binary’lar, kutubxonalar, man sahifalari va konfiglarni `--prefix` ichiga nusxalaydi |
| `sudo make uninstall` | ularni o’chiradi, **agar** loyiha buni qilgan bo’lsa - ko’pchiligi qilmagan |

`--prefix=/usr/local` sukut bo’yicha qiymat va to’g’ri joy:
`/usr/local/bin`, `/usr/local/lib`, `/usr/local/etc`. Hech qachon
`/usr/bin` ichiga o’rnatmang - u paket menejerining hududi va kelajakdagi
paket yangilanishi to’qnashadi.

Ba’zi loyihalar buning o’rniga CMake yoki Meson ishlatadi:

```bash
cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr/local && cmake --build build -j"$(nproc)" && sudo cmake --install build
meson setup build --prefix=/usr/local && ninja -C build && sudo ninja -C build install
```

## O’rnatgandan keyin

```bash
which nginx; nginx -V                     # -V u qanday configure opsiyalari bilan qurilganini ko'rsatadi
echo /usr/local/lib | sudo tee /etc/ld.so.conf.d/local.conf && sudo ldconfig    # agar kutubxonalar o'sha yerga tushgan bo'lsa
export PATH=/usr/local/nginx/sbin:$PATH   # doimiy qilish uchun /etc/profile.d/ ichiga qo'shing
```

Keyin uni service qiling (systemd darsi) - source o’rnatishlari unit fayl,
logrotate konfiguratsiyasi va user account olib kelmaydi; ularni siz
yozasiz.

## Xizmat ko’rsatish muammosi

Source o’rnatish `apt`/`dnf` uchun ko’rinmaydi: xavfsizlik yangilanishlari
yo’q, bog’liqliklar kuzatilmaydi, toza o’chirish yo’q. Uni boshqarib
turishning ikki yo’li bor:

```bash
sudo apt install checkinstall
sudo checkinstall            # make install'ni bajaradi VA .deb quradi, keyin dpkg -r uni o'chiradi
```

yoki har bir versiyani o’z prefix’i ostiga o’rnating va symlink bilan
almashtiring:

```
/opt/nginx-1.26.1/  /opt/nginx-1.27.0/   and   /opt/nginx -> nginx-1.27.0
```

Shunda ortga qaytish - bitta `ln -sfn`.

:::warning
Iloji bo’lsa paketni tanlang. Kompilyatsiya qilingan `openssl` yoki `nginx`
keyingi xavfsizlik yangilanishini olmaydi, agar **siz** uni qayta
qurmasangiz; "biz buni 2023 yilda kompilyatsiya qilganmiz" - eski
zaifliklar shunday yashab qoladi. Aniq sabab bo’lgandagina kompilyatsiya
qiling, sababni va build buyrug’ini yozib qo’ying va upstream relizlarini
kuzatish uchun eslatma qo’ying.
:::

:::exam-tip
Imtihondagi kompilyatsiya topshirig’i kichik va yopiq bo’ladi: diskda
tarball turadi, uni oching, `./configure --prefix=...`, `make`,
`make install`, keyin binary ishlashini tekshiring. Avval
`INSTALL`/`README`’ni o’qing, `configure` kompilyatorni topa olmasa
`build-essential`’ni o’rnating va faqat oxirgi qadamga root kerakligini
esda tuting.
:::

## O’zingizni tekshiring

1. `./configure`, `make` va `make install`’ning har biri nima qiladi va
   qaysi biriga root kerak?
2. Nega `--prefix=/usr/local`, `/usr` emas?
3. Paket bilan solishtirganda source o’rnatishning ikkita kamchiligi
   nima va `checkinstall` bunga qanday yordam beradi?
