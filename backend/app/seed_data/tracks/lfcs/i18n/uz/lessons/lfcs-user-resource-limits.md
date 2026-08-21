## Bitta user mashinani egallab olishiga yo’l qo’ymaslik

Limitlar process nimani qancha iste’mol qilishini cheklaydi - ochiq
fayllar, process’lar, xotira, CPU vaqti. Ularsiz nazoratdan chiqqan bitta
tsikl yoki bitta fork bomba host’ni yiqitadi.

## ulimit: shell nuqtai nazari

```bash
ulimit -a                # shu shell uchun hamma limitlar
# core file size          (blocks, -c) 0
# data seg size           (kbytes, -d) unlimited
# open files                      (-n) 1024
# max user processes              (-u) 15678
# virtual memory          (kbytes, -v) unlimited
ulimit -n                # bitta qiymat
ulimit -Hn               # HARD limit (shift)
ulimit -Sn               # SOFT limit (hozir amal qiladigani)
ulimit -n 4096           # soft limitni hard limitgacha ko'tarish - faqat shu shell
ulimit -Hn 8192          # hard limitni pasaytirish (uni faqat root ko'tara oladi)
```

Har bir limitning **soft** qiymati (amalda qo’llanadi, user uni hard
qiymatgacha ko’tara oladi) va **hard** qiymati (shift; uni faqat root
ko’taradi) bo’ladi. `ulimit` o’zgarishi shell va uning bolalari uchun
saqlanadi hamda shell bilan birga o’ladi.

| Flag | Nimani cheklaydi |
|---|---|
| `-n` | ochiq file descriptor’lar - amalda o’zgartiradiganingiz shu |
| `-u` | har bir user uchun process’lar - fork bombaga qarshi |
| `-f` | process yarata oladigan maksimal fayl hajmi |
| `-c` | core dump hajmi |
| `-v` | virtual xotira |
| `-m` | rezident xotira |
| `-t` | CPU sekundlari |
| `-s` | stack hajmi |
| `-l` | qulflangan xotira |

## Doimiy limitlar: /etc/security/limits.conf

Ularni PAM’ning `pam_limits` moduli **login paytida** o’qiydi, shuning
uchun ular login shell’lar, SSH sessiyalari va su uchun amal qiladi -
systemd service’lari uchun emas.

```
# /etc/security/limits.conf   (yoki /etc/security/limits.d/ ichidagi fayl)
#<domain>   <type>  <item>   <value>
alice        soft   nofile   4096
alice        hard   nofile   8192
@developers  soft   nproc    100
@developers  hard   nproc    200
*            hard   core     0
*            soft   nofile   2048
root         hard   nofile   65536
```

- **domain**: username, `@group`, `*` (root’dan tashqari hamma) yoki
  guruh bo’yicha umumiy qiymat uchun `%group`.
- **type**: `soft`, `hard` yoki ikkalasi uchun birdaniga `-`.
- **item**: `nofile`, `nproc`, `fsize`, `core`, `memlock`, `cpu`, `as`,
  `maxlogins`, `priority`.

```bash
sudo tee /etc/security/limits.d/90-developers.conf <<'EOF'
@developers  soft  nofile  4096
@developers  hard  nofile  8192
@developers  hard  nproc   200
EOF
```

`limits.conf`’ni tahrirlagandan ko’ra `limits.d/` ichidagi alohida fayl
afzal. User **chiqib, qaytadan kirishi** kerak; mavjud sessiyadagi
`ulimit -a` eski qiymatlarni ko’rsatadi.

```bash
grep pam_limits /etc/pam.d/common-session /etc/pam.d/sshd    # PAM ularni qo'llayotganini tasdiqlash
su - alice -c 'ulimit -a'                                     # user nomidan sinash
```

## Service’lar uchun limitlar: systemd

`limits.conf` unit’larga **amal qilmaydi** - systemd ularni login orqali
emas, to’g’ridan-to’g’ri ishga tushiradi. Unit’dan foydalaning:

```ini
[Service]
LimitNOFILE=65535
LimitNPROC=512
LimitCORE=0
MemoryMax=2G            # cgroup limitlari, rlimit'lardan kuchliroq
CPUQuota=50%
TasksMax=4096
```

```bash
sudo systemctl daemon-reload && sudo systemctl restart myapp
systemctl show myapp -p LimitNOFILE -p MemoryMax
cat /proc/$(pgrep -f myapp | head -1)/limits
```

Hamma unit’lar uchun sukut qiymatlari: `/etc/systemd/system.conf`
ichidagi `DefaultLimitNOFILE=`, user sessiyalari uchun esa `logind.conf`
ichidagi `UserTasksMax=`.

## Tizim bo’ylab shiftlar

```bash
sysctl fs.file-max                    # kernel bo'yicha ochiq fayllar
sysctl kernel.pid_max                 # maksimal PID'lar
sysctl -w fs.file-max=200000
cat /proc/sys/fs/file-nr              # ajratilgan / bo'sh / maksimal, ayni damda
```

Har bir user uchun `fs.file-max`’dan yuqori qo’yilgan `nofile` qiymatiga
yetib bo’lmaydi - database yoki web server’ni sozlaganda ikkalasini ham
ko’taring.

## Ishlayotgan process’ni tekshirish

```bash
cat /proc/1234/limits
prlimit --pid 1234                     # o'qishga qulay jadval
sudo prlimit --pid 1234 --nofile=8192:16384    # ISHLAYOTGAN process limitlarini o'zgartirish
ulimit -a
```

Aynan shu `prlimit` - "service’ga ko’proq file descriptor kerak, lekin men
uni hozir qayta ishga tushira olmayman" degan holatning javobi.

:::warning
`nproc` limiti UID’ning **hamma** process’larini sanaydi, SSH sessiyalari
ham shular ichida - uni juda past qo’ysangiz, user buni tuzatish uchun
tizimga kira olmaydi. Bundan tashqari limits.conf’dagi `*` domeni root’ni
qamrab olmaydi; odamlar uchun mos `nofile` o’z user’i ostida ishlaydigan
database uchun juda kichik bo’lishi mumkin, unga baribir unit sozlamasi
kerak.
:::

:::exam-tip
"X user’ini N ta ochiq fayl / process bilan cheklang" →
`/etc/security/limits.d/*.conf` ichida soft va hard birga yozilgan qator,
so’ng `su - X -c 'ulimit -n'` bilan tekshiring (yangi login, sizning
shell’ingiz emas). Agar topshiriq **service** haqida bo’lsa, javob -
limits.conf emas, unit ichidagi `LimitNOFILE=`.
:::

## O’zingizni tekshiring

1. Soft va hard limit o’rtasidagi farq nima va ularning har birini kim
   ko’tara oladi?
2. Nega `limits.conf` systemd service’iga ta’sir qilmaydi va nima ta’sir
   qiladi?
3. Allaqachon ishlayotgan process limitlarini qanday tekshirasiz va uni
   qayta ishga tushirmasdan qanday o’zgartirasiz?
