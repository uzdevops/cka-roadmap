## Ikki oila, bir xil g’oyalar

| | Debian/Ubuntu | RHEL/Fedora/Rocky |
|---|---|---|
| yuqori daraja | `apt` | `dnf` (eskisi: `yum`) |
| quyi daraja | `dpkg` | `rpm` |
| paket | `.deb` | `.rpm` |
| repo konfiguratsiyasi | `/etc/apt/sources.list`, `sources.list.d/` | `/etc/yum.repos.d/*.repo` |
| kesh | `/var/cache/apt/archives/` | `/var/cache/dnf/` |
| log | `/var/log/apt/history.log` | `/var/log/dnf.log` |

Yuqori darajadagi vosita bog’liqliklarni hal qiladi va repository’lar bilan
gaplashadi; quyi darajadagisi esa diskda allaqachon turgan bitta fayl
ustida ishlaydi.

## apt: kundalik buyruqlar

```bash
sudo apt update                     # paket ro'yxatlarini yangilaydi - DOIM birinchi
sudo apt install nginx
sudo apt install nginx=1.24.0-1     # aniq bir versiya
sudo apt install -y --no-install-recommends nginx
sudo apt remove nginx               # dasturni o'chiradi, konfiguratsiya fayllarini QOLDIRADI
sudo apt purge nginx                # konfiguratsiya fayllarini ham o'chiradi
sudo apt autoremove                 # endi hech kimga kerak bo'lmagan bog'liqliklarni tashlaydi
sudo apt upgrade                    # hammasini yangilaydi (hech qachon paket o'chirmaydi)
sudo apt full-upgrade               # bog'liqliklarni qanoatlantirish uchun o'chirishi mumkin
apt search nginx
apt show nginx                      # versiya, hajm, bog'liqliklar, tavsif
apt list --installed | grep nginx
apt list --upgradable
apt-cache policy nginx              # o'rnatilgan versiya, candidate va u qaysi repo'dan kelishi
sudo apt-mark hold nginx            # qotirish: buni yangilama
sudo apt-mark unhold nginx
apt-mark showhold
sudo apt clean; sudo apt autoclean  # yuklab olingan keshni bo'shatadi
```

## dpkg: lokal qatlam

```bash
sudo dpkg -i package.deb            # yuklab olingan faylni o'rnatadi (bog'liqliklarni OLIB kelmaydi)
sudo apt install -f                 # ...keyin yetishmayotgan bog'liqliklarni tuzatadi
sudo dpkg -r nginx; sudo dpkg -P nginx
dpkg -l                             # o'rnatilganlarning hammasi ('ii' = installed ok)
dpkg -l | grep nginx
dpkg -L nginx                       # paket qaysi FAYLLARni o'rnatgan
dpkg -S /etc/nginx/nginx.conf       # bu fayl qaysi PAKETga tegishli
dpkg -s nginx                       # holat va metadata
dpkg -c package.deb                 # faylning ichidagilar, o'rnatmasdan
dpkg --get-selections > pkgs.txt    # mashinaning paket to'plamini takrorlash uchun
```

## dnf / yum

```bash
sudo dnf install nginx
sudo dnf install -y nginx-1.24.0
sudo dnf remove nginx
sudo dnf upgrade                    # hammasi (dnf update ham xuddi shu)
sudo dnf upgrade nginx
sudo dnf search nginx
dnf info nginx
dnf list installed | grep nginx
dnf list available
sudo dnf provides /usr/sbin/nginx   # bu fayl/buyruqni qaysi paket beradi
dnf repoquery -l nginx              # uning fayllar ro'yxati
sudo dnf history                    # har bir tranzaksiya, raqamlangan
sudo dnf history undo 42            # tranzaksiyani ORTGA QAYTARADI - dnf'ning eng kuchli tomoni
sudo dnf clean all
sudo dnf group install "Development Tools"
sudo dnf install epel-release       # keng tarqalgan qo'shimcha repo
```

## rpm: lokal qatlam

```bash
sudo rpm -ivh package.rpm           # o'rnatadi, batafsil, progress bilan
sudo rpm -Uvh package.rpm           # yangilaydi (yo'q bo'lsa o'rnatadi)
sudo rpm -e nginx                   # o'chiradi
rpm -qa                             # o'rnatilganlarning hammasi
rpm -qa | grep nginx
rpm -qi nginx                       # ma'lumot
rpm -ql nginx                       # fayllar ro'yxati
rpm -qf /etc/nginx/nginx.conf       # fayl qaysi paketga tegishli
rpm -qc nginx                       # faqat uning konfiguratsiya fayllari
rpm -qp --scripts package.rpm       # u qanday skriptlarni ishga tushirishi - ishonishdan oldin o'qing
rpm -V nginx                        # TEKSHIRISH: o'rnatilgandan beri qaysi fayllar o'zgargan
```

`rpm -V` chiqishidagi belgilar: `5` checksum farq qiladi, `S` hajm, `T`
vaqt, `M` rejim, `U`/`G` egasi/guruhi, `c` konfiguratsiya faylini
belgilaydi. RHEL mashinasida "kim nimani tahrirlagan" degan savolga eng tez
javob shu (Debian’da: `debsums`).

## Sizdan amalda so’raladigan savollar

| Savol | Debian | RHEL |
|---|---|---|
| X’ni o’rnatish | `apt install X` | `dnf install X` |
| X’ni konfiguratsiyasi bilan o’chirish | `apt purge X` | `dnf remove X` |
| X o’rnatilganmi, qaysi versiya | `apt list --installed \| grep X`, `dpkg -l X` | `rpm -q X` |
| /path qaysi paketga tegishli | `dpkg -S /path` | `rpm -qf /path` |
| X qanday fayllarni o’rnatgan | `dpkg -L X` | `rpm -ql X` |
| Y buyrug’ini qaysi paket beradi | `apt-file search Y` | `dnf provides Y` |
| yaqinda nima o’zgargan | `/var/log/apt/history.log` | `dnf history` |
| oxirgi o’rnatishni bekor qilish | `apt remove` / qo’lda | `dnf history undo` |

## Yangilashlarda ehtiyot bo’ling

```bash
sudo apt update && sudo apt upgrade      # tasdiqlashdan OLDIN ro'yxatni o'qing
sudo apt list --upgradable
sudo needrestart                          # kutubxona yangilangach qaysi service'larni qayta ishga tushirish kerak
sudo apt install --only-upgrade nginx     # faqat bitta paket, boshqalari emas
```

`apt upgrade` hech qachon paketlarni o’chirmaydi; `full-upgrade`/`dist-upgrade`
o’chirishi mumkin - production mashinasida `y` deb yozishdan oldin u nimani
o’chirmoqchi ekanini o’qing.

:::exam-tip
Ikkala oila ham uchrashi mumkin; imtihon Ubuntu’da, shuning uchun
`apt`/`dpkg` ehtimoli yuqori, lekin moslikni biling. "X paketini o’rnating
va u boot’da ishga tushishiga ishonch hosil qiling" - bu ikkita maqsad
birlashgani: `apt install -y X`, keyin `systemctl enable --now X`.
"/usr/bin/x qaysi paketga tegishli ekanini toping" - bu `dpkg -S`. Yangi
mashinada `apt install`’dan oldin doim `apt update` qiling.
:::

## O’zingizni tekshiring

1. `apt remove` bilan `apt purge` o’rtasida, `apt upgrade` bilan
   `apt full-upgrade` o’rtasida qanday farq bor?
2. Har bir oilada `/etc/ssh/sshd_config` qaysi paketga tegishli ekanini
   qaysi buyruq aytadi?
3. Qaysi RPM buyrug’i o’rnatilgandan beri qaysi fayllar o’zgarganini
   ko’rsatadi?
