## Skript - bu buyruqlar fayli

Ikki marta tergan har qanday narsangiz skriptga tegishli. LFCS texnik
xizmatni avtomatlashtiradigan shell skriptlarni so’raydi: nimanidir backup
qilish, nimanidir tekshirish, nimanidir tozalash, nimadir haqida hisobot
berish.

```bash
#!/bin/bash
# backup-etc.sh - /etc ni har kuni arxivlaydi va 7 nusxani saqlaydi
set -euo pipefail

DEST=/backup
KEEP=7
STAMP=$(date +%F)

mkdir -p "$DEST"
tar -czf "$DEST/etc-$STAMP.tar.gz" -C / etc
find "$DEST" -name 'etc-*.tar.gz' -mtime +$KEEP -delete
echo "backup written: $DEST/etc-$STAMP.tar.gz"
```

```bash
chmod +x backup-etc.sh
./backup-etc.sh
bash -n backup-etc.sh        # ishga tushirmasdan sintaksisni tekshirish
bash -x backup-etc.sh        # ishlayotgan har bir buyruqni kuzatish
```

**Shebang** `#!/bin/bash` kernel’ga qaysi interpretator ishlatilishini
aytadi; u birinchi satr bo’lishi shart. `set -e` - har qanday xatoda
chiqish, `-u` - aniqlanmagan o’zgaruvchida xato, `-o pipefail` - pipeline
qismlaridan biri ishlamasa, butun pipeline ishlamaydi - jimgina buzilishni
to’xtagan skriptga aylantiradigan uchta flag.

## O’zgaruvchilar va tirnoqqa olish

```bash
name="web01"
count=5
path="/var/log/$name"
echo "Host: $name has $count logs in ${path}"
today=$(date +%F)                   # buyruq substitutsiyasi
files=$(ls /etc | wc -l)
readonly MAX=100
unset name
```

Ko’p bug’larning oldini oladigan qoidalar: **`=` atrofida probel yo’q**;
deyarli har doim qo’shtirnoq ichida `"$var"` (aks holda probelli yo’l
hammasini buzadi); nom boshqa belgilarga tegib turganda `${var}`;
harfma-harf matn uchun `'single quotes'`.

```bash
"${1:-default}"     # birinchi argument, yoki o'rnatilmagan bo'lsa "default"
"${var:?must be set}"   # bo'sh bo'lsa xabar bilan xato beradi
"${#var}"           # uzunlik
"${var%.txt}"       # suffiksni olib tashlaydi;  ${var#*/} prefiksni olib tashlaydi
"${var/old/new}"    # almashtiradi
```

## Argumentlar va muhit

```bash
$0        # skriptning nomi
$1 $2 …   # pozitsion argumentlar
$#        # nechta
$@        # hammasi, har biri alohida tirnoqda: "$@"
$?        # oxirgi buyruqning exit statusi
$$        # shu skriptning PID'i
```

```bash
if [ $# -lt 1 ]; then
    echo "usage: $0 <directory>" >&2
    exit 1
fi
DIR=$1
```

## Shartlar

```bash
if [ -f /etc/fstab ]; then
    echo "exists"
elif [ -d /etc/fstab ]; then
    echo "it is a directory"
else
    echo "missing"
fi

[[ -f $file ]] && echo "found"           # bash'ning [[ ]] i: so'z bo'linishi yo'q, =~ va && ni qo'llab-quvvatlaydi
systemctl is-active --quiet nginx || systemctl start nginx
```

| Test | Qachon rost |
|---|---|
| `-f f` / `-d d` / `-e p` | oddiy fayl / direktoriya / mavjud |
| `-r -w -x` | o’qish / yozish / bajarish mumkin |
| `-s f` | fayl bo’sh emas |
| `-z "$s"` / `-n "$s"` | satr bo’sh / bo’sh emas |
| `"$a" = "$b"` / `!=` | satrlarning tengligi |
| `$a -eq -ne -lt -le -gt -ge $b` | sonli taqqoslash |
| `[[ $s =~ ^[0-9]+$ ]]` | regex mosligi (bash) |

```bash
case "$1" in
    start)   echo "starting" ;;
    stop)    echo "stopping" ;;
    restart) $0 stop; $0 start ;;
    *)       echo "usage: $0 {start|stop|restart}" >&2; exit 1 ;;
esac
```

## Tsikllar

```bash
for f in /var/log/*.log; do
    gzip -k "$f"
done

for i in {1..5}; do echo "host$i"; done
for u in $(cut -d: -f1 /etc/passwd); do echo "$u"; done

while read -r line; do
    echo "line: $line"
done < /etc/fstab

while ! ping -c1 -W1 10.0.0.5 >/dev/null 2>&1; do
    echo "waiting for host..."; sleep 5
done

until systemctl is-active --quiet nginx; do sleep 1; done

for pid in $(pgrep old-daemon); do kill "$pid"; done
```

`break` tsikldan chiqadi, `continue` keyingi iteratsiyaga o’tkazadi.

## Funksiyalar va exit kodlar

```bash
log() { echo "[$(date +%T)] $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

check_disk() {
    local threshold=${1:-90}
    local used
    used=$(df --output=pcent / | tail -1 | tr -dc '0-9')
    (( used > threshold )) && return 1
    return 0
}

check_disk 85 || die "root filesystem above 85%"
log "disk ok"
exit 0
```

Exit `0` muvaffaqiyat degani; qolgan hammasi - nosozlik, va `cron`,
systemd hamda `&&`/`||` aynan shuni o’qiydi.

## Texnik xizmat shablonlari

```bash
# rotatsiya va tozalash
find /var/log/myapp -name '*.log' -mtime +14 -delete

# service watchdog'i
systemctl is-active --quiet myapp || { systemctl restart myapp; log "restarted myapp"; }

# cron'dan, jimgina, faylga hisobot
{ df -h; echo; free -h; echo; systemctl --failed; } > /var/log/healthcheck.log 2>&1

# bir vaqtda ikki marta ishlamasin
exec 9>/var/lock/mytask.lock
flock -n 9 || exit 0

# chiqishda tozalash, xato bo'lganda ham
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
```

:::warning
Cron’da `PATH` minimal va `$HOME` boshqacha bo’lishi mumkin - buyruqlar va
fayllar uchun absolut yo’llardan foydalaning yoki skript boshida `PATH` ni
o’rnating. Sizning shell’ingizda ishlaydigan, cron’da esa jimgina
ishlamaydigan skript deyarli har doim aynan shu (6-hafta bunga qaytadi).
:::

:::exam-tip
Skript topshirig’i kichik bo’ladi: "/usr/local/bin/x da skript yozing, u
argument sifatida direktoriyani oladi va undagi fayllar sonini chiqaradi,
direktoriya mavjud bo’lmasa 1 bilan chiqadi". Shebang, argument tekshiruvi,
`[ -d "$1" ] || exit 1`, ishning o’zi, `chmod +x`. Uni yaxshi va yomon
argument bilan sinab ko’ring va ikkala safar ham `echo $?` ni tekshiring.
:::

## O’zingizni tekshiring

1. `set -e`, `set -u` va `set -o pipefail` nima qiladi?
2. O’zgaruvchilar nega `"$var"` shaklida tirnoqqa olinishi kerak?
3. `/var/log/app` ichidagi har bir `.log` faylni gzip qiladigan tsikl
   yozing.
