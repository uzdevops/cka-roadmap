## `config.toml` - muhim fayl

```toml
# /etc/gitlab-runner/config.toml
concurrent = 4                      # bu host bir vaqtda ishlatadigan job’lar, barcha [[runners]] bo’ylab
check_interval = 3
log_level = "warning"

[[runners]]
  name = "xyz-build-01"
  url = "https://gitlab.com"
  token = "glrt-…"
  executor = "docker"
  limit = 4                         # SHU runner yozuvi uchun maks parallel job
  environment = ["DOCKER_TLS_CERTDIR=/certs"]
  [runners.cache]
    Type = "s3"                     # runner’lar bo’ylab umumiy cache (ixtiyoriy)
    Shared = true
    [runners.cache.s3]
      ServerAddress = "minio.internal:9000"
      BucketName = "runner-cache"
      Insecure = true
  [runners.docker]
    image = "alpine:3.20"           # job hech narsa o’rnatmaganda default image
    privileged = true               # docker:dind service’lar uchun kerak
    volumes = ["/cache", "/certs/client"]
    pull_policy = ["if-not-present", "always"]
    shm_size = 0
```

Tahrirlang, keyin `sudo gitlab-runner restart` (yoki o’zgarishda qayta
yuklaydi). Bilishga arziydigan kalitlar:

| Kalit | Nega tegasiz |
|---|---|
| `concurrent` | host’ning umumiy parallelligi - CPU/RAM bilan chegaralangan |
| `limit` | bitta runner yozuvini chegaralash (masalan deploy runner’ni 1 da) |
| `privileged` | `docker:dind`ga kerak; bu host’da root - faqat ishonchli loyihalar uchun |
| `volumes` | doimiy `/cache`; `/var/run/docker.sock`ni mount qilish - job’larga docker berishning *boshqa* yo’li (umumiy daemon, dind yo’q) |
| `pull_policy` | `if-not-present` image’larni job’lar orasida lokal saqlaydi - katta tezlashish; harakatlanuvchi image’lar uchun `always` |
| `[runners.cache]` | cache’ni host’dan chiqaring, har runner ko’rsin |

## Executor’ni tanlash

| Executor | Izolyatsiya | Tezlik | Eslatmalar |
|---|---|---|---|
| `shell` | yo’q - job’lar host foydalanuvchisini bo’lishadi | eng tez, hammasini cache’laydi | faqat bitta ishonchli jamoa uchun; `gitlab-runner` foydalanuvchisiga vositalar kerak |
| `docker` | har job’ga container | image tortishlar narxi; volume’lar orqali cache | default tanlov |
| `docker` + socket mount | har job’ga container, **umumiy** daemon | tez build’lar (layer cache) | job’lar bir-birining container’larini ko’radi |
| `docker` + dind service | har job’ga container, har job’ga daemon | sekinroq build’lar | toza, `privileged` kerak |
| `kubernetes` | har job’ga Pod | klaster bilan masshtablanadi | `[runners.kubernetes]` orqali config; klasterga image pull hisob ma’lumotlari kerak |
| `docker-autoscaler` / `instance` | har job’ga VM (fleeting plugin) | elastik | docker+machine’ni almashtiradi |

## Uni boshqarish

```bash
sudo gitlab-runner list                 # bu host’da ro’yxatdan o’tgan runner’lar
sudo gitlab-runner verify               # har biri GitLab’ga yeta oladimi?
sudo gitlab-runner status
sudo journalctl -u gitlab-runner -f     # runner’ning o’z log’i (job log’lari emas)
sudo gitlab-runner unregister --name xyz-build-01
```

Runner’ni paket menejeri bilan yangilang; GitLab serveridan bir-ikki minor
versiya ichida saqlang. Host’da to’g’ridan-to’g’ri chiqish bo’lmasa
`environment = ["HTTPS_PROXY=…"]` bilan `gitlab-runner`ni proxy ortiga
qo’ying.

## Deploy runner, to’g’ri qilingan

Bitta runner yozuvi, `limit = 1`, tag `deploy`, **himoyalangan** (faqat
himoyalangan ref’lar), SSH kalitlari yoki kubeconfig’ni fayl sifatida
saqlaydigan mustahkamlangan host’da `executor = "shell"` - va GitLab
variable’larida umuman *hech qanday* sir yo’q. Undagi job’lar
`tags: [deploy]` va `resource_group`langan. Buzilgan feature branch’ning
zarar radiusi nol.

## O’z-o’zini tekshirish

- `concurrent = 4` va `limit = 1`li runner - bir vaqtda nechta deploy job ishlaydi? Jami nechta job?
- dind va docker socket’ni mount qilish orasidagi murosa nima?
- `pull_policy = ["if-not-present", "always"]` nega shu tartibda?
