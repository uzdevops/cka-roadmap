## GitLab ko’ra oladigan deploy’lar

Deploy job - shunchaki job - GitLab’ga *nimani* *qayerga* deploy
qilganingizni aytmaguningizcha. `environment:` shuni qiladi va evaziga
GitLab har deploy’ni kuzatadi: qaysi commit qayerda jonli, kim deploy qildi,
qachon, ishlayotgan narsaga havola bilan va istalgan oldingi versiyani bir
bosishda **qayta deploy** qilish.

```yaml
deploy-dev:
  stage: deploy
  image: alpine:3.20
  script:
    - ./deploy.sh dev "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
  environment:
    name: dev
    url: https://dev.xyz.example.com
    deployment_tier: development      # production | staging | testing | development | other
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

*Operate → Environments* `dev`ni oxirgi deploy’i, **Open** tugmasi (`url:`)
va tarixi bilan ro’yxatlaydi. Bu yo’nalishdagi har keyingi deploy job
`environment:` blokini tashiydi; usiz deploy platformaga ko’rinmaydi.

## Job ichida

`environment:` `CI_ENVIRONMENT_NAME`, `CI_ENVIRONMENT_SLUG`,
`CI_ENVIRONMENT_URL` va `CI_ENVIRONMENT_TIER`ni o’rnatadi - bitta deploy
skripti har environment’ga xizmat qila oladi:

```bash
#!/usr/bin/env sh
# deploy.sh <env> <image>
set -eu
env="$1"; image="$2"
echo "deploying $image to $env ($CI_ENVIRONMENT_URL)"
```

## Environment scope’li variable’lar

3-haftadagi variable’larda **environment scope** bor. `DEPLOY_HOST`ni uch
marta ta’riflang - scope `dev`, `staging`, `production` - va har deploy job
o’sha `$DEPLOY_HOST` orqali to’g’risini o’qiydi. Wildcard’lar ishlaydi:
`review/*` har review app’ga mos keladi (keyingi darslar).

## Tier’lar va ular nega muhim

`deployment_tier` - GitLab o’yinchoq environment’ni sizni uyg’otadiganidan
ajratadigan yo’l: production environment’lar himoya qoidalari oladi
("Staging va production" darsi), dashboard’lar tier bo’yicha guruhlaydi va
`environment: name: production` avtomatik production tier deb hisoblanadi.
Environment’larni oddiy nomlang - `dev`, `staging`, `production` - va nom
shulardan biri bo’lmasa tier’ni o’rnating.

## Deploy job shakli, to’liq

```yaml
.deploy:
  stage: deploy
  image: alpine:3.20
  before_script:
    - apk add --no-cache openssh-client curl
  script:
    - ./deploy.sh "$CI_ENVIRONMENT_NAME" "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
    - curl -fsS "$CI_ENVIRONMENT_URL/healthz"      # u javob bermaguncha deploy tugamagan
  resource_group: $CI_ENVIRONMENT_NAME              # har environment’ga bir vaqtda bitta deploy

deploy-dev:
  extends: .deploy
  environment: { name: dev, url: https://dev.xyz.example.com }
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

Health check qatori - "skript 0 bilan chiqdi" va "servis ishlab turibdi"
orasidagi farq. Uni har deploy’ning qismi qiling.

## O’z-o’zini tekshirish

- Deploy job’ga `environment:` qo’shib nimaga erishasiz?
- Variable staging va production’da bir nom bilan turli qiymatga ega bo’lishi kerak. Qaysi mexanizm?
- Deploy job oxirida nega health endpoint’ni `curl` qiladi?
