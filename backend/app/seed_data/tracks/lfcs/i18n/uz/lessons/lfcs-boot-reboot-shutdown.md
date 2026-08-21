## Mashinani to’g’ri to’xtatish

Linux tizimida ochiq fayllari bor jarayonlar, iflos cache’li filesystem’lar
va tranzaksiya o’rtasida turgan service’lar bo’ladi. Quvvatni uzish
bularning hammasini kesadi; shutdown buyruqlari esa unmount qiladi, flush
qiladi va hamma narsani tartib bilan to’xtatadi.

```bash
sudo systemctl poweroff              # hammasini to'xtatib, quvvatni o'chiradi
sudo systemctl reboot                # hammasini to'xtatib, qayta yuklaydi
sudo systemctl halt                  # hammasini to'xtatib, CPU'ni to'xtatadi (quvvat o'chmaydi)
sudo systemctl suspend               # RAM'ga
sudo systemctl hibernate             # diskka
```

Eski buyruqlar ham ishlaydi (ular `systemctl` ga symlink):

```bash
sudo poweroff; sudo reboot; sudo halt
sudo shutdown -h now                 # hozir halt / quvvatni o'chirish
sudo shutdown -r now                 # hozir qayta yuklash
sudo shutdown -h +10 "Patching at 22:10, please save your work"
sudo shutdown -r 22:30
sudo shutdown -c                     # rejalashtirilgan shutdown'ni bekor qiladi
```

## Mashinadagi odamlarni ogohlantirish

Kechikish bilan berilgan `shutdown` uchta ish qiladi: xabarni tizimga kirgan
har bir terminalga tarqatadi, yangi login’lar rad etilishi uchun
`/run/nologin` faylini yaratadi va amalni rejalashtiradi.

```bash
who                                          # kim kirgan va qayerdan
w                                            # + ular nima ishga tushirgan
wall "Rebooting in 5 minutes for kernel update"     # hech nima rejalashtirmasdan tarqatadi
sudo shutdown -r +5 "Kernel update"
sudo shutdown -c                             # fikringiz o'zgardi - bu xabar ham tarqaladi
```

## Boot qayerga ketdi: oxirgisini o’qish

```bash
uptime                       # oxirgi boot'dan beri qancha vaqt, load average
uptime -s                    # boot vaqtining o'zi
who -b                       # xuddi shu, utmp'dan
last reboot | head           # boot'lar tarixi
last -x | head               # + runlevel/shutdown yozuvlari - toza bo'ldimi?
journalctl --list-boots      # journal eslab qolgan har bir boot, id'lari bilan
journalctl -b                # shu boot logi
journalctl -b -1             # OLDINGI boot - crash'ning oxirgi so'zlari shu yerda
journalctl -b -1 -p err      # undan faqat xatolar
dmesg -T | less              # timestamp'li kernel ring buffer
systemd-analyze              # boot qancha vaqt oldi, kernel/userspace bo'yicha
systemd-analyze blame        # eng sekin unit'lar
systemd-analyze critical-chain
```

`journalctl -b -1` - "server tunda qayta yuklandi, nega" degan savolning
buyrug’i. Oxirida odatdagi shutdown satrlaridan boshqa hech narsa bo’lmasa,
bu toza reboot edi (kimdir yoki nimadir so’ragan); shunchaki to’xtab qolgan
log esa - crash yoki quvvat uzilishi.

## Masofadagi mashinani xavfsiz qayta yuklash

Qaytib kelmaydigan serverdan yomonroq narsa yo’q. Masofadan reboot qilishdan
oldin:

```bash
sudo systemctl is-enabled sshd networking     # qaytib kirish yo'li ko'tariladimi?
mount | grep -c "ro,"                          # kutilmaganda muhim narsa read-only emasmi
sudo journalctl -p err -b | tail               # reboot tuzatmaydigan hal qilinmagan xatolar
findmnt --verify                               # fstab joyidami? xato fstab yozuvi boot'ni to'sishi mumkin (11-hafta)
sudo systemctl list-units --state=failed
sync                                           # cache'larni flush qiladi (systemctl buni qiladi, lekin zarari yo'q)
sudo shutdown -r +1 "Reboot for kernel update"
```

Keyin uning qaytishini kuzating: `ping -c 100 host`, va qayta ulaning.

:::warning
`/etc/fstab` dagi noto’g’ri satr - klassik "u boshqa qaytmadi" holati: boot
paytida systemd mavjud bo’lmagan qurilmani kutadi va emergency rejimiga
tushadi - bunga esa SSH emas, konsolga kirish kerak. fstab’ni tahrirlagandan
keyin va reboot qilishdan **oldin** doim `mount -a` (yoki
`findmnt --verify`) qiling. Konsoli yo’q masofadagi mashinada shu tekshiruv
- reboot bilan data-markazga borish o’rtasidagi farq.
:::

## Majburlash, boshqa hech narsa yordam bermaganda

```bash
sudo systemctl reboot --force            # unit'larni to'xtatishni tashlab ketadi, lekin unmount qiladi
sudo systemctl reboot --force --force    # darhol, reset tugmasi kabi - oxirgi chora
# Magic SysRq, fizik konsoldan, kernel hali tirik bo'lganda:
#   Alt+SysRq+R E I S U B  ("Raising Elephants Is So Utterly Boring"):
#   unRaw, tErminate, kIll, Sync, Unmount, reBoot
echo 1 | sudo tee /proc/sys/kernel/sysrq       # o'chirilgan bo'lsa, SysRq'ni yoqadi
```

:::exam-tip
Ikkala lug’atni ham biling (`systemctl reboot` va `shutdown -r`), xabarli
kechiktirilgan shaklni (`shutdown -r +10 "msg"`) va bekor qilish uchun
`shutdown -c` ni. Oldingi boot uchun `journalctl -b -1` ni ham biling -
"tizim nega qayta yuklanganini aniqlang" ehtimoli bor topshiriq va javob
aynan o’sha yerda.
:::

## O’zingizni tekshiring

1. `shutdown -h +10 "msg"` qanday uchta ishni qiladi?
2. Qaysi buyruq shundan **oldingi** boot logini ko’rsatadi va u sizga qachon
   kerak bo’ladi?
3. Masofadagi mashinani qayta yuklashdan oldin nimani tekshirish kerak va
   qaysi fayl uning qaytishiga ko’pincha to’sqinlik qiladi?
