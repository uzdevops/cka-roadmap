## The reference card

Keep this lesson open for the whole track. It is deliberately terse: the
command, the flags that matter, one example. Each row is explained in
full in its own lesson; this is the place you come back to.

## Getting help

| | |
|---|---|
| `man cmd`, `man 5 fstab`, `man -k keyword` (`apropos`) | manual by section; search titles |
| `cmd --help`, `help cd` (shell builtins) | quick syntax |
| `info cmd`, `/usr/share/doc/pkg/` | longer docs, examples |
| `type cmd`, `which cmd`, `whereis cmd` | what a name resolves to |

## Files

| | |
|---|---|
| `ls -la`, `ls -li` (inodes), `ls -lZ` (SELinux), `stat f` | look |
| `cp -r`, `cp -a` (preserve), `mv`, `rm -rf`, `mkdir -p`, `touch`, `rmdir` | create/move/remove |
| `ln target hard`, `ln -s target soft`, `readlink -f` | links |
| `find / -name x -type f -size +1M -mtime -7 -perm -4000 -user u -exec cmd {} \;` | search |
| `locate x` (`updatedb`) | indexed search |
| `cat`, `head -n`, `tail -n`/`-f`, `less`, `wc -l` | read |
| `sort -n/-r/-k2`, `uniq -c`, `cut -d: -f1`, `tr a-z A-Z`, `paste`, `diff -u a b` | transform |
| `sed 's/a/b/g' f`, `sed -i`, `sed -n '3,5p'`, `awk -F: '{print $1}'` | edit streams |
| `grep -i -n -r -v -c -E -w -o 'pat' f` | search content |
| `tar czf a.tgz dir`, `tar xzf a.tgz -C /dst`, `tar tf`, `-j` bz2, `-J` xz | archive |
| `gzip/gunzip`, `bzip2`, `xz`, `zip -r`/`unzip` | compress |
| `rsync -av src/ user@host:/dst/`, `scp -r f host:/dst` | copy remote |
| `>` `>>` `2>` `2>&1` `&>` `<` `<<EOF` `\|` `\| tee f` | redirection |

## Permissions

| | |
|---|---|
| `chmod u+x f`, `chmod 644 f`, `chmod -R g+w d`, `chmod 4755` (SUID) `2775` (SGID) `1777` (sticky) | mode |
| `chown user:group f`, `chgrp g f`, `umask`, `umask 027` | owner, defaults |
| `getfacl f`, `setfacl -m u:bob:rw f`, `setfacl -d -m g:dev:rwx d`, `setfacl -x u:bob f`, `setfacl -b f` | ACLs |
| `lsattr f`, `chattr +i f` (immutable), `chattr +a` (append-only) | attributes |

## Users and groups

| | |
|---|---|
| `useradd -m -s /bin/bash -G sudo -e 2026-12-31 u`, `usermod -aG g u`, `usermod -L/-U`, `userdel -r u` | users |
| `passwd u`, `chage -l u`, `chage -M 90 -W 7 u`, `chage -E date u` | passwords, ageing |
| `groupadd g`, `groupmod -n new old`, `groupdel g`, `gpasswd -a u g`, `gpasswd -d u g`, `groups u`, `id u` | groups |
| `/etc/passwd` `/etc/shadow` `/etc/group` `/etc/gshadow` `/etc/login.defs` `/etc/skel` `/etc/default/useradd` | files |
| `visudo`, `/etc/sudoers.d/`, `u ALL=(ALL) NOPASSWD: /usr/bin/systemctl`, `sudo -l`, `sudo -i`, `su - u` | privilege |
| `ulimit -a`, `/etc/security/limits.conf` (`u hard nproc 100`) | limits |
| `/etc/profile`, `/etc/profile.d/*.sh`, `/etc/environment`, `~/.bashrc`, `~/.profile` | environment |

## Processes and services

| | |
|---|---|
| `ps aux`, `ps -ef --forest`, `top`/`htop`, `pgrep -a x`, `pidof x` | see |
| `kill -15 pid`, `kill -9`, `killall x`, `pkill -u u`, `kill -l` | signal |
| `nice -n 10 cmd`, `renice -n 5 -p pid` | priority |
| `cmd &`, `jobs`, `fg %1`, `bg`, `Ctrl-Z`, `nohup cmd &`, `disown` | jobs |
| `systemctl start/stop/restart/reload/status/enable/disable/mask/unmask u`, `enable --now`, `is-active`, `is-enabled` | units |
| `systemctl list-units --type=service --state=failed`, `list-unit-files`, `cat u`, `edit u`, `daemon-reload`, `show u -p X` | inspect |
| `/etc/systemd/system/x.service`: `[Unit] Description After=` `[Service] ExecStart= Restart=on-failure User=` `[Install] WantedBy=multi-user.target` | write one |
| `systemctl get-default`, `set-default multi-user.target`, `isolate rescue.target`, `reboot`, `poweroff`, `shutdown -h +5 "msg"`, `shutdown -c` | targets, power |
| `journalctl -u x -f`, `-b`, `-p err`, `--since "1 hour ago"`, `-k`, `--disk-usage`, `/var/log/syslog` `auth.log`, `logrotate` | logs |
| `crontab -e/-l/-r`, `crontab -u u -e`, `/etc/crontab`, `/etc/cron.d/`, `*/5 * * * * cmd`, `at now +1 hour`, `atq`, `atrm`, `systemctl list-timers` | schedule |
| `apt update; apt install/remove/purge/search/show x; apt list --installed; dpkg -l; dpkg -S /path; dpkg -i f.deb` | Debian pkgs |
| `dnf install/remove/search/info/provides x; rpm -qa; rpm -qf /path; rpm -ql x` | RPM pkgs |
| `/etc/apt/sources.list(.d)`, `apt-key`/`/etc/apt/keyrings`, `/etc/yum.repos.d/*.repo` | repos |
| `./configure && make && sudo make install` (after `build-essential`) | source |
| `sysctl -a`, `sysctl -w net.ipv4.ip_forward=1`, `/etc/sysctl.d/99-x.conf`, `sysctl -p` | kernel params |
| `getenforce`, `setenforce 0/1`, `/etc/selinux/config`, `ls -Z`, `ps -Z`, `chcon`, `restorecon -Rv`, `semanage fcontext -a -t httpd_sys_content_t "/web(/.*)?"`, `semanage port -a -t http_port_t -p tcp 8081`, `getsebool -a`, `setsebool -P x on`, `ausearch -m avc` | SELinux |
| `podman/docker run -d --name x -p 8080:80 -v /h:/c img`, `ps -a`, `logs`, `exec -it x sh`, `stop`, `rm`, `images`, `pull`, `build -t` | containers |
| `virsh list --all`, `start/shutdown/destroy/undefine vm`, `console vm`, `virt-install ...`, `virsh dominfo` | VMs |

## Networking

| | |
|---|---|
| `ip a`, `ip r`, `ip -6 r`, `ip link set dev eth0 up`, `ip a add 10.0.0.5/24 dev eth0`, `ip r add default via 10.0.0.1` | now (not persistent) |
| `nmcli con show`, `nmcli con mod eth0 ipv4.addresses 10.0.0.5/24 ipv4.gateway 10.0.0.1 ipv4.dns 1.1.1.1 ipv4.method manual`, `nmcli con up eth0` | persistent (NM) |
| `/etc/netplan/*.yaml`, `netplan apply`, `netplan try` | persistent (Ubuntu netplan) |
| `hostnamectl set-hostname x`, `/etc/hosts`, `/etc/resolv.conf`, `resolvectl status`, `getent hosts x`, `dig`/`host`/`nslookup` | names |
| `ss -tulpn`, `ss -s`, `ping`, `traceroute`, `nc -zv h p`, `curl -I` | check |
| `nmcli con add type bridge ifname br0`, `... type bridge-slave ifname eth1 master br0`; `type bond ifname bond0 mode active-backup`, `type bond-slave` | bridge, bond |
| `firewall-cmd --list-all`, `--add-service=http --permanent`, `--add-port=8080/tcp`, `--zone=`, `--reload`, `--add-masquerade`, `--add-forward-port=port=80:proto=tcp:toport=8080`, `--add-rich-rule` | firewalld |
| `ufw status`, `ufw allow 22/tcp`, `ufw deny from 10.0.0.0/8`, `ufw enable` | ufw |
| `nft list ruleset`, `nft add rule inet filter input tcp dport 22 accept`, `/etc/nftables.conf`; `iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080` | nftables/iptables |
| nginx: `proxy_pass http://backend;`, `upstream backend { server a:8080; server b:8080; }` | proxy, LB |
| `timedatectl`, `timedatectl set-timezone Europe/Berlin`, `set-ntp true`, `chronyc sources`, `/etc/chrony/chrony.conf` | time |
| `/etc/ssh/sshd_config` (`PermitRootLogin no`, `PasswordAuthentication no`, `Port`), `systemctl reload sshd`, `ssh-keygen -t ed25519`, `ssh-copy-id u@h`, `~/.ssh/config`, `ssh -L 8080:localhost:80 h`, `-R`, `-D` | SSH |

## Storage

| | |
|---|---|
| `lsblk -f`, `blkid`, `fdisk -l`, `fdisk /dev/sdb` (n, p, t, w), `parted /dev/sdb mklabel gpt mkpart primary ext4 0% 100%`, `partprobe` | partitions |
| `mkfs.ext4 -L data /dev/sdb1`, `mkfs.xfs`, `tune2fs -L`, `xfs_admin -L`, `e2label`, `fsck`, `xfs_repair` | filesystems |
| `mkswap /dev/sdb2`, `swapon`, `swapoff`, `fallocate -l 1G /swap; chmod 600; mkswap; swapon`, `swapon --show`, `free -h` | swap |
| `/etc/fstab`: `UUID=... /mnt/data ext4 defaults,noexec 0 2`; `mount -a`; `findmnt`; `mount -o remount,ro /mnt/data`; `umount` | mounts |
| `pvcreate /dev/sdb1`, `vgcreate vg0 /dev/sdb1`, `lvcreate -L 2G -n data vg0`, `lvextend -L +1G -r /dev/vg0/data`, `lvreduce`, `vgextend`, `pvs vgs lvs`, `lvdisplay` | LVM |
| `/etc/exports` (`/srv/nfs 10.0.0.0/24(rw,sync,no_subtree_check)`), `exportfs -arv`, `showmount -e h`, `mount -t nfs h:/srv/nfs /mnt` | NFS |
| `nbd-server`, `/etc/nbd-server/config`, `modprobe nbd`, `nbd-client h 10809 /dev/nbd0` | NBD |
| `iostat -xz 1`, `iotop`, `vmstat 1`, `df -h`, `du -sh *`, `df -i` | performance, space |

:::tip
Do not try to learn this page. Use it. When a lesson introduces a command,
find its row here; when a mock task stumps you, scan the domain's block.
By week 13 the rows you have used fifty times are the exam.
:::

## Check yourself

1. Without looking back: the command to add a user with a home directory,
   bash shell, and an expiry date.
2. The fstab line that mounts an ext4 filesystem by UUID at `/mnt/data`
   with `noexec`.
3. The firewalld command that forwards TCP 80 to 8080 and makes it
   permanent.
