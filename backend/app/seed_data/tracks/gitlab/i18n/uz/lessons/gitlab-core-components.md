## Beshta komponent

GitLab pipeline beshta narsadan iborat. Keyingi har bir dars shu beshtadan
biriga yaqinroq qarash.

```text
.gitlab-ci.yml ──► pipeline ──► stage’lar ──► job’lar ──► runner (executor)
   fayl           bitta ijro     tartib       ish         mashina
```

### 1. `.gitlab-ci.yml`

Repozitoriy ildizidagi YAML. Yuqori darajali kalitlar yo **global kalit
so’zlar** (`stages`, `default`, `variables`, `workflow`, `include`), yo
**job nomlari**. `script`ga ega har narsa - job.

```yaml
default:
  image: alpine:3.20        # o’zinikini o’rnatmagan har bir job’ga qo’llanadi

variables:
  APP_NAME: xyz-web         # har job’ga mavjud

stages: [prepare, build]
```

### 2. Pipeline

Bitta commit uchun faylning bitta ijrosi. Pipeline’ning **source**’i bor -
`push`, `merge_request_event`, `schedule`, `web`, `api`, `trigger` - uni
`rules:` `$CI_PIPELINE_SOURCE` sifatida o’qiy oladi. Bitta commit bir
nechta pipeline berishi mumkin (branch pipeline *va* merge request
pipeline) - "Merge request pipeline’lar" darsi buni tartibga soladi.

### 3. Stage’lar

Tartib. Hech narsa e’lon qilmasangiz default stage’lar: `.pre`, `build`,
`test`, `deploy`, `.post`. O’zingiznikini e’lon qilish o’rtadagi uchtasini
almashtiradi; `.pre` va `.post` har doim mavjud va qolganlarini qamrab turadi.

### 4. Job’lar

```yaml
build-app:
  stage: build
  image: node:20-alpine
  before_script:
    - npm ci
  script:
    - npm run build
  after_script:
    - echo "done, exit code was $CI_JOB_STATUS"
  artifacts:
    paths: [dist/]
```

`before_script` va `after_script` `script` bilan bir xil shell’da ishlaydi
(`after_script` `script` yiqilganda ham ishlaydi). Job **holati**ni faqat
`script` hal qiladi.

### 5. Runner’lar va executor’lar

**Runner** - GitLab’dan job so’rab turadigan `gitlab-runner` jarayoni.
Uning **executor**’i job *qanday* izolyatsiya qilinishini hal qiladi:
`shell` (to’g’ridan-to’g’ri host’da), `docker` (har job yangi container’da -
keng tarqalgan tanlov), `kubernetes` (har job bitta Pod) va yana bir
nechtasi. gitlab.com’da shared runner’lar avtomatik masshtablanadigan
VM’larda `docker` ishlatadi - `image:` shuning uchun shunchalik muhim: bu
`script`ingiz ishlaydigan container.

## Job log’ini shu beshtasi orqali o’qish

```text
Running with gitlab-runner 17.x (abc123)         ← runner
  on blue-1.saas-linux-small-amd64.runners ...   ← runner nomi / executor
Preparing the "docker+machine" executor          ← executor
Using Docker executor with image node:20-alpine  ← image
Getting source from Git repository               ← toza klon
$ npm ci                                         ← before_script
$ npm run build                                  ← script
Uploading artifacts for successful job           ← artifact’lar
Job succeeded
```

## O’z-o’zini tekshirish

- Pipeline stage ro’yxatidan hech qachon olib tashlab bo’lmaydigan ikkita kalit qaysi?
- Job `script`da yiqiladi, `after_script` esa yaxshi ishlaydi. Job holati qanday?
- Uchta executor’ni ayting va har biri uchun job qayerda ishlashini tushuntiring.
