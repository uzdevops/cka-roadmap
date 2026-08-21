## Reverse proxy nima qiladi

**Reverse proxy** bir yoki bir nechta ilova serveri oldida turadi: u
client ulanishini o’zida tugatadi, so’ng backend’ga o’zining ulanishini
ochadi va javobni qaytaradi. Client hech qachon backend bilan gaplashmaydi.

```
 client ──▶ nginx :443 (TLS)  ──▶  app :8080
                              ──▶  app :8081     ← o'sha proxy, bir nechta backend = load balancer
```

Nima uchun kerak: ko’p service uchun bitta ommaviy manzil va port, TLS
bitta joyda, ilovani bezovta qilmasdan statik fayllarni berish, health
check va failover, rate limiting hamda header qo’shish va caching uchun
joy.

## nginx reverse proxy sifatida

```bash
sudo apt install nginx
sudo systemctl enable --now nginx
```

```nginx
# /etc/nginx/sites-available/app.conf   (Debian; RHEL: /etc/nginx/conf.d/app.conf)
server {
    listen 80;
    server_name app.example.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    location /static/ {
        alias /var/www/app/static/;        # to'g'ridan-to'g'ri beriladi, ilovaga umuman yetib bormaydi
        expires 7d;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/app.conf /etc/nginx/sites-enabled/    # faqat Debian
sudo nginx -t                       # reload'dan OLDIN DOIMO tekshiring
sudo systemctl reload nginx
curl -I http://app.example.com
```

To’rtta `proxy_set_header` qatori muhim: ularsiz backend client sifatida
nginx’ning manzilini, host sifatida esa nginx’ning nomini ko’radi -
natijada redirect’lar, loglar va rate limit’lar hammasi noto’g’ri bo’ladi.

## Backend’lar orasida load balancing

```nginx
upstream app_backend {
    least_conn;                                  # yoki ip_hash, yoki sukut bo'yicha round-robin
    server 10.0.0.11:8080 max_fails=3 fail_timeout=30s;
    server 10.0.0.12:8080 max_fails=3 fail_timeout=30s;
    server 10.0.0.13:8080 backup;                # faqat qolganlari ishlamaganda ishlatiladi
    keepalive 32;
}

server {
    listen 80;
    server_name app.example.com;
    location / {
        proxy_pass http://app_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";          # upstream'ga keepalive uchun kerak
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_next_upstream error timeout http_502 http_503;
    }
}
```

| Usul | So’rovni qayerga yuboradi |
|---|---|
| round-robin (sukut bo’yicha) | navbat bilan har bir serverga |
| `least_conn` | faol ulanishlari eng kam bo’lgan serverga |
| `ip_hash` | client IP’si bo’yicha tanlangan serverga - **sticky sessiyalar** |
| `hash $request_uri consistent` | URL bo’yicha tanlangan serverga - cache’lar uchun foydali |
| `weight=3` | kattaroq serverga proporsional ravishda ko’proq trafik |

Passiv health check’lar `max_fails`/`fail_timeout`dan keladi: N marta
nosozlikdan keyin backend bir muddat chetlab o’tiladi. (Aktiv health
check’lar - nginx Plus imkoniyati; HAProxy ularni bepul versiyada ham
qiladi.)

## TLS termination

```nginx
server {
    listen 443 ssl http2;
    server_name app.example.com;

    ssl_certificate     /etc/ssl/certs/app.crt;      # sertifikat + oraliq sertifikatlar
    ssl_certificate_key /etc/ssl/private/app.key;    # chmod 600
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    location / { proxy_pass http://app_backend; proxy_set_header Host $host; }
}
server {
    listen 80;
    server_name app.example.com;
    return 301 https://$host$request_uri;            # oddiy HTTP'ni redirect qilish
}
```

```bash
sudo certbot --nginx -d app.example.com              # Let's Encrypt: oladi va ulab qo'yadi
sudo certbot renew --dry-run
openssl s_client -connect app.example.com:443 </dev/null | openssl x509 -noout -dates
```

## Foydali qo’shimchalar

```nginx
client_max_body_size 50m;                       # yuklamalar
proxy_buffering on;
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
location /api/ { limit_req zone=api burst=20 nodelay; proxy_pass http://app_backend; }

# websocket'lar
location /ws/ {
    proxy_pass http://app_backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## HAProxy, muqobil variant

```
# /etc/haproxy/haproxy.cfg
frontend web
    bind *:80
    default_backend app

backend app
    balance roundrobin
    option httpchk GET /health              # AKTIV health check'lar
    server app1 10.0.0.11:8080 check
    server app2 10.0.0.12:8080 check
```

```bash
sudo haproxy -c -f /etc/haproxy/haproxy.cfg      # config'ni tekshirish
sudo systemctl reload haproxy
```

HAProxy - yaxshiroq maxsus load balancer (aktiv check’lar, boyroq
balanslash, statistika sahifasi); nginx esa o’sha mashina bir vaqtda
statik fayllar va TLS bilan ham shug’ullanganda yutadi.

## Tekshirish

```bash
sudo nginx -t && sudo systemctl reload nginx
curl -I http://app.example.com
for i in $(seq 6); do curl -s http://app.example.com/whoami; done    # backend'lar almashayotganini ko'ring
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log
ss -tulpn | grep -E ':80|:443'
sudo systemctl stop app@10.0.0.11 ; curl -I http://app.example.com   # failover baribir javob beradi
```

| Alomat | Sababi |
|---|---|
| 502 Bad Gateway | backend ishlamayapti, port noto’g’ri, yoki SELinux’da `httpd_can_network_connect` o’chiq (7-hafta) |
| 504 Gateway Timeout | backend juda sekin - `proxy_read_timeout` |
| 413 Request Entity Too Large | `client_max_body_size` |
| backend loglarida proxy’ning IP’si ko’rinadi | `X-Forwarded-For` / `X-Real-IP` header’lari yo’q |
| redirect halqasi | proxy https’ni tugatayotgan bo’lsa-da, backend http’ga redirect qiladi - `X-Forwarded-Proto` yuboring |

:::exam-tip
Kutiladigan topshiriq: "nginx’ni shunday sozlangki, 80-portga kelgan
so’rovlar 8080-portdagi ilovaga uzatilsin" - `proxy_pass` bo’lgan `server`
bloki, `nginx -t`, `systemctl reload nginx` va `curl -I` bilan tekshirish.
Agar backend boshqa host’da bo’lsa, ular orasidagi firewall’ni va RHEL’da
SELinux boolean’ini esdan chiqarmang.
:::

## O’zingizni tekshiring

1. Reverse proxy ilova serveri oldida nima qo’shadi?
2. `proxy_pass` bilan qaysi to’rtta header o’rnatilishi kerak va ularsiz
   nima buziladi?
3. Qaysi balanslash usuli sticky sessiya beradi va nginx ishlamayotgan
   backend’ni qanday sezadi?
