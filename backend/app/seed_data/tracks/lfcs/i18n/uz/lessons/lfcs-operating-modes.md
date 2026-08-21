## Target’lar: "tizim ishlayapti" nimani anglatadi

SysV’da **runlevel**’lar bor edi (0-6); systemd’da **target**’lar bor -
berilgan rejim talab qiladigan service’larni guruhlaydigan nomlangan
unit’lar. Target unga kerak bo’lgan hamma narsani ishga tushirish orqali
qo’lga kiritiladi.

| Target | Eski runlevel | Ma’nosi |
|---|---|---|
| `poweroff.target` | 0 | o’chirish |
| `rescue.target` | 1, S | single user: root shell, lokal filesystem’lar, **network yo’q, boshqa service’lar yo’q** |
| `multi-user.target` | 2, 3, 4 | to’liq tizim, network, barcha service’lar, **matnli login** - server uchun sukut bo’yicha |
| `graphical.target` | 5 | multi-user + display manager |
| `reboot.target` | 6 | reboot |
| `emergency.target` | - | eng minimali: root shell, `/` **faqat o’qish uchun** mount qilingan, deyarli boshqa hech narsa yo’q |

```bash
systemctl get-default                       # graphical.target / multi-user.target
sudo systemctl set-default multi-user.target   # bundan buyon nimaga boot qilinadi (/etc/systemd/system ichidagi symlink)
ls -l /etc/systemd/system/default.target
systemctl list-units --type=target           # hozir nima aktiv
systemctl list-dependencies multi-user.target | head -30
```

## Hozirning o’zida almashtirish

```bash
sudo systemctl isolate multi-user.target     # GUI'ni to'xtating, tizim ishlab tursin
sudo systemctl isolate graphical.target      # uni qayta ishga tushiring
sudo systemctl isolate rescue.target         # single user'ga tushing (root parolini so'raydi)
sudo systemctl rescue                        # xuddi shu, ustiga wall xabari
sudo systemctl emergency
sudo systemctl default                       # sukut bo'yicha target'ga qaytish
runlevel; who -r                             # moslik ko'rinishi: "N 5"
sudo init 3                                  # hamon ishlaydi: isolate multi-user.target ga o'giriladi
```

`isolate` target’ning unit’larini ishga tushiradi va **unga kirmagan hamma
narsani to’xtatadi** - oddiy `start`’dan farqi shu. Agar target network’ni
o’z ichiga olmasa, uni SSH orqali `isolate` qilmang: `rescue.target`
ulanishingizni uzadi.

## Boot paytida rejim tanlash

GRUB menyusida yozuv ustida `e`’ni bosing va `linux` satriga qo’shing:

| Qo’shimcha | Ta’siri |
|---|---|
| `systemd.unit=rescue.target` | rescue’ga boot qilish |
| `systemd.unit=emergency.target` | emergency’ga boot qilish |
| `single` yoki `1` | rescue, eski yozilishi |
| `init=/bin/bash` | systemd umuman yo’q - `/` faqat o’qish uchun bo’lgan root shell; avval `mount -o remount,rw /` |
| `systemd.mask=some.service` | bitta unit’siz boot qilish |
| `rd.break` | initramfs’da to’xtash (RHEL) |

Ctrl+X tahrir bilan boot qiladi, faqat shu boot uchun. Buzilgan service,
yaroqsiz `fstab` yoki yo’qolgan root paroli sizni tizimga kirita olmay
qo’yganda ichkariga shunday kirasiz - va doimiy ravishda,
`/etc/default/grub` + `update-grub` orqali.

```bash
# unutilgan root parolini tiklash, init=/bin/bash dan:
mount -o remount,rw /
passwd root
exec /sbin/init          # yoki: mount -o remount,ro / ; reboot -f
```

## Rescue va emergency, amalda

| | rescue | emergency |
|---|---|---|
| filesystem’lar | lokallari rw bilan mount qilingan | faqat `/`, **faqat o’qish uchun** |
| service’lar | asosiylari ishga tushirilgan | hech biri |
| nimaga kerak | buzilgan service’ni, to’lgan diskni tuzatish | `/etc/fstab`’ni, mount bo’lmayotgan filesystem’ni tuzatish |

Emergency rejimida birinchi buyruq deyarli har doim shu:

```bash
mount -o remount,rw /
vi /etc/fstab            # aybdor satrni izohga oling
mount -a                 # qolgani joyida ekanini isbotlang
systemctl reboot
```

## Boot’ni buzadigan unit’ni mask qilish

```bash
sudo systemctl mask broken.service      # uni /dev/null ga bog'laydi: umuman ishga tushirib bo'lmaydi
sudo systemctl unmask broken.service
```

`mask` `disable`’dan kuchliroq va "bu service boot’ni osib qo’yadi" holati
uchun mo’ljallangan asbob - service’lar darsida yana ko’rib chiqiladi.

:::exam-tip
Bu maqsadni uchta buyruq qoplaydi: `systemctl get-default`, `systemctl
set-default <target>`, `systemctl isolate <target>`. Ikkita foydali
target’ni nomi bilan biling (`multi-user`, `graphical`) va ikkita tiklash
target’ini (`rescue`, `emergency`). Agar topshiriqda "tizim buyruq satriga
boot qilsin" deyilgan bo’lsa, bu `set-default multi-user.target` - va
`get-default` bilan tekshiring.
:::

## O’zingizni tekshiring

1. `systemctl start` va `systemctl isolate` orasidagi farq nima?
2. Server odatda qaysi target’ga boot qiladi va uni qanday qilib doimiy
   o’zgartirasiz?
3. Emergency rejimida nega `mount -o remount,rw /` deyarli har doim
   birinchi buyruq bo’ladi?
