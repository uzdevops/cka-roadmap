## Nima ishlayotganini ko’rish

```bash
ps aux                       # BSD uslubi: har bir jarayon, %CPU, %MEM, START, TIME, COMMAND bilan
ps -ef                       # System V uslubi: UID, PID, PPID, C, STIME, TTY, TIME, CMD
ps -ef --forest              # ota/bola daraxti
ps aux --sort=-%mem | head   # eng ko'p xotira ishlatuvchilar
ps aux --sort=-%cpu | head
ps -u ahmad                  # bitta user'niki
ps -p 1234 -o pid,ppid,user,stat,etime,cmd
ps -eo pid,ppid,user,pri,ni,stat,%cpu,%mem,etime,cmd --sort=-%cpu | head
pgrep -a nginx               # nom bo'yicha PID'lar (va buyruq satrlari) - ps|grep dan yaxshiroq
pgrep -u ahmad -l
pidof sshd
pstree -p                    # daraxt, ixcham ko'rinishda
```

**STAT** ustuni: `R` ishlayapti, `S` uxlayapti (uzilishi mumkin), `D`
uzib bo’lmaydigan uyqu (odatda I/O da bloklangan - `D` holatidagi
jarayonni hatto kill ham qilib bo’lmaydi), `T` to’xtatilgan, `Z` zombie
(tugagan, ota-jarayon uni yig’ib olmagan), ustiga `s` sessiya lideri, `+`
foreground, `<` yuqori prioritet, `N` past.

## Jonli ko’rinishlar

```bash
top                          # interaktiv
# top ichida: P CPU bo'yicha saralash, M xotira bo'yicha, k kill, r renice, u user bo'yicha filtr, 1 har bir CPU, h yordam, q chiqish
htop                         # chiroyliroq, o'rnatilgan bo'lsa
uptime                       # load average: 1, 5, 15 daqiqa
vmstat 1 5                   # CPU/xotira/IO suratlari
free -h                      # xotira; ahamiyatlisi "available" ustuni
```

Load average - ishlayotgan **yoki I/O ni kutayotgan** jarayonlar soni;
uni CPU soni bilan solishtiring (`nproc`). 4 ta CPU’da 4.0 - to’liq
bandlik; 1 ta CPU’da 4.0 - navbat.

## Signal’lar

```bash
kill 1234                    # SIGTERM (15): "iltimos, to'xta" - sukut bo'yichasi va muloyimi
kill -15 1234
kill -9 1234                 # SIGKILL: kernel uni o'ldiradi; tozalash YO'Q, saqlanmagan ma'lumot yo'qoladi
kill -HUP 1234               # ko'p daemon'lar SIGHUP'da configini qayta o'qiydi
kill -l                      # har bir signal nomi va raqami
killall nginx                # aniq nom bo'yicha
killall -u ahmad             # user'ning hamma narsasi
pkill -f "python.*worker"    # to'liq buyruq satri shabloni bo'yicha
pkill -HUP -x sshd
```

| Signal | # | Ma’nosi |
|---|---|---|
| `SIGTERM` | 15 | muloyim tugatish (ushlab qolsa bo’ladi) - **doim avval shuni sinang** |
| `SIGKILL` | 9 | darhol o’ldirish (ushlab qolib bo’lmaydi) |
| `SIGHUP` | 1 | hang-up; kelishuvga ko’ra daemon’lar uchun "configni qayta o’qi" |
| `SIGINT` | 2 | Ctrl-C |
| `SIGSTOP` / `SIGCONT` | 19/18 | pauza / davom ettirish |
| `SIGQUIT` | 3 | core dump bilan chiqish |

`D` holatidagi jarayon I/O si tugaguncha hatto SIGKILL’ni ham e’tiborsiz
qoldiradi; **zombie** (`Z`) esa allaqachon o’lgan - uni kill qilib
bo’lmaydi, siz uning ota-jarayonini qayta ishga tushirasiz yoki
tuzatasiz.

## Prioritetlar: nice va renice

Niceness **-20 (eng imtiyozli)** dan **19 (eng imtiyozsiz)** gacha
boradi; sukut bo’yicha 0. Uni faqat root pasaytira oladi (ya’ni jarayonni
muhimroq qila oladi).

```bash
nice -n 10 tar -czf backup.tar.gz /data      # ishni muloyim boshlash
nice -n -5 ./important                        # faqat root
renice -n 5 -p 1234                           # ishlayotgan jarayonni o'zgartirish
renice -n 10 -u batchuser                     # user'ning hammasi
ps -eo pid,ni,cmd | grep tar
ionice -c3 -p 1234                            # I/O prioriteti: idle klassi - backup'lar uchun
```

## Foreground, background va logout’dan omon qolish

```bash
long-job &                   # background'da ishga tushirish
jobs                         # shu shell'ning job'lari: [1]+ Running
fg %1                        # foreground'ga olib chiqish
bg %1                        # to'xtatilgan job'ni background'da davom ettirish
# Ctrl-Z  foreground'dagi job'ni to'xtatib turadi (SIGTSTP), keyin bg yoki fg
kill %1                      # job raqami bo'yicha
nohup long-job > job.log 2>&1 &     # SIGHUP'ga befarq: logout'dan omon qoladi
disown -h %1                        # allaqachon ishlayotgan job'ni shell'dan uzadi
setsid long-job                     # yangi sessiya, to'liq uzilgan
tmux new -s work                    # masofadan ishlash uchun amaliy javob
```

Terminalni yopish uning job’lariga SIGHUP yuboradi; `nohup`, `disown`,
`setsid` yoki multiplekser - bundan omon qolishning to’rt yo’li.

## Aybdorni topish

```bash
ps aux --sort=-%cpu | head -5
top -b -n1 | head -20                     # batch rejimi, skriptlar va loglar uchun
lsof -p 1234                              # jarayon ochib qo'ygan har bir fayl/socket
lsof /var/log/app.log                     # bu faylni qaysi jarayon ushlab turibdi
lsof -i :8080                             # portni kim tinglayapti (yana: ss -tulpn)
fuser -v /mnt/data                        # mount nuqtasini kim ishlatayapti (unmount qilishdan oldin)
fuser -km /mnt/data                       # ularni kill qiladi (ehtiyot bo'ling)
strace -p 1234                            # syscall'lar, jonli
cat /proc/1234/status; cat /proc/1234/limits; ls -l /proc/1234/cwd /proc/1234/exe
```

## Resurs limitlari, har bir jarayon uchun

```bash
ulimit -a                    # joriy shell'ning limitlari
ulimit -n 4096               # maksimal ochiq fayllar, shu shell uchun
cat /proc/1234/limits        # ishlayotgan jarayonniki
systemctl show myapp -p LimitNOFILE
```

Har bir user uchun doimiy limitlar - `/etc/security/limits.conf`
(8-hafta); har bir service uchun esa unit ichidagi `LimitNOFILE=`.

:::exam-tip
Ehtimoliy topshiriqlar: "eng ko’p xotira ishlatayotgan jarayonni toping va
uning PID’ini yozib oling" (`ps aux --sort=-%mem | head -2`), "X nomli
jarayonni tugating" (`pkill X`, `pgrep` bilan tekshiring), "Y ni 10 nice
qiymati bilan ishga tushiring" (`nice -n 10 Y`), "Z PID’ining prioritetini
5 ga o’zgartiring" (`renice -n 5 -p Z`). `ps -o pid,ni,cmd -p <pid>` bilan
tekshiring. SIGKILL’dan oldin SIGTERM’ni sinab ko’ring - ba’zi
tekshiruvchilar jarayon toza tugaganini nazorat qiladi.
:::

## O’zingizni tekshiring

1. SIGTERM va SIGKILL orasidagi farq nima va avval qaysi birini
   yuborasiz?
2. `Z` holati nimani anglatadi va bunday jarayondan qanday qutulasiz?
3. Qaysi buyruq unmount qilishga to’sqinlik qilayotgan faylni qaysi
   jarayon ushlab turganini ko’rsatadi?
