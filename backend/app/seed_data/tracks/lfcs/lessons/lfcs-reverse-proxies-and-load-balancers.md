## What a reverse proxy does

A **reverse proxy** sits in front of one or more application servers: it
terminates the client connection, then makes its own connection to a
backend and returns the answer. The client never talks to the backend.

```
 client ──▶ nginx :443 (TLS)  ──▶  app :8080
                              ──▶  app :8081     ← the same proxy, several backends = load balancer
```

Why bother: one public address and port for many services, TLS in one
place, static files served without waking the application, health checks
and failover, rate limiting, and a place to add headers and caching.

## nginx as a reverse proxy

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
        alias /var/www/app/static/;        # served directly, never reaches the app
        expires 7d;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/app.conf /etc/nginx/sites-enabled/    # Debian only
sudo nginx -t                       # ALWAYS test before reloading
sudo systemctl reload nginx
curl -I http://app.example.com
```

The four `proxy_set_header` lines matter: without them the backend sees
nginx's address as the client and nginx's name as the host, so redirects,
logs and rate limits are all wrong.

## Load balancing across backends

```nginx
upstream app_backend {
    least_conn;                                  # or ip_hash, or default round-robin
    server 10.0.0.11:8080 max_fails=3 fail_timeout=30s;
    server 10.0.0.12:8080 max_fails=3 fail_timeout=30s;
    server 10.0.0.13:8080 backup;                # only used when the others are down
    keepalive 32;
}

server {
    listen 80;
    server_name app.example.com;
    location / {
        proxy_pass http://app_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";          # needed for keepalive to the upstream
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_next_upstream error timeout http_502 http_503;
    }
}
```

| Method | Sends a request to |
|---|---|
| round-robin (default) | each server in turn |
| `least_conn` | the server with the fewest active connections |
| `ip_hash` | a server chosen by client IP - **sticky sessions** |
| `hash $request_uri consistent` | a server chosen by URL - useful for caches |
| `weight=3` | proportionally more traffic to a bigger server |

Passive health checks come from `max_fails`/`fail_timeout`: after N
failures a backend is skipped for a while. (Active health checks are an
nginx Plus feature; HAProxy does them in the free version.)

## TLS termination

```nginx
server {
    listen 443 ssl http2;
    server_name app.example.com;

    ssl_certificate     /etc/ssl/certs/app.crt;      # certificate + intermediates
    ssl_certificate_key /etc/ssl/private/app.key;    # chmod 600
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    location / { proxy_pass http://app_backend; proxy_set_header Host $host; }
}
server {
    listen 80;
    server_name app.example.com;
    return 301 https://$host$request_uri;            # redirect plain HTTP
}
```

```bash
sudo certbot --nginx -d app.example.com              # Let's Encrypt: obtains and wires it up
sudo certbot renew --dry-run
openssl s_client -connect app.example.com:443 </dev/null | openssl x509 -noout -dates
```

## Useful extras

```nginx
client_max_body_size 50m;                       # uploads
proxy_buffering on;
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
location /api/ { limit_req zone=api burst=20 nodelay; proxy_pass http://app_backend; }

# websockets
location /ws/ {
    proxy_pass http://app_backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## HAProxy, the alternative

```
# /etc/haproxy/haproxy.cfg
frontend web
    bind *:80
    default_backend app

backend app
    balance roundrobin
    option httpchk GET /health              # ACTIVE health checks
    server app1 10.0.0.11:8080 check
    server app2 10.0.0.12:8080 check
```

```bash
sudo haproxy -c -f /etc/haproxy/haproxy.cfg      # config check
sudo systemctl reload haproxy
```

HAProxy is the better dedicated load balancer (active checks, richer
balancing, a stats page); nginx wins when the same box also serves static
files and TLS.

## Verifying

```bash
sudo nginx -t && sudo systemctl reload nginx
curl -I http://app.example.com
for i in $(seq 6); do curl -s http://app.example.com/whoami; done    # see the backends alternate
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log
ss -tulpn | grep -E ':80|:443'
sudo systemctl stop app@10.0.0.11 ; curl -I http://app.example.com   # failover still answers
```

| Symptom | Cause |
|---|---|
| 502 Bad Gateway | backend down, wrong port, or SELinux `httpd_can_network_connect` off (week 7) |
| 504 Gateway Timeout | backend too slow - `proxy_read_timeout` |
| 413 Request Entity Too Large | `client_max_body_size` |
| backend logs show the proxy's IP | missing `X-Forwarded-For` / `X-Real-IP` headers |
| redirect loop | backend redirects to http while the proxy terminates https - send `X-Forwarded-Proto` |

:::exam-tip
Expect: "configure nginx so that requests to port 80 are forwarded to the
application on port 8080" - a `server` block with `proxy_pass`, `nginx -t`,
`systemctl reload nginx`, verified with `curl -I`. If the backend is on
another host, remember the firewall between them and, on RHEL, the SELinux
boolean.
:::

## Check yourself

1. What does a reverse proxy add in front of an application server?
2. Which four headers should be set on `proxy_pass`, and what breaks
   without them?
3. Which balancing method gives sticky sessions, and how does nginx notice
   a dead backend?
