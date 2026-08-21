## Resource group’lar - iltimos, navbat bilan

Bir paytda bir environment’ga deploy qilayotgan ikki pipeline - staging
server yarmi eski, yarmi yangi bo’lib qolishining yo’li. **Resource group**
- nomlangan mutex: uni bo’lishadigan job’lar pipeline’lar bo’ylab **bir
vaqtda bittadan** ishlaydi.

```yaml
deploy-staging:
  script: ./deploy.sh staging
  resource_group: staging          # istalgan satr; qamrov - loyiha

deploy-prod:
  script: ./deploy.sh production
  resource_group: production
```

Ikkinchi `deploy-staging` birinchisi tugaguncha kutadi (holat *waiting for
resource*). API’dagi `process_mode` (`unordered` default, `oldest_first`,
`newest_first`) navbat tartibini hal qiladi; "faqat eng oxirgi commit
haqiqatan deploy bo’lsin" uchun sizga `newest_first` kerak.

## Timeout’lar

Osilib qolgan job runner’ni garovda ushlaydi. Loyiha default’i 1 soat
(*Settings → CI/CD → General pipelines*); job uni qisqartira oladi,
runner’ning o’z chegarasidan hech qachon oshira olmaydi:

```yaml
integration:
  script: ./run-integration.sh
  timeout: 20 minutes              # 1h 30m, 2h, 90m - hammasi yaroqli
```

Chegaraga yetgan job aniq xabar bilan **yiqitiladi**; bu bir soat hech kim
sezmaydigan pipeline’dan yaxshi.

## `image:` va `services:`

`image:` - job shell’i ishlaydigan container. `services:` - u bilan yonma-yon
ishga tushiriladigan va hostname bo’yicha erishiladigan **qo’shimcha
container’lar** - test job’iga ma’lumotlar bazasi berishning standart yo’li:

```yaml
integration-tests:
  image: node:20-alpine
  services:
    - name: postgres:16-alpine
      alias: db                    # job tarmog’i ichidagi hostname
  variables:
    POSTGRES_USER: app
    POSTGRES_PASSWORD: secret
    POSTGRES_DB: app_test
    DATABASE_URL: postgres://app:secret@db:5432/app_test
  script:
    - npm ci
    - npm run test:integration
```

Job’dagi variable’lar service container’larga ham uzatiladi - `postgres`
o’z user va parolini shunday oladi. `alias`siz hostname image nomidan
chiqariladi (`postgres`). Image tortishlar runner pull policy’siga amal
qiladi - self-managed docker runner’da `if-not-present`, SaaS’da har doim
yangi.

`image:` `entrypoint:` override va `pull_policy:` ham tashiy oladi (runner
ruxsat bergan joyda). Vosita image’i shell o’rniga vositani ishga tushirishga
default qilinganda foydali:

```yaml
scan:
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]               # PID 1 sifatida `trivy` emas, shell ber
  script:
    - trivy image --exit-code 1 "$IMAGE"
```

## `parallel:` va `parallel:matrix`

Bir xil job’ni N marta ishlating (`CI_NODE_INDEX` / `CI_NODE_TOTAL` test
to’plamini bo’laklashga imkon beradi), yoki variable’lar kombinatsiyasi
bo’yicha bir martadan:

```yaml
unit-shards:
  script: npm test -- --shard=$CI_NODE_INDEX/$CI_NODE_TOTAL
  parallel: 4

build:
  script: ./build.sh "$OS" "$ARCH"
  parallel:
    matrix:
      - OS: [linux, darwin]
        ARCH: [amd64, arm64]
      - OS: [windows]
        ARCH: [amd64]
```

Bu matrix `build: [linux, amd64]` va hokazo nomli beshta job yaratadi, har
biri o’z `$OS`/`$ARCH` bilan, parallel. Ulardan biriga muhtoj job nomni
to’liq yozadi: `needs: ["build: [linux, amd64]"]`.

## O’z-o’zini tekshirish

- Ikki pipeline bir daqiqa ichida `deploy-staging` ishlatadi. Deploy’lar
  ustma-ust tushmasligini nima kafolatlaydi?
- Test job’iga Redis kerak. Qaysi kalit so’z va job unga qanday yetadi?
- `OS: [a, b]` × `ARCH: [x, y, z]` matrix’i nechta job yaratadi?
