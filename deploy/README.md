# Deploying behind nginx

Setup for **https://cka-prep.yatm.uz**: the compose stack listens on the
loopback interface only, and nginx on the same host terminates TLS and splits
traffic by path.

Two topologies, one routing table. Pick by where the certificate lives.

**A — TLS terminates on a separate host** (what 192.168.121.52 runs):

```
                  ┌── edge nginx ──┐      ┌─────────── app server ───────────┐
  browser ──443──►│ cert for       │─80──►│ nginx :80                        │
                  │ cka-prep…      │      │   /api/v1/, /docs ► 127.0.0.1:8000│
                  └────────────────┘      │   everything else ► 127.0.0.1:3000│
                                          │  compose net "k8s":              │
                                          │    frontend ► backend ► db       │
                                          └──────────────────────────────────┘
```

Use `cka-prep.yatm.uz.http-only.conf`. No certificate and no port 443 on the app
server, and **no HTTP→HTTPS redirect** — the edge already did that, and
redirecting again would bounce its request straight back out.

**B — this host terminates TLS itself:** use `cka-prep.yatm.uz.conf` and follow
step 5.

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

Then fill in the two secrets. Generate them in place:

```bash
sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -hex 24)|" .env
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$(openssl rand -hex 32)|" .env
```

Hex on purpose. The database password goes straight into the connection string
`postgresql+asyncpg://user:PASSWORD@db:5432/cka_prep`, so a `/`, `+`, `@` or `:`
from `openssl rand -base64` quietly produces a DSN that points somewhere else.
A `$` is worse still: Docker Compose expands it while reading `.env`.

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

Two configs ship here, and which one you start with depends on whether DNS
already points at this host:

| File | When |
| --- | --- |
| `cka-prep.yatm.uz.http-only.conf` | DNS not moved yet — HTTP only, no certificate needed |
| `cka-prep.yatm.uz.conf` | DNS resolves here and you have a certificate |

Both route identically, so switching is not a re-learn.

On a Debian/Ubuntu nginx with `sites-available`:

```bash
sudo cp deploy/nginx/cka-prep.yatm.uz.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/cka-prep.yatm.uz.conf /etc/nginx/sites-enabled/
```

On one that only includes `conf.d/*.conf` (the nginx.org packages, and what
192.168.121.52 runs), copy it in with a name that sorts **last**:

```bash
sudo cp deploy/nginx/cka-prep.yatm.uz.http-only.conf \
        /etc/nginx/conf.d/zz-cka-prep.yatm.uz.conf
```

That prefix is not cosmetic. `conf.d/*.conf` is included alphabetically and the
first server block on a listen address becomes the default for unmatched `Host`
headers — drop in a `c…`-named file and it silently takes over from
`default.conf`.

```bash
sudo mkdir -p /var/www/certbot
sudo nginx -t && sudo systemctl reload nginx
```

The TLS config references certificates, so `nginx -t` fails on it until step 5.

### What the edge proxy must send (topology A)

```nginx
location / {
    proxy_pass http://192.168.121.52:80;
    proxy_set_header Host              $host;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

All three matter, and the app config is built to cooperate with them:

- **`Host`** picks the right `server_name` here.
- **`X-Forwarded-For`** must *append*, not replace. Measured on this stack:
  uvicorn 0.34 reads the **leftmost** entry, so the real client IP survives both
  hops and the API's rate limiter throttles per user instead of per proxy.
- **`X-Forwarded-Proto`** is how the backend learns the request was HTTPS.
  Because `$scheme` on the app server is always `http`, the config maps the
  incoming value through instead of hardcoding it — otherwise every redirect
  FastAPI issues comes back as `http://`, and the browser takes an extra bounce
  through the edge to get corrected.

Verify from the app server, simulating the edge:

```bash
curl -sI -H 'Host: cka-prep.yatm.uz' -H 'X-Forwarded-Proto: https' \
     http://127.0.0.1/api/v1/auth/me/ | grep -i location
# location: https://cka-prep.yatm.uz/api/v1/auth/me   <- https, not http
```

If you change the nginx config, `systemctl reload` is asynchronous — sleep a
couple of seconds before testing or you will measure the old workers.

## 5. TLS (topology B only)

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

## Swarm instead of Compose

`docker compose up` is one way to run this on a server. The other is a
single-node Docker Swarm, which adds restart policies, rolling updates and
resource limits without introducing an orchestrator:

```bash
./install.sh                  # from the repository root
```

nginx does **not** change. It still runs on the host, still terminates TLS, and
still proxies to `127.0.0.1:8000` and `127.0.0.1:3000` - every config in this
directory works unmodified.

### The port difference, and why the firewall is not optional

Compose can bind a published port to one interface (`BACKEND_BIND=127.0.0.1`).
**Swarm cannot** - the long port syntax has no `host_ip` field, so a published
port lands on `0.0.0.0`. The stack file therefore uses:

```yaml
ports:
  - target: 8000
    published: 8000
    protocol: tcp
    mode: host
```

`mode: host` rather than the default ingress routing mesh, for two reasons:
nginx connects over the loopback interface and a mesh-published port is served
by Swarm's ingress network, which a loopback connection does not reach; and the
mesh adds a NAT hop for traffic that never leaves the node.

The consequence is that on a Swarm host, ports 8000 and 3000 are reachable from
the network. That means the raw API and the un-proxied frontend, bypassing nginx
and TLS. Close them:

```bash
# nftables
sudo nft add rule inet filter input iif != "lo" tcp dport 8000 drop
sudo nft add rule inet filter input iif != "lo" tcp dport 3000 drop

# or ufw
sudo ufw deny 8000/tcp
sudo ufw deny 3000/tcp
```

Verify from **another machine** - a check run on the host itself goes over
loopback and will always succeed:

```bash
nc -zv <host> 8000    # must be refused or time out
```

`install.sh` prints these commands and warns when the ports are open. It applies
them only with `--with-firewall`: changing a server's firewall without being
asked is a good way to lose the SSH session you are holding.

### Secrets

`SECRET_KEY` and `POSTGRES_PASSWORD` are Docker secrets under Swarm, mounted at
`/run/secrets/` rather than passed as environment variables - so they stay out
of `docker inspect` and out of every child process's environment. The backend
reads `SECRET_KEY_FILE` / `POSTGRES_PASSWORD_FILE` and falls back to the plain
variable, so the compose path is unaffected.

A Swarm secret is immutable. Rotating one means creating a new name and updating
the service; `install.sh` only ever creates a missing secret, and never replaces
a live one underneath a running stack.

### Single node

There is no registry, so images exist only on the machine that built them -
hence `--resolve-image never` on the deploy. A second node would need a registry
(or `docker save`/`docker load` onto each node) and the tags in
`docker-stack.yml` pointed at it.

## The Telegram bot

Optional. Without `TELEGRAM_BOT_TOKEN` the service logs why it is disabled and
exits 0 - which is why its restart policy is `on-failure` and not `any`: a
policy that restarts on ANY exit turns "switched off" into a restart loop.

Under Swarm the token is a Docker secret (`cka_telegram_token`), created by
install.sh from `.env`. A Swarm secret is immutable, so adding a token later is
a rotation rather than an edit:

```bash
docker service rm cka_bot                 # frees the secret
docker secret rm cka_telegram_token
# put TELEGRAM_BOT_TOKEN in .env, then
./install.sh
```

On Kubernetes the Deployment ships with `replicas: 0` for the same reason - a
Deployment has no "do not restart" option, so a bot with no token would sit in
CrashLoopBackOff. Put the token in the Secret, then scale it up:

```bash
kubectl -n cka-prep scale deployment/cka-bot --replicas=1
```

**Never more than one replica.** Long polling means two processes on one token
compete for every update and Telegram rejects one of them.

## Automatic deploys

Two units in [systemd/](systemd/), driving two scripts in [bin/](bin/). The
split is deliberate: polling is cheap and must never fail, deploying is
expensive and its failures need to be attributable.

| Unit | Type | Does |
| --- | --- | --- |
| `cka-check.timer` | timer, every 5 min | fires `cka-check.service` |
| `cka-check.service` | oneshot | `git fetch`, compares `HEAD` with `origin/main`, and if they differ starts the deploy |
| `cka-deploy.service` | oneshot | fast-forwards, `docker compose up -d --build`, waits for health |

Install:

```bash
sudo install -m 0755 deploy/bin/cka-check-updates.sh /usr/local/bin/cka-check-updates
sudo install -m 0755 deploy/bin/cka-deploy.sh        /usr/local/bin/cka-deploy
sudo install -m 0644 deploy/systemd/cka-*            /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cka-check.timer
```

Watch it:

```bash
systemctl list-timers cka-check.timer
journalctl -u cka-check.service -f      # one line per poll
journalctl -u cka-deploy.service -f     # build output
sudo systemctl start cka-deploy         # deploy right now, skip the wait
```

### How it behaves

**A dirty working tree stops the deploy.** A deploy target has to mirror the
remote; fast-forwarding over local edits either fails outright or throws them
away without saying so. So `cka-deploy` checks `git status --porcelain` first and
refuses, naming the files. Fix it by committing and pushing the change, or by
discarding it — then the next poll picks up where it left off.

**A build outlasting the interval is fine.** The checker triggers with
`systemctl start --no-block`, and starting an already-running oneshot unit is a
no-op, so a ten-minute build does not stack up two deploys.

**The pipeline updates itself.** After a successful deploy, `cka-deploy` copies
`deploy/bin/*` and `deploy/systemd/*` out of the repo into their system
locations and reloads systemd if anything changed. A commit can therefore change
the deploy process, taking effect on the run after it lands.

**Images are pruned, volumes never.** `docker image prune -f` runs after a
successful deploy and only removes dangling layers from the build.

### Manual updates

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
