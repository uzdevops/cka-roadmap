## Manzillar o’rniga nomlar

```bash
ping 192.168.1.11      # ishlaydi, lekin manzillarni hech kim yodda tutmaydi
ping db                # "db" qandaydir yo'l bilan 192.168.1.11 ga aylanishi kerak
```

Linux host ikki joyga qaraydi, tartibni esa `/etc/nsswitch.conf` belgilaydi
(`hosts: files dns` - avval fayllar, keyin DNS).

## /etc/hosts

```bash
cat >> /etc/hosts <<EOF
192.168.1.11   db
192.168.1.12   web
EOF
ping db            # lokal aniqlandi, tarmoqdan hech nima so'ralmadi
```

Har bir host o’z faylini yuritadi. Uchta mashinaga yaraydi; uch yuztasi
uchun - kabus. Yechim - markaziy server.

## DNS server va /etc/resolv.conf

```bash
cat /etc/resolv.conf
# nameserver 192.168.1.100
# search mycompany.com prod.mycompany.com
# options ndots:5
```

- `nameserver` - kimdan so’rash kerakligi (uchtagacha; tartib bo’yicha
  sinaladi).
- `search` - nomda nuqta bo’lmaganda qo’shiladigan qo’shimchalar: `ping web`
  avval `web.mycompany.com`, keyin `web.prod.mycompany.com`’ni sinaydi.
- `ndots` - nuqtalari shundan kam bo’lgan nom **avval** search
  qo’shimchalari bilan sinaladi; ko’p bo’lsa, avval o’zi bor holicha.

Zamonaviy Ubuntu’da `/etc/resolv.conf`’ni `systemd-resolved` generatsiya
qiladi (nameserver `127.0.0.53`, lokal stub) - haqiqiy upstream’larni
`resolvectl status` ko’rsatadi. **Pod** ichida bu faylni kubelet yozadi va
aynan u har qanday Pod’dan `curl api`’ni ishlatadi; bu - Kubernetes’dagi
DNS darsining mavzusi.

## Tanishingiz kerak bo’lgan record turlari

| Turi | Nimani bog’laydi | Misol |
|---|---|---|
| A | nom → IPv4 | `web.example.com → 203.0.113.10` |
| AAAA | nom → IPv6 | |
| CNAME | nom → boshqa nom | `www → web.example.com` |
| SRV | xizmat → host + port | CoreDNS `_http._tcp.svc` so’rovlarida ishlatadi |
| PTR | IP → nom (teskari) | `10.113.0.203.in-addr.arpa → web` |

Kubernetes Service’lari - A record’lar (nomlangan portlar uchun SRV ham);
headless Service’lar esa har bir Pod uchun bittadan bir nechta A record
qaytaradi.

## Vositalar

```bash
nslookup web.example.com               # oddiy: resolv.conf dagi nameserver'dan so'raydi
dig web.example.com                    # batafsil: har bir bo'lim, javob bergan server, TTL
dig @10.96.0.10 api.payroll.svc.cluster.local   # ANIQ bir serverdan so'rash (CoreDNS ClusterIP'si)
host web.example.com
getent hosts web                       # libc qanday aniqlasa shunday: /etc/hosts KEYIN DNS
```

`nslookup` va `dig` **faqat** DNS’ga murojaat qiladi - ular `/etc/hosts`’ni
e’tiborsiz qoldiradi. `ping`, `curl`, `getent` esa libc orqali o’tadi va
hosts faylini hamda search ro’yxatini hisobga oladi. "ping ishlaydi, dig
ishlamaydi" yoki aksincha bo’lganda, tushuntirish - aynan shu farq.

:::exam-tip
Pod ichida kerakli vosita ko’pincha bo’lmaydi. `busybox`’da `nslookup` bor;
`kubectl run -it --rm t --image=busybox:1.36 -- nslookup kubernetes` -
universal DNS testi. To’liq `dig` uchun
`registry.k8s.io/e2e-test-images/jessie-dnsutils` kabi image’dan foydalaning.
:::

## Muvaffaqiyatsiz so’rovni o’qish

| Chiqish | Ma’nosi |
|---|---|
| `;; connection timed out; no servers could be reached` | resolv.conf dagi nameserver’ga yetib bo’lmayapti (CoreDNS o’chgan, NetworkPolicy 53 ni to’sgan) |
| `** server can't find web: NXDOMAIN` | server javob berdi: bunday nom yo’q (xato yozuv, noto’g’ri namespace, yetishmayotgan search qo’shimchasi) |
| noto’g’ri manzilga aylandi | eskirgan `/etc/hosts` yozuvi yoki siz kutmagan CNAME |

Timed out = **ulanish** muammosi; NXDOMAIN = **nom** muammosi. Bu ikkisini
ajratib olsangiz, DNS’ni tekshirishning yarmi tayyor.

## O’zingizni tekshiring

1. `ping web` `/etc/hosts` va DNS’ga qanday tartibda murojaat qiladi va bu
   tartibni qaysi fayl belgilaydi?
2. `resolv.conf`’dagi `search` qatori `api` nomiga nima qiladi?
3. Pod ichidan `nslookup` "connection timed out" deyapti. Nom noto’g’rimi
   yoki gap boshqa narsadami?
