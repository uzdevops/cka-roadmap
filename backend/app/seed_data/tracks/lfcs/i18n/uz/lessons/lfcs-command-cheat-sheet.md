## Ma’lumot kartochkasi

Bu darsni butun yo’nalish davomida ochiq tuting. U ataylab qisqa: buyruq,
ahamiyatga ega bayroqlar, bitta misol. Har bir satr o’z darsida to’liq
tushuntiriladi; bu esa siz qaytib keladigan joy.

## Yordam olish

| | |
|---|---|
| `man cmd`, `man 5 fstab`, `man -k keyword` (`apropos`) | bo’limlar bo’yicha qo’llanma; sarlavhalar bo’yicha qidiruv |
| `cmd --help`, `help cd` (shell builtins) | tez sintaksis |
| `info cmd`, `/usr/share/doc/pkg/` | uzunroq hujjatlar, misollar |
| `type cmd`, `which cmd`, `whereis cmd` | nom nimaga yechilishi |

## Fayllar

| | |
|---|---|
| `ls -la`, `ls -li` (inodes), `ls -lZ` (SELinux), `stat f` | ko’rish |
| `cp -r`, `cp -a` (preserve), `mv`, `rm -rf`, `mkdir -p`, `touch`, `rmdir` | yaratish/ko’chirish/o’chirish |
| `ln target hard`, `ln -s target soft`, `readlink -f` | linklar |
| `find / -name x -type f -size +1M -mtime -7 -perm -4000 -user u -exec cmd {} \;` | qidiruv |
| `locate x` (`updatedb`) | indekslangan qidiruv |
| `cat`, `head -n`, `tail -n`/`-f`, `less`, `wc -l` | o’qish |
| `sort -n/-r/-k2`, `uniq -c`, `cut -d: -f1`, `tr a-z A-Z`, `paste`, `diff -u a b` | o’zgartirish |
| `sed 's/a/b/g' f`, `sed -i`, `sed -n '3,5p'`, `awk -F: '{print $1}'` | oqimlarni tahrirlash |
| `grep -i -n -r -v -c -E -w -o 'pat' f` | mazmun bo’yicha qidiruv |
| `tar czf a.tgz dir`, `tar xzf a.tgz -C /dst`, `tar tf`, `-j` bz2, `-J` xz | arxivlash |
| `gzip/gunzip`, `bzip2`, `xz`, `zip -r`/`unzip` | siqish |
| `rsync -av src/ user@host:/dst/`, `scp -r f host:/dst` | masofaga nusxalash |
| `>` `>>` `2>` `2>&1` `&>` `<` `<<EOF` `\|` `\| tee f` | redirection |

## Ruxsatlar

| | |
|---|---|
| `chmod u+x f`, `chmod 644 f`, `chmod -R g+w d`, `chmod 4755` (SUID) `2775` (SGID) `1777` (sticky) | rejim |
| `chown user:group f`, `chgrp g f`, `umask`, `umask 027` | egasi, sukut qiymatlari |
| `getfacl f`, `setfacl -m u:bob:rw f`, `setfacl -d -m g:dev:rwx d`, `setfacl -x u:bob f`, `setfacl -b f` | ACL’lar |
| `lsattr f`, `chattr +i f` (immutable), `chattr +a` (append-only) | atributlar |

## User’lar va guruhlar

| | |
|---|---|
| `useradd -m -s /bin/bash -G sudo -e 2026-12-31 u`, `usermod -aG g u`, `usermod -L/-U`, `userdel -r u` | user’lar |
| `passwd u`, `chage -l u`, `chage -M 90 -W 7 u`, `chage -E date u` | parollar, muddat |
| `groupadd g`, `groupmod -n new old`, `groupdel g`, `gpasswd -a u g`, `gpasswd -d u g`, `groups u`, `id u` | guruhlar |
| `/etc/passwd` `/etc/shadow` `/etc/group` `/etc/gshadow` `/etc/login.defs` `/etc/skel` `/etc/default/useradd` | fayllar |
| `visudo`, `/etc/sudoers.d/`, `u ALL=(ALL) NOPASSWD: /usr/bin/systemctl`, `sudo -l`, `sudo -i`, `su - u` | imtiyoz |
| `ulimit -a`, `/etc/security/limits.conf` (`u hard nproc 100`) | limitlar |
| `/etc/profile`, `/etc/profile.d/*.sh`, `/etc/environment`, `~/.bashrc`, `~/.profile` | muhit |

## Jarayonlar va service’lar

| | |
|---|---|
| `ps aux`, `ps -ef --forest`, `top`/`htop`, `pgrep -a x`, `pidof x` | ko’rish |
| `kill -15 pid`, `kill -9`, `killall x`, `pkill -u u`, `kill -l` | signal yuborish |
| `nice -n 10 cmd`, `renice -n 5 -p pid` | ustuvorlik |
| `cmd &`, `jobs`, `fg %1`, `bg`, `Ctrl-Z`, `nohup cmd &`, `disown` | job’lar |
| `systemctl start/stop/restart/reload/status/enable/disable/mask/unmask u`, `enable --now`, `is-active`, `is-enabled` | unit’lar |
| `systemctl list-units --type=service --state=failed`, `list-unit-files`, `cat u`, `edit u`, `daemon-reload`, `show u -p X` | tekshirish |
| `/etc/systemd/system/x.service`: `[Unit] Description After=` `[Service] ExecStart= Restart=on-failure User=` `[Install] WantedBy=multi-user.target` | unit yozish |
| `systemctl get-default`, `set-default multi-user.target`, `isolate rescue.target`, `reboot`, `poweroff`, `shutdown -h +5 "msg"`, `shutdown -c` | target’lar, quvvat |
| `journalctl -u x -f`, `-b`, `-p err`, `--since "1 hour ago"`, `-k`, `--disk-usage`, `/var/log/syslog` `auth.log`, `logrotate` | loglar |
| `crontab -e/-l/-r`, `crontab -u u -e`, `/etc/crontab`, `/etc/cron.d/`, `*/5 * * * * cmd`, `at now +1 hour`, `atq`, `atrm`, `systemctl list-timers` | rejalashtirish |
| `apt update; apt install/remove/purge/search/show x; apt list --installed; dpkg -l; dpkg -S /path; dpkg -i f.deb` | Debian paketlari |
| `dnf install/remove/search/info/provides x; rpm -qa; rpm -qf /path; rpm -ql x` | RPM paketlari |
| `/etc/apt/sources.list(.d)`, `apt-key`/`/etc/apt/keyrings`, `/etc/yum.repos.d/*.repo` | repozitoriylar |
| `./configure && make && sudo make install` (after `build-essential`) | manbadan |
| `sysctl -a`, `sysctl -w net.ipv4.ip_forward=1`, `/etc/sysctl.d/99-x.conf`, `sysctl -p` | kernel parametrlari |
| `getenforce`, `setenforce 0/1`, `/etc/selinux/config`, `ls -Z`, `ps -Z`, `chcon`, `restorecon -Rv`, `semanage fcontext -a -t httpd_sys_content_t "/web(/.*)?"`, `semanage port -a -t http_port_t -p tcp 8081`, `getsebool -a`, `setsebool -P x on`, `ausearch -m avc` | SELinux |
| `podman/docker run -d --name x -p 8080:80 -v /h:/c img`, `ps -a`, `logs`, `exec -it x sh`, `stop`, `rm`, `images`, `pull`, `build -t` | konteynerlar |
| `virsh list --all`, `start/shutdown/destroy/undefine vm`, `console vm`, `virt-install ...`, `virsh dominfo` | VM’lar |

## Networking

| | |
|---|---|
| `ip a`, `ip r`, `ip -6 r`, `ip link set dev eth0 up`, `ip a add 10.0.0.5/24 dev eth0`, `ip r add default via 10.0.0.1` | hozir (doimiy emas) |
| `nmcli con show`, `nmcli con mod eth0 ipv4.addresses 10.0.0.5/24 ipv4.gateway 10.0.0.1 ipv4.dns 1.1.1.1 ipv4.method manual`, `nmcli con up eth0` | doimiy (NM) |
| `/etc/netplan/*.yaml`, `netplan apply`, `netplan try` | doimiy (Ubuntu netplan) |
| `hostnamectl set-hostname x`, `/etc/hosts`, `/etc/resolv.conf`, `resolvectl status`, `getent hosts x`, `dig`/`host`/`nslookup` | nomlar |
| `ss -tulpn`, `ss -s`, `ping`, `traceroute`, `nc -zv h p`, `curl -I` | tekshirish |
| `nmcli con add type bridge ifname br0`, `... type bridge-slave ifname eth1 master br0`; `type bond ifname bond0 mode active-backup`, `type bond-slave` | bridge, bond |
| `firewall-cmd --list-all`, `--add-service=http --permanent`, `--add-port=8080/tcp`, `--zone=`, `--reload`, `--add-masquerade`, `--add-forward-port=port=80:proto=tcp:toport=8080`, `--add-rich-rule` | firewalld |
| `ufw status`, `ufw allow 22/tcp`, `ufw deny from 10.0.0.0/8`, `ufw enable` | ufw |
| `nft list ruleset`, `nft add rule inet filter input tcp dport 22 accept`, `/etc/nftables.conf`; `iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080` | nftables/iptables |
| nginx: `proxy_pass http://backend;`, `upstream backend { server a:8080; server b:8080; }` | proxy, LB |
| `timedatectl`, `timedatectl set-timezone Europe/Berlin`, `set-ntp true`, `chronyc sources`, `/etc/chrony/chrony.conf` | vaqt |
| `/etc/ssh/sshd_config` (`PermitRootLogin no`, `PasswordAuthentication no`, `Port`), `systemctl reload sshd`, `ssh-keygen -t ed25519`, `ssh-copy-id u@h`, `~/.ssh/config`, `ssh -L 8080:localhost:80 h`, `-R`, `-D` | SSH |

## Storage

| | |
|---|---|
| `lsblk -f`, `blkid`, `fdisk -l`, `fdisk /dev/sdb` (n, p, t, w), `parted /dev/sdb mklabel gpt mkpart primary ext4 0% 100%`, `partprobe` | partition’lar |
| `mkfs.ext4 -L data /dev/sdb1`, `mkfs.xfs`, `tune2fs -L`, `xfs_admin -L`, `e2label`, `fsck`, `xfs_repair` | fayl tizimlari |
| `mkswap /dev/sdb2`, `swapon`, `swapoff`, `fallocate -l 1G /swap; chmod 600; mkswap; swapon`, `swapon --show`, `free -h` | swap |
| `/etc/fstab`: `UUID=... /mnt/data ext4 defaults,noexec 0 2`; `mount -a`; `findmnt`; `mount -o remount,ro /mnt/data`; `umount` | mount’lar |
| `pvcreate /dev/sdb1`, `vgcreate vg0 /dev/sdb1`, `lvcreate -L 2G -n data vg0`, `lvextend -L +1G -r /dev/vg0/data`, `lvreduce`, `vgextend`, `pvs vgs lvs`, `lvdisplay` | LVM |
| `/etc/exports` (`/srv/nfs 10.0.0.0/24(rw,sync,no_subtree_check)`), `exportfs -arv`, `showmount -e h`, `mount -t nfs h:/srv/nfs /mnt` | NFS |
| `nbd-server`, `/etc/nbd-server/config`, `modprobe nbd`, `nbd-client h 10809 /dev/nbd0` | NBD |
| `iostat -xz 1`, `iotop`, `vmstat 1`, `df -h`, `du -sh *`, `df -i` | unumdorlik, joy |

:::tip
Bu sahifani yodlashga urinmang. Undan foydalaning. Dars biror buyruqni
tanishtirsa, uning satrini shu yerdan toping; mock topshirig’i sizni
to’xtatib qo’ysa, o’sha sohaning blokini ko’zdan kechiring. 13-haftaga
borib, siz ellik marta ishlatgan satrlar - aynan imtihonning o’zi.
:::

## O’zingizni tekshiring

1. Orqaga qaramasdan: home direktoriyasi, bash shell’i va tugash sanasi
   bilan user qo’shadigan buyruq.
2. ext4 fayl tizimini UUID bo’yicha `/mnt/data`’ga `noexec` bilan mount
   qiladigan fstab satri.
3. TCP 80 ni 8080 ga yo’naltiradigan va uni doimiy qiladigan firewalld
   buyrug’i.
