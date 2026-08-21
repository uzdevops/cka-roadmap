## Shared runner’larda ishlatish

Shared runner’lar yoqilgan bo’lsa job’ga faqat `script` kerak. Siz
o’rnatmasangiz runner o’z default image’ini tanlaydi - gitlab.com’da bu
`ruby:3.1`. Har doim image’ni aniq o’rnating; default - tarixiy tasodif,
tavsiya emas.

```yaml
default:
  image: alpine:3.20

check-tools:
  script:
    - apk add --no-cache curl jq
    - curl -s https://api.github.com/repos/git/git | jq .stargazers_count
```

O’sha `apk add` qatori "job’imga image’da yo’q vosita kerak" uchun namuna:
job boshida o’rnating. Ishlaydi, sekin (har job, har safar) va 5-haftada
ko’pini maxsus image yoki cache bilan almashtirasiz.

## `before_script` va `after_script`

```yaml
default:
  before_script:
    - echo "== $CI_JOB_NAME on $(hostname) =="
    - apk add --no-cache bash
  after_script:
    - echo "== finished with status $CI_JOB_STATUS =="

build:
  script:
    - bash ./build.sh
```

- `before_script` qatorlari `script` oldiga **bir xil shell’da** qo’shiladi -
  u yerda export qilgan variable’lar `script`da ko’rinadi.
- `after_script` **alohida** shell’da ishlaydi, hatto yiqilgan `script`dan
  keyin ham, `$CI_JOB_STATUS` `success`/`failed`/`canceled` qilib
  o’rnatilgan holda. Tozalash va xabarnomalar uchun ishlating; `script`dagi
  variable’lar u yerda bo’lishiga tayanmang.
- Job darajasidagi `before_script` default’nikini **almashtiradi**, qo’shilmaydi.
  Ikkalasini xohlasangiz qatorlarni takrorlang.

## Uchinchi tomon kutubxonalari, halol yo’l

Bog’liqliklarni `before_script`da o’rnatish `script`ni o’qishga oson saqlaydi:

```yaml
test:
  image: python:3.12-slim
  before_script:
    - pip install --quiet -r requirements.txt
  script:
    - pytest -q
```

Ikki qoida: o’rnatganingizni qotiring (`requirements.txt`,
`package-lock.json`, `apk add curl=8.*`) - kecha o’tgan pipeline bugun ham
o’tsin; va lock-fayl varianti (`pip install -r`, `npm ci`)siz hech qachon
`pip install` / `npm install` qilmang - lock’siz o’rnatish har ishga
tushirishda boshqa muhit.

## Skriptlar YAML’da emas, fayllarda

`script` besh qatordan oshgach, uni repozitoriyga ko’chiring va chaqiring:

```yaml
deploy:
  image: alpine:3.20
  script:
    - chmod +x scripts/deploy.sh       # Git bit’ni saqlamasligi mumkin
    - ./scripts/deploy.sh "$CI_ENVIRONMENT_NAME"
```

```bash
#!/usr/bin/env sh
# scripts/deploy.sh - CI’da ham, laptopda ham bir xil ishlaydi
set -eu
target="${1:?environment name required}"
echo "deploying $CI_COMMIT_SHORT_SHA to $target"
```

`set -eu` skriptni birinchi xatoda va o’rnatilmagan variable’da yiqitadi -
YAML `script` bilan bir xil shartnoma. Lokal ishga tushira oladigan skript -
lokal debug qila oladigan pipeline.

## O’z-o’zini tekshirish

- `before_script`da export qilingan variable - `script`da ko’rinadimi? `after_script`da-chi?
- Pipeline’da nega `npm install` emas, `npm ci`?
- Job darajasida `before_script` o’rnatdingiz. `default:`dagisi hali ham ishlaydimi?
