## Paketlar qayerdan keladi

Repository - bu paketlarni va imzolangan indeksni saqlaydigan server.
Mashinangizda ularning ro’yxati bor; `apt update` / `dnf makecache`
indekslarni yuklab oladi; o’rnatish esa eng yaxshi versiyani taklif
qiladigan repository’dan bo’ladi.

## Debian/Ubuntu: sources.list

```bash
cat /etc/apt/sources.list
ls /etc/apt/sources.list.d/
```

```
deb http://archive.ubuntu.com/ubuntu noble main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu noble-security main restricted
deb http://archive.ubuntu.com/ubuntu noble-updates main restricted universe
# deb-src ...   ← source paketlari, kompilyatsiya uchun
```

`deb` turi, URL, **suite** (`noble`, `noble-updates`, `noble-backports`),
keyin **komponentlar**: `main` (qo’llab-quvvatlanadigan erkin),
`restricted` (drayverlar), `universe` (jamoa), `multiverse` (erkin
bo’lmagan).

Zamonaviy deb822 shakli, har bir repository uchun bitta fayl:

```
# /etc/apt/sources.list.d/docker.sources
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: noble
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
```

## Uchinchi tomon repository’sini to’g’ri qo’shish

Repository’larga GPG kaliti orqali ishoniladi. Eski `apt-key add` eskirgan
(u kalitni *har bir* repo uchun ishonchli deb hisoblardi); hozirgi usul
kalitni `/etc/apt/keyrings` ichiga qo’yadi va source faylidan unga
murojaat qiladi:

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo tee /etc/apt/keyrings/docker.asc > /dev/null
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
apt-cache policy docker-ce         # candidate versiya qaysi repo'dan keladi
```

Oddiyroq yordamchilar:

```bash
sudo add-apt-repository universe                 # komponentni yoqadi
sudo add-apt-repository ppa:user/ppa-name        # Ubuntu PPA (source + kalit qo'shadi)
sudo add-apt-repository --remove ppa:user/ppa-name
sudo apt update
```

## Pinning va prioritetlar (Debian)

```bash
apt-cache policy nginx
# Installed: 1.24.0-1
# Candidate: 1.26.0-1
#   500 https://nginx.org/packages/ubuntu noble/nginx amd64 Packages
#   500 http://archive.ubuntu.com/ubuntu noble/main amd64 Packages
```

```
# /etc/apt/preferences.d/nginx
Package: nginx
Pin: origin nginx.org
Pin-Priority: 900
```

Yuqori prioritet g’olib chiqadi. Ikkita repository bir xil paketni taklif
qilsa va sizga aniq bir origin kerak bo’lsa, shundan foydalaning; "buni
hech qachon yangilama" uchun `apt-mark hold` - qo’polroq vosita.

## RHEL oilasi: .repo fayllari

```bash
ls /etc/yum.repos.d/
cat /etc/yum.repos.d/docker-ce.repo
```

```ini
[docker-ce-stable]
name=Docker CE Stable - $basearch
baseurl=https://download.docker.com/linux/centos/$releasever/$basearch/stable
enabled=1
gpgcheck=1
gpgkey=https://download.docker.com/linux/centos/gpg
```

```bash
dnf repolist                                  # yoqilgan repository'lar
dnf repolist --all                            # o'chirilganlari bilan birga
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf config-manager --set-enabled crb
sudo dnf config-manager --set-disabled docker-ce-test
sudo rpm --import https://download.docker.com/linux/centos/gpg
sudo dnf install epel-release
sudo dnf clean all && sudo dnf makecache
sudo dnf --disablerepo=* --enablerepo=base install x       # faqat bitta buyruq uchun
```

## Tekshirish va nosozlikni bartaraf etish

```bash
apt-key list                       # eskirgan, lekin eski kalitlarni ko'rsatadi
ls /etc/apt/trusted.gpg.d/ /etc/apt/keyrings/
sudo apt update 2>&1 | grep -i "NO_PUBKEY\|not signed\|Failed"
```

| Xabar | Sabab | Yechim |
|---|---|---|
| `NO_PUBKEY 1234ABCD` | repository’ning kaliti o’rnatilmagan | kalitni `/etc/apt/keyrings` ichiga oling va `signed-by` bilan unga murojaat qiling |
| `Repository ... is not signed` | kalit yo’q yoki kalit yo’li noto’g’ri | xuddi shunday |
| `apt update`’da `404 Not Found` | suite/codename noto’g’ri yoki repo sizning relizingizni tashlab yuborgan | source faylidagi codename’ni to’g’rilang |
| `Unable to locate package X` | uni beradigan komponent yoki repo yoqilmagan | `add-apt-repository universe`, keyin `apt update` |
| `Conflicting values set for option Signed-By` | bir xil repo ikki marta, har xil kalitlar bilan ko’rsatilgan | ortiqcha `.list`/`.sources` faylini o’chiring |
| dnf: `GPG check FAILED` | kalit yo’q yoki paket buzilgan | to’g’ri kalitni import qiling; buni "tuzatish" uchun hech qachon `gpgcheck=0` qilmang |

Lokal repository’lar, tarmoqdan uzilgan mashinalar uchun:

```bash
sudo apt install dpkg-dev && dpkg-scanpackages . | gzip > Packages.gz     # directory repo sifatida
echo "deb [trusted=yes] file:/srv/repo ./" | sudo tee /etc/apt/sources.list.d/local.list
sudo dnf install createrepo_c && createrepo_c /srv/repo                    # RPM tomoni
```

:::warning
`gpgcheck=0`, `[trusted=yes]` va `--allow-unauthenticated` - bularning
hammasi "bu server menga nima yuborsa, root sifatida ishlat" degani. Ular
o’zingiz qurgan lokal mirror’lar uchun mavjud. Internetdan kelgan kalit
xatosini o’chirish uchun ulardan hech qachon foydalanmang - kalitni
tuzating.
:::

:::exam-tip
Ehtimoliy topshiriq: "K kaliti bilan R repository’sini qo’shing va undan P
paketini o’rnating". Ketma-ketlik: kalit → source fayli → `apt update` →
`apt install`, keyin u R’dan kelganini isbotlash uchun `apt-cache policy
P`. Fayllar qayerda turishini (`/etc/apt/sources.list.d/`,
`/etc/yum.repos.d/`) va indeks yangilanmaguncha hech narsa kuchga
kirmasligini biling.
:::

## O’zingizni tekshiring

1. sources.list’dagi `deb` satrining to’rtta qismi nima?
2. `apt-key add` nega eskirgan va uning o’rniga nima keladi?
3. `apt update` `NO_PUBKEY` deb xabar berdi. Nima yetishmayapti va nima
   sizning yechimingiz bo’lmasligi kerak?
