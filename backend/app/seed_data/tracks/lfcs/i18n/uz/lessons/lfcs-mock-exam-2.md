## LFCS mock imtihon 2

Ikki soat. O’n beshta topshiriq, jami 100. 1-mock’dan qiyinroq: LVM, NFS,
SSH’ni himoyalash, tuzatish kerak bo’lgan buzilgan service. Sizga
`/dev/sdb` va `/dev/sdc` kerak (har biri ≥3 GB). Avval snapshot.

---

**1.** (8) `/dev/sdb`’da LVM stack yarating: physical volume, `vgdata`
nomli volume group va 1 GiB hajmli `lvfiles` logical volume. Uni xfs
formatlang va `/mnt/files`’ga doimiy qilib mount qiling.

**2.** (8) `lvfiles`’ni **fayl tizimi bilan birga** 500 MiB’ga kengaytiring,
u mount qilingan holatda turgan paytda. `df -h /mnt/files` chiqishini
`/root/lvsize.txt`’da ko’rsating.

**3.** (7) `/dev/sdc`’ni `vgdata`’ga qo’shing va hosil bo’lgan bo’sh joyni
`/root/vgfree.txt`’da ko’rsating.

**4.** (7) `/srv/share`’ni `192.168.122.0/24` tarmog’iga NFS orqali
o’qish-yozish rejimida, root squashing bilan export qiling va
`/root/exports.txt`’ga yozilgan `showmount -e localhost` bilan tekshiring.

**5.** (8) SSH’ni himoyalang: root login’ni o’chiring, parol
autentifikatsiyasini o’chiring va `MaxAuthTries`’ni 3 ga qo’ying. O’z
sessiyangizni buzmang; `sshd -T` bilan tekshiring.

**6.** (7) Interaktiv tarzda tizimga kira olmaydigan, home direktoriyasi
bo’lmagan va hisobi qulflangan `svc_backup` nomli user yarating.

**7.** (6) `operators` guruhiga (uni yarating) root sifatida **parolsiz**
`/usr/bin/systemctl restart nginx`’ni ishga tushirish imkonini bering,
boshqa hech narsani emas.

**8.** (7) `brokenapp` service ishga tushmayapti (avval uni yarating:
`ExecStart` yo’li mavjud bo’lmagan `/usr/local/bin/brokenapp`’ga ishora
qiladigan unit). Uni diagnostika qiling, ishlaydigan skript yarating va
service’ni ishga tushirib enable qiling. Topgan nosozlik xabaringizni
`/root/broken.txt`’ga yozing.

**9.** (7) `/var/log/myapp/*.log` uchun `logrotate`’ni sozlang
(direktoriyani va log faylni yarating): har kuni rotate qilinsin, 7 tasi
saqlansin, siqilsin va fayl yo’q bo’lsa xato bermasin. `logrotate -d`
bilan sinab ko’ring.

**10.** (6) Tizimdagi SUID biti qo’yilgan barcha fayllarni toping va
ro’yxatni `/root/suid.txt`’ga yozing.

**11.** (7) Ikkinchi interfeysga statik IP’ni doimiy qilib o’rnating:
manzil `192.168.150.10/24`, gateway yo’q, DNS `1.1.1.1`. `ip -br a`
chiqishini `/root/ipbr.txt`’da ko’rsating.

**12.** (6) `journald`’ni jurnal reboot’lar orasida doimiy saqlanadigan
qilib sozlang va `journalctl --disk-usage`’ni `/root/journal.txt`’da
ko’rsating.

**13.** (7) `/usr/local/bin/diskcheck.sh` skriptini yozing: agar mount
qilingan biror fayl tizimi 80% dan ko’p band bo’lsa, ogohlantirish
chiqarib 1 kodi bilan chiqsin, aks holda 0 bilan chiqsin. Uni bajariladigan
qiling va ishga tushiring, chiqishni `/root/diskcheck.txt`’ga saqlang.

**14.** (5) Barcha userlar uchun sukut bo’yicha umask’ni tizim bo’ylab
`027`’ga o’rnating.

**15.** (4) `/root/facts.txt` faylini yarating, unda har bir satrda
bittadan: kernel versiyasi, CPU yadrolari soni va umumiy xotira MB’da.

---

:::exam-tip
1-3-topshiriqlar - bitta uzluksiz LVM hikoyasi va birgalikda 23 ball
turadi; agar `lvextend -r` sizga hali avtomatik bo’lmasa, bir soatlik
mashq o’zini oqlaydigan joy aynan shu. 8-topshiriq - har qanday nosozlik
savolining shakli: `systemctl status` → `journalctl -xeu` → xabar sababni
aytadi → tuzatish → `daemon-reload` → `enable --now` → tekshirish.
:::

## O’zingizni tekshiring

1. 2- va 3-topshiriqqa qaysi yagona buyruq kerak bo’ldi va LVM amallari
   qanday tartibda boradi?
2. 5-topshiriqda o’zgarishni sessiyangizni xavf ostiga qo’ymasdan qanday
   tasdiqladingiz?
3. Qaysi topshiriqlarga `daemon-reload` yoki `--reload` kerak bo’ldi va
   ularni esladingizmi?
