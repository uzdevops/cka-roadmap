# Deploying behind nginx

Setup for **https://cka-prep.yatm.uz**: the compose stack listens on the
loopback interface only, and nginx on the same host terminates TLS and splits
traffic by path.

```
                    ┌─────────────── the server ───────────────┐
  browser ──443──►  │  nginx                                   │
                    │    /api/v1/, /docs  ──► 127.0.0.1:8000   │
                    │    everything else  ──► 127.0.0.1:3000   │
                    │                                          │
                    │  compose network "k8s":                  │
                    │    frontend ──► backend ──► db           │
                    └──────────────────────────────────────────┘
```

Everything the browser loads comes from one origin, so **CORS never applies**
and `NEXT_PUBLIC_API_URL` is just the site URL. This is the same shape as
[k8s/06-ingress.yaml](../k8s/06-ingress.yaml), for anyone moving to Kubernetes
later.

## 1. DNS

Point an `A` record for `cka-prep.yatm.uz` at the server's public IP, and
confirm it resolves before asking Let's Encrypt for anything:

```bash
dig +short cka-prep.yatm.uz
```

## 2. Configuration

```bash
git clone <repo> && cd <repo>
cp .env.production.example .env
```

Then edit `.env` and fill in the placeholders. The two that matter most:

```bash
openssl rand -base64 24   # -> POSTGRES_PASSWORD
openssl rand -hex 32      # -> SECRET_KEY
```

Also change `DEMO_STUDENT_PASSWORD` and `DEMO_ADMIN_PASSWORD` **before the
first start** — the defaults are published in this repo's README, and the admin
account can edit every lesson. The seeder matches users by email and skips ones
that already exist, so changing a password afterwards has no effect on an
account that was already created.

`POSTGRES_BIND`, `BACKEND_BIND` and `FRONTEND_BIND` are set to `127.0.0.1` in
the example. Leave them there. At the default `0.0.0.0` the database and the
unproxied API are reachable from the internet.

## 3. Start the stack

```bash
docker compose up -d --build
```

`--build` is not optional here: `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_SITE_URL`
are compiled into the client bundle at image build time. Changing them in `.env`
and only restarting leaves the old domain baked into the JavaScript.

Check it before involving nginx:

```bash
curl -s localhost:8000/healthz
curl -s localhost:3000/healthz
docker compose ps          # all three healthy
```

## 4. nginx

```bash
sudo apt install nginx
sudo cp deploy/nginx/cka-prep.yatm.uz.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/cka-prep.yatm.uz.conf /etc/nginx/sites-enabled/
sudo mkdir -p /var/www/certbot
```

The config references certificates that do not exist yet, so `nginx -t` fails
until step 5. If you would rather have it up first, comment out the whole
`listen 443` server block, reload, get the certificate, then put it back.

## 5. TLS

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d cka-prep.yatm.uz
sudo nginx -t && sudo systemctl reload nginx
```

Certbot installs a renewal timer. Confirm it works:

```bash
sudo certbot renew --dry-run
```

## 6. Firewall

Only 80, 443 and SSH should be open. The container ports are on the loopback
interface, but a firewall means a future `.env` mistake is not immediately fatal:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Updating

```bash
git pull
docker compose up -d --build
```

Migrations and the idempotent seeder run automatically on backend start, so new
lessons and new columns arrive with the image. The seeder never overwrites a
lesson that already has real content, nor a translation that is already filled
in — content edited through the admin panel survives a redeploy.

## Backups

`db` is the only stateful service. Everything else can be rebuilt from the repo.

```bash
docker compose exec -T db pg_dump -U cka cka_prep | gzip > cka-$(date +%F).sql.gz
```

Restore into an empty database:

```bash
gunzip -c cka-2026-08-17.sql.gz | docker compose exec -T db psql -U cka -d cka_prep
```

## Things worth knowing

**`/docs` is public.** The nginx config proxies `/docs`, `/redoc` and
`/openapi.json`. Nothing sensitive is exposed — the schemas are the same ones
the frontend uses, and every admin endpoint re-checks the role server-side — but
delete those three `location` blocks if you would rather not advertise the API.

**Do not widen `/api/v1/` to `/api/`.** Next.js owns `/api/preview`, which the
admin editor calls to render its Markdown preview. Routing all of `/api/` to the
backend gives that a 404.

**Rate limiting depends on the proxy headers.** uvicorn already starts with
`--proxy-headers --forwarded-allow-ips '*'`, and the nginx config sets
`X-Forwarded-For`. Drop either and slowapi counts every request in the cluster
against nginx's own IP, which throttles all of your users at once.

**One backend worker by default.** Set `UVICORN_WORKERS` if you need more; the
app is stateless apart from the database, so workers scale freely.
