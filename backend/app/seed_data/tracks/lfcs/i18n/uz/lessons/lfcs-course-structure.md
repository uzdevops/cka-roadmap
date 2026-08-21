## Beshta soha va ularning og’irliklari

Imtihon topshiriqlari beshta sohadan olinadi. Og’irliklar har biriga nechta
topshiriq tegishini - demak, o’qish soatlaringiz qayerga ketishini -
belgilaydi.

| Soha | Og’irlik | Bu yo’nalishda |
|---|---|---|
| **Operations Deployment** | **25%** | 5-7-haftalar |
| **Networking** | **25%** | 9-10-haftalar |
| **Storage** | **20%** | 11-12-haftalar |
| **Essential Commands** | **20%** | 1-4-haftalar |
| **Users and Groups** | **10%** | 8-hafta |

(Og’irliklar Linux Foundation’ning joriy soha ro’yxatidan; ro’yxatdan
o’tayotganda imtihon sahifasidan tekshiring - ular bir-ikki yilda bir
qayta ko’rib chiqiladi.)

Imtihonning yarmi - operations va networking. Aynan shu sohalarda
topshiriqlar eng uzun: systemd unit’i, firewall qoidalari to’plami, bond
qilingan interfeys - shuning uchun u yerga sarflagan vaqtingiz ikki barobar
qaytadi.

## Modul-modul

**Essential Commands (1-4-haftalar)** - hamma bilaman deb o’ylaydigan
narsalar: tizimga kirish, `man`, fayllar va linklar, SUID/SGID/sticky bilan
birga ruxsatlar, `find`, matn vositalari (`sort`, `cut`, `sed`, `tr`), oddiy
va kengaytirilgan muntazam ifodalar bilan `grep`, `tar` va kompressorlar,
redirection va pipe’lar, `openssl` bilan sertifikat o’qish va yaratish hamda
Git asoslari. Buni hamma "biladi"; imtihon esa buni tez va aniq qila
olasizmi - shuni tekshiradi.

**Operations Deployment (5-7-haftalar)** - tizim ishlayotgan narsa
sifatida: yuklanish, target’lar, ma’lumot yo’qotmasdan o’chirish; shell
skript yozish; `systemctl` va **unit fayl yozish**; jarayonlar va signallar;
`journalctl` va `/var/log`; `cron`, `at` va timer’lar; paketlar va
repozitoriylar; manbadan kompilyatsiya; butunlik va resurslarni tekshirish;
`sysctl`; **SELinux** kontekstlari va boolean’lari; podman/docker bilan
konteynerlar; libvirt bilan VM’lar.

**Users and Groups (8-hafta)** - `useradd` va uning hamrohlari hamda ular
ortidagi fayllar, guruhlar, `/etc/skel`, profillar, `ulimit` va
`limits.conf`, `sudo` va `visudo`, root’ga kirish siyosati va hostni LDAP’ga
yo’naltirish.

**Networking (9-10-haftalar)** - `nmcli` va netplan bilan manzillash va
nom yechish, `ss` bilan service’larni tekshirish, bridge va bond’lar,
**firewalld va nftables**, **NAT va port yo’naltirish**, reverse proxy va
yuk muvozanatlagich sifatida nginx, `chrony` va kalitlar bilan `sshd`
himoyasi.

**Storage (11-12-haftalar)** - `fdisk`/`parted` bilan partition’lar, swap,
`mkfs`, **`/etc/fstab`**, mount opsiyalari, NFS server va klient, NBD,
**LVM** yaratish/kengaytirish/kichraytirish, `iostat`/`iotop` va `setfacl`
bilan ACL’lar.

**Exam prep (13-hafta)** - to’rtta mock va xulosa.

## Topshiriqning ko’rinishi

Ko’pchilik topshiriq - ikki-uchta buyruq va bitta tekshiruv, maqsadlar
ro’yxatidagidek ifodalangan: "`vg0` volume group’ida `data` nomli 2 GiB
logical volume yarating, uni ext4 formatlang va `/mnt/data` ga doimiy
qilib mount qiling." Har bir kalit so’z - alohida qadam va nosozlik nuqtasi.
13-haftadagi mock’lar aynan shu ohangda yozilgan, toki bu til begona
tuyulmay qolsin.

:::exam-tip
Og’irliklarni yana bir bor o’qing: Users and Groups’dan mukammal ball
imtihonning 10% i, Operations Deployment’dan mukammal ball esa 25% i. O’tish
chegarasi uchdan ikki atrofida. Bitta kichik sohada zaif bo’lsangiz
chidasa bo’ladi; operations yoki networking’da zaif bo’lish esa mumkin emas.
:::

## O’zingizni tekshiring

1. Qaysi ikki soha birgalikda imtihonning yarmini tashkil qiladi?
2. Qaysi hafta systemd unit fayllarini, qaysi hafta LVM’ni qamrab oladi?
3. "2 GiB logical volume yarating... doimiy qilib mount qiling" topshirig’ini
   oling: u yashirgan qadamlarni sanab bering.
