## Tizimga uchta eshik

Linux tizimiga mashinaning o’zidagi **matnli konsol** orqali, desktop
o’rnatilgan bo’lsa **grafik konsol** orqali yoki SSH ustidan **masofadan**
kirish mumkin. Imtihon sizdan bularning istalganini talab qilishi mumkin;
ishda esa asosan uchinchisi ishlatiladi.

```
 jismoniy klaviatura+ekran ──▶ tty1..tty6  (matn, "virtual konsollar")
                           ──▶ display manager ──▶ grafik sessiya (GNOME/KDE...)
 tarmoq ───────────────────▶ sshd ──▶ shell
```

## Matnli konsollar: TTY’lar

Kernel bir nechta **virtual konsol** beradi - `/dev/tty1` dan `/dev/tty6`
gacha, har biri o’z login prompt’i bilan (systemd’ning `getty@.service`
ostida `agetty` xizmat qiladi). Ular orasida **Ctrl+Alt+F1 … F6** bilan
almashing; desktop’siz serverda boot paytida shulardan biriga tushasiz.

```
Ubuntu 24.04 LTS server tty1

server login: ahmad
Password:
ahmad@server:~$
```

```bash
tty                      # men qaysi terminaldaman?  /dev/tty2, grafik/SSH terminal uchun esa /dev/pts/0
who                      # kim, qaysi tty da va qachondan beri kirgan
w                        # xuddi shu, ustiga har biri nima ishlatayotgani
```

TTY’dagi sessiya - sizga tegishli **shell jarayoni** (bash); `exit`,
`logout` yoki Ctrl+D uni tugatadi va `getty` prompt’ni yana ko’rsatadi.

## Grafik konsollar

Desktop o’rnatilgan bo’lsa, **display manager** (gdm, sddm, lightdm) bitta
TTY’ni - odatda tty1 yoki tty7 ni - egallaydi va grafik login’ni
ko’rsatadi. Grafik sessiyaning ichida ham matnli terminallar bor (terminal
emulyatori **psevdo-terminal**, `/dev/pts/N` ochadi), qolgan TTY’lar esa
uning ortida turaveradi: Ctrl+Alt+F3 matnli login’ga o’tkazadi, Ctrl+Alt+F1
(yoki distributivga qarab F7/F2) qaytaradi.

```bash
systemctl status display-manager        # qaysi biri va ishlayaptimi
systemctl get-default                   # graphical.target va multi-user.target (5-hafta)
```

## Masofadan: SSH

```bash
ssh user@host                           # parol yoki kalit
ssh -p 2222 user@host                   # sukut bo'yicha bo'lmagan port
ssh user@host 'uptime'                  # bitta buyruqni bajarib qaytadi
exit
```

SSH sizga masofadagi hostda psevdo-terminal (`/dev/pts/N`) beradi; shell
uchun bu mashina oldida o’tirish bilan bir xil. Server tomoni - `sshd`;
uni sozlash 10-haftada. Hozircha ikkita amaliy izoh: birinchi ulanish
sizdan host kalitiga ishonishni so’raydi (va uni `~/.ssh/known_hosts` ga
saqlaydi); yopilgan tarmoq ulanishi esa sessiyani va unda ishlayotgan
hamma narsani o’ldiradi, agar `nohup`, `tmux` yoki `screen` ishlatmagan
bo’lsangiz.

## Qaysi biri qaysi

| | TTY | grafik terminal | SSH |
|---|---|---|---|
| qurilma | `/dev/ttyN` | `/dev/pts/N` | `/dev/pts/N` |
| kerak | jismoniy kirish (yoki VM konsoli) | desktop | tarmoq + sshd |
| tarmoq uzilishidan omon qoladi | ha | ha | yo’q |
| odatdagi qo’llanish | serverlar, rescue, GUI yoki tarmoq buzilganda | ish stansiyalari | qolgan hammasi |

:::exam-tip
Imtihonda sizga beriladigan terminal allaqachon shell. Topshiriq baribir
"X hostga kiring" deyishi mumkin - bu `ssh`, host nomi esa topshiriqda.
VM konsoli yagona kirish yo’li bo’lgan holat uchun `Ctrl+Alt+Fn`
almashuvini biling, "qaysi user’lar va qayerdan kirgan" uchun esa
`who`/`w` ni biling.
:::

## O’zingizni tekshiring

1. Virtual konsol nima va ular orasida qanday almashasiz?
2. Desktop ichidagi terminal oynasi: bu TTY’mi? U qanday qurilmadan
   foydalanadi?
3. `who` va `w` sizga nimani aytadi va ular nimasi bilan farq qiladi?
