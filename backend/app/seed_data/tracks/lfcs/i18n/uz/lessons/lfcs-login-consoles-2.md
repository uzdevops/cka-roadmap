## Sessiya nima

Siz tizimga kirganingizda - TTY’da, display manager orqali yoki SSH
ustidan - tizim **sessiya** boshlaydi: login jarayoni sizni
autentifikatsiya qiladi (PAM), shaxsingiz va muhitingizni o’rnatadi hamda
**login shell**’ingizni (yoki desktop’ni) ishga tushiradi. Siz ishga
tushirgan hamma narsa - o’sha shell’ning bolasi. Chiqib ketsangiz, shell
tugaydi; uning bolalari `SIGHUP` oladi va odatda u bilan birga tugaydi.

```bash
echo $SHELL                 # /etc/passwd dan olingan login shell'ingiz
echo $$                     # shell'ning PID'i
ps -o pid,ppid,tty,cmd -u $USER
loginctl list-sessions      # systemd-logind ko'zi bilan: har bir sessiya, uning user'i, seat/tty yoki masofaviy
loginctl show-session 3
last | head                 # /var/log/wtmp dan login tarixi: kim, qayerdan, qancha vaqt
lastlog                     # har bir user'ning eng so'nggi login'i
```

## Almashish va multipleksatsiya

Jismoniy yoki VM konsolida **Ctrl+Alt+F1…F6** TTY’lar orasida ko’chiradi;
har biri alohida login’ni ushlab turishi mumkin - biri o’z nomingizdan,
biri favqulodda holat uchun root sifatida, biri logni kuzatib. Faqat
matnli sessiyada (`Alt+Gr` desktop yorliqlari yo’q) yolg’iz **Alt+F2**
almashtiradi.

```bash
chvt 3                      # buyruq satridan tty3 ga o'tish (root)
```

SSH ustida almashadigan TTY’lar yo’q; ekvivalenti - **multiplekser**:
`tmux` yoki `screen` ulanish uzilganda sessiyalarni tirik saqlaydi va
ularni bo’lish hamda ular orasida almashish imkonini beradi.

```bash
tmux                        # yangi sessiya; Ctrl+b d uni ajratadi
tmux ls; tmux attach        # uzilgan ulanishdan keyin qaytish
```

## Xavfsiz chiqish

| Qayerda | Qanday |
|---|---|
| shell | `exit`, `logout` yoki bo’sh satrda Ctrl+D |
| grafik sessiya | desktop’ning chiqish menyusi; yoki `loginctl terminate-session <id>` |
| boshqa user’ning sessiyasi (root) | `loginctl terminate-session <id>`, `pkill -KILL -u user`, `loginctl kill-user user` |

"Xavfsiz" degani: yozuvning o’rtasida emas. User’ni chiqarib yuborishdan
yoki qayta yuklashdan oldin `w` ular nima ishlatayotganini ko’rsatadi;
`wall "message"` har bir terminalga yozadi; `shutdown +5` (5-hafta)
ularga vaqt beradi va yangi login’larni bloklaydi.

## Kim kirgan va qayerdan

```bash
who
# ahmad    tty1         2026-08-19 09:12
# ahmad    pts/0        2026-08-19 09:20 (10.0.0.7)
# backup   pts/1        2026-08-19 09:31 (10.0.0.9)
w
# 09:35:02 up 2 days,  3 users,  load average: 0.10, 0.05, 0.01
# USER     TTY      FROM       LOGIN@   IDLE   WHAT
# ahmad    pts/0    10.0.0.7   09:20    0.00s  w
```

`FROM` ustuni va `last` "tunning uchida bu mashinada kim bo’lgan" degan
audit savoliga javob beradi; `who -b` oxirgi boot vaqtini beradi; `users`
esa yalang’och ro’yxatni.

## Root’ning sessiyasi

To’g’ridan-to’g’ri root sifatida kirish odatda o’chirilgan (8-hafta); siz
o’z nomingizdan kirasiz va huquqni ko’tarasiz: root login shell uchun
`sudo -i`, root’da parol bo’lsa `su -`. Har ikki holatda ham sessiya
sizniki - `who` baribir sizni ko’rsatadi - va `sudo` logi nima
qilganingizni yozib qo’yadi.

:::tip
Masofadagi har qanday ishda `tmux` ni refleksga aylantiring: boshida
`tmux new -s work`, uzilgan ulanishdan keyin `tmux attach -t work`. Bu
"tarmoq uzildi va 40 daqiqalik ishim o’ldi" ni "qayta ulanib davom etaman"
ga aylantiradi.
:::

## O’zingizni tekshiring

1. Login shell’ingiz tugaganda siz ishga tushirgan dasturlarga nima
   bo’ladi?
2. Grafik va masofaviylarini ham qo’shib, har bir faol sessiyani bitta
   buyruq bilan qanday ko’rasiz?
3. Boshqa user’ni majburan chiqarib yuborishdan oldin nimani ishga
   tushirasiz va nega?
