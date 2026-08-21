## Pipeline ichida image yig’ish

`build` stage’i testlangan kodni container image’ga aylantiradi. Job’ga
gaplashadigan Docker daemon kerak - `docker` executor’dagi job esa
*o’zi* container - xo’sh, daemon qayerdan keladi? Uchta javob, qanchalik
tez-tez ishlatishingiz tartibida.

## 1. Service sifatida Docker-in-Docker (`dind`)

```yaml
build-image:
  stage: build
  image: docker:27
  services:
    - docker:27-dind
  variables:
    DOCKER_HOST: tcp://docker:2376          # service’ning hostname’i
    DOCKER_TLS_CERTDIR: "/certs"            # dind sertifikatlarni shu yerda yaratadi…
    DOCKER_TLS_VERIFY: 1                    # …va client ularni tekshiradi
    DOCKER_CERT_PATH: "/certs/client"
  before_script:
    - docker info                           # daemon’ga yetish mumkinligini isbotlaydi
  script:
    - docker build --pull -t "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA" .
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_COMMIT_TAG
```

`docker:27-dind` service’i job yonida haqiqiy daemon ishlatadi; `docker:27`
image’i job’ga CLI beradi. Runner **privileged** container’larga ruxsat
berishi kerak - gitlab.com shared runner’lari beradi; self-managed docker
runner’ga `config.toml`da `privileged = true` kerak (8-hafta). Uchta TLS
variable bezak emas: ularsiz client va daemon socket’da kelisha olmaydi va
klassik *"Cannot connect to the Docker daemon at tcp://docker:2375"*
olasiz.

## 2. Kaniko - daemon yo’q, privilege yo’q

```yaml
build-image:
  stage: build
  image:
    name: gcr.io/kaniko-project/executor:v1.23.2-debug
    entrypoint: [""]
  script:
    - /kaniko/executor
        --context "$CI_PROJECT_DIR"
        --dockerfile "$CI_PROJECT_DIR/Dockerfile"
        --destination "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
```

Kaniko userspace’da yig’adi va push qiladi; registry hisob ma’lumotlarini
`/kaniko/.docker/config.json`dan o’qiydi - GitLab’da uni predefined
registry variable’lari bilan to’ldirasiz (keyingi dars). Privileged
container’larga ruxsat bo’lmaganda kaniko (yoki buildah) tanlang -
tartibga solingan muhitlarda va Kubernetes executor’larda keng tarqalgan.

## 3. Shell executor’ning o’z daemon’i

Self-managed `shell` runner’da job shunchaki host daemon’iga qarshi
`docker build` ishlatadi. Oddiy, tez (layer cache job’lar orasida
saqlanadi) va eng kam izolyatsiyalangan: har job boshqa har job’ning
container’larini ko’ra va o’chira oladi. Bitta jamoaning mashinasi uchun
yaxshi, umumiy park uchun noto’g’ri.

## Build’ni takrorlanadigan va tez qiling

```dockerfile
# Dockerfile - XYZ nodejs-app
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev

FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
USER node
CMD ["node", "server.js"]
```

- `COPY . .`dan **oldin** `COPY package*.json` - lock fayl o’zgarmaguncha
  bog’liqliklar layer’i cache’lanadi.
- `docker build`da `--pull` - bazaviy image yangilanadi.
- `--cache-from "$CI_REGISTRY_IMAGE:latest"` (`BUILDKIT_INLINE_CACHE=1`
  bilan) yangi dind daemon’ga oxirgi push qilingan image layer’larini qayta
  ishlatishga imkon beradi - "har job bo’sh cache bilan boshlanadi"ning dind
  davosi.

## O’z-o’zini tekshirish

- `docker` executor job’iga `docker build` uchun nega `dind` service kerak?
- Uchta TLS variable’ni ayting va ularsiz nima noto’g’ri ketadi.
- Qachon dind o’rniga kaniko tanlaysiz?
