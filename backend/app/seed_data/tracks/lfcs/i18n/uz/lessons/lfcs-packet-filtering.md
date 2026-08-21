## Bitta filtrga uchta interfeys

Hamma narsaning ostida kernel’ning **netfilter**’i turadi. Uning ustida:

| Vosita | Qayerda | Izoh |
|---|---|---|
| **nftables** (`nft`) | zamonaviy standart | iptables’ni almashtiradi; IPv4/IPv6 uchun bitta framework |
| **firewalld** (`firewall-cmd`) | RHEL oilasi, Ubuntu’da ham | nftables ustidagi zone’lar va service’lar |
| **ufw** | Ubuntu’da sukut bo’yicha | nftables/iptables ustidagi oddiy rule’lar |
| **iptables** | eskirgan | hujjatlarda hali hamma joyda; endi odatda nftables ustidagi shim |

Ulardan **bittasini** ishlating. Bitta host’dagi ikkita menejer ruleset
uchun bir-biri bilan urishadi.

## ufw: Ubuntu usuli

```bash
sudo ufw status verbose
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp                       # yoki: sudo ufw allow OpenSSH
sudo ufw allow 80,443/tcp
sudo ufw allow from 192.168.1.0/24 to any port 3306 proto tcp
sudo ufw allow in on eth1 to any port 53
sudo ufw deny from 10.20.30.40
sudo ufw limit 22/tcp                        # takrorlanuvchi ulanishlarni rate-limit qilish (brute force)
sudo ufw delete allow 80/tcp
sudo ufw status numbered && sudo ufw delete 3
sudo ufw enable                              # reboot'dan keyin ham saqlanadi
sudo ufw disable
sudo ufw reset
sudo ufw app list; sudo ufw app info OpenSSH
sudo ufw logging on
```

:::warning
`default deny incoming` bilan va **hech qanday SSH rule’isiz**
`sudo ufw enable` sessiyangizni darhol tugatadi. Yoqishdan **oldin** doimo
`sudo ufw allow 22/tcp` (yoki `allow OpenSSH`) qiling - har qanday firewall
vositasida SSH rule’i birinchi bo’ladi.
:::

## firewalld: zone’lar va service’lar

**zone** - bu interfeyslarga yoki manbalarga qo’llanadigan siyosat:
`public`, `internal`, `trusted`, `dmz`, `drop`, `work`, `home`.

```bash
sudo systemctl enable --now firewalld
firewall-cmd --state
firewall-cmd --get-active-zones
firewall-cmd --get-default-zone
firewall-cmd --list-all                                   # sukut bo'yicha zone'ning butun siyosati
firewall-cmd --zone=public --list-all
firewall-cmd --get-services                                # u biladigan nomlangan service'lar
```

Ikki bosqichli qoida: **runtime**’ni o’zgartiring, keyin uni **doimiy**
qiling - yoki `--permanent` va `--reload` qo’shing.

```bash
sudo firewall-cmd --add-service=http                       # faqat runtime, reload'da yo'qoladi
sudo firewall-cmd --permanent --add-service=http           # faqat config, hali faol emas
sudo firewall-cmd --reload                                 # permanent config'ni faollashtirish
sudo firewall-cmd --runtime-to-permanent                   # hozir faol bo'lganini saqlash
```

```bash
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --permanent --remove-service=cockpit
sudo firewall-cmd --permanent --zone=internal --add-source=192.168.1.0/24
sudo firewall-cmd --permanent --zone=internal --add-service=ssh
sudo firewall-cmd --permanent --change-interface=eth1 --zone=internal
sudo firewall-cmd --permanent --set-default-zone=public
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="10.0.0.0/8" service name="mysql" accept'
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="10.20.30.40" drop'
sudo firewall-cmd --reload
firewall-cmd --list-all --zone=internal
```

Rich rule’lar oddiy `--add-service` shakli ifodalay olmaydigan manbalar,
logging, rate limit va reject’larni qo’shadi.

## Bevosita nftables

```bash
sudo nft list ruleset
sudo nft list tables
sudo nft add table inet filter
sudo nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
sudo nft add rule inet filter input ct state established,related accept
sudo nft add rule inet filter input iif lo accept
sudo nft add rule inet filter input tcp dport 22 accept
sudo nft add rule inet filter input tcp dport { 80, 443 } accept
sudo nft add rule inet filter input ip saddr 192.168.1.0/24 tcp dport 3306 accept
sudo nft add rule inet filter input icmp type echo-request limit rate 5/second accept
sudo nft -a list ruleset                       # handle'lar bilan; delete uchun kerak
sudo nft delete rule inet filter input handle 7
```

Saqlash:

```bash
sudo nft list ruleset | sudo tee /etc/nftables.conf
sudo systemctl enable --now nftables
```

Minimal `/etc/nftables.conf`:

```
#!/usr/sbin/nft -f
flush ruleset
table inet filter {
  chain input {
    type filter hook input priority 0; policy drop;
    ct state established,related accept
    iif lo accept
    ct state invalid drop
    tcp dport 22 accept
    tcp dport { 80, 443 } accept
    icmp type echo-request accept
  }
  chain forward { type filter hook forward priority 0; policy drop; }
  chain output  { type filter hook output  priority 0; policy accept; }
}
```

Tartib muhim: **avval established/related** (o’z trafigingizga javoblar
o’tishi uchun), ikkinchi bo’lib loopback, keyin aniq portlar va sukut
bo’yicha `drop` siyosati bilan.

## iptables, eski hujjatlarni o’qish uchun

```bash
sudo iptables -L -n -v --line-numbers
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -P INPUT DROP
sudo iptables -D INPUT 3
sudo iptables-save > /etc/iptables/rules.v4       # saqlash (iptables-persistent)
sudo iptables-restore < /etc/iptables/rules.v4
```

`INPUT`/`FORWARD`/`OUTPUT` chain’lari, `ACCEPT`/`DROP`/`REJECT` target’lari,
`filter`/`nat`/`mangle` table’lari - nftables meros qilib olgan lug’at.

## Rule’laringizni sinash

```bash
sudo ufw status numbered; sudo firewall-cmd --list-all; sudo nft list ruleset
ss -tulpn                                     # umuman nima tinglayapti
nc -zv <host> 22                              # BOSHQA mashinadan
nmap -Pn -p 22,80,443 <host>                  # agar mavjud bo'lsa
sudo journalctl -k | grep -i "UFW\|nft\|DROP" # loglangan drop'lar
sudo tcpdump -ni eth0 port 8080               # paket umuman yetib kelyaptimi?
```

Boshqa host’dan sinang: butun dunyoni bloklaydigan rule ham loopback’ni
o’tkazaveradi, shuning uchun `curl localhost` firewall haqida hech narsani
isbotlamaydi.

:::exam-tip
Imtihon mashinasi Ubuntu, shuning uchun `ufw` eng ehtimolli, lekin
firewalld ham maqsadlar ro’yxatida ochiq yozilgan - ikkala lug’atni ham
biling. Shakl bir xil: avval SSH’ga ruxsat bering, sukut bo’yicha siyosatni
o’rnating, topshiriqda aytilgan rule’larni qo’shing, uni doimiy qiling
(`ufw enable`, yoki `--permanent` + `--reload`) va `status`/`--list-all`
bilan tekshiring.
:::

## O’zingizni tekshiring

1. Uzoqdan turib default-deny firewall’ni yoqishdan oldin doimo nima
   qilishingiz kerak?
2. firewalld’da runtime va permanent o’zgarish orasidagi farq nima va
   qaysi ikki buyruq ularni bir-biriga bog’laydi?
3. Nega nftables input chain’i `ct state established,related`ni erta
   qabul qilishi kerak?
