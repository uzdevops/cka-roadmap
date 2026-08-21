## Runner allaqachon biladigan narsalar

Har job commit, pipeline, loyiha va runner’ni tavsiflaydigan bir necha yuz
**predefined variable** bilan boshlanadi. Siz ularni hech qachon
o’rnatmaysiz; o’qiysiz. Har hafta ishlatadiganlaringiz:

| Variable | Misol | Qo’llanish |
|---|---|---|
| `CI_COMMIT_SHA` / `CI_COMMIT_SHORT_SHA` | `a1b2c3d4…` / `a1b2c3d4` | image tag’lar, build ID’lar |
| `CI_COMMIT_BRANCH` | `feature/login` | faqat branch pipeline’larda (MR/tag pipeline’larda bo’sh) |
| `CI_COMMIT_TAG` | `v1.4.0` | faqat tag pipeline’larda |
| `CI_COMMIT_REF_NAME` / `CI_COMMIT_REF_SLUG` | `feature/login` / `feature-login` | ref va uning DNS/yo’l uchun xavfsiz versiyasi |
| `CI_DEFAULT_BRANCH` | `main` | "men default branch’damanmi?" - qattiq yozmasdan |
| `CI_PIPELINE_SOURCE` | `push`, `merge_request_event`, `schedule`, `web`, `api`, `trigger` | `rules:` uchun eng foydali kiritma |
| `CI_PIPELINE_ID` / `CI_PIPELINE_IID` | `1842317` / `57` | global id / loyiha bo’yicha hisoblagich |
| `CI_JOB_NAME`, `CI_JOB_ID`, `CI_JOB_STATUS` | | log, `after_script` |
| `CI_PROJECT_PATH`, `CI_PROJECT_DIR` | `xyz-team/app`, `/builds/xyz-team/app` | yo’llar |
| `CI_REGISTRY`, `CI_REGISTRY_IMAGE`, `CI_REGISTRY_USER`, `CI_REGISTRY_PASSWORD` | | container registry login (5-hafta) |
| `CI_JOB_TOKEN` | | API / registry / paketlarga kirish uchun qisqa umrli token |
| `CI_MERGE_REQUEST_IID`, `CI_MERGE_REQUEST_SOURCE_BRANCH_NAME`, `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` | | faqat MR pipeline’larda |
| `CI_ENVIRONMENT_NAME`, `CI_ENVIRONMENT_URL` | | `environment:`li job’larda (6-hafta) |
| `GITLAB_USER_LOGIN`, `GITLAB_USER_EMAIL` | | kim ishga tushirgani |

```yaml
show:
  image: alpine:3.20
  script:
    - echo "pipeline $CI_PIPELINE_IID from $CI_PIPELINE_SOURCE"
    - echo "ref $CI_COMMIT_REF_NAME (slug $CI_COMMIT_REF_SLUG) commit $CI_COMMIT_SHORT_SHA"
    - echo "by $GITLAB_USER_LOGIN on runner $CI_RUNNER_DESCRIPTION"
    - env | grep -E '^(CI_|GITLAB_)' | sort     # to’liq ro’yxat, bu pipeline turi uchun
```

Bu job’ni push’dan, merge request’dan va schedule’dan ishga tushiring va
uchta log’ni solishtiring. Bir holatda *bo’sh*, boshqasida o’rnatilgan
variable’lar - aynan ertaga `rules:` tayanadigan variable’lar.

## Ular asosida qurilgan namunalar

**Yagona va kuzatiladigan image tag:**

```yaml
variables:
  IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
```

**Branch uchun xavfsiz hostname** (`feature/login` → `feature-login`):

```yaml
environment:
  name: review/$CI_COMMIT_REF_SLUG
  url: https://$CI_COMMIT_REF_SLUG.review.example.com
```

**Faqat default branch’da, hech qayerga "main" yozmasdan:**

```yaml
rules:
  - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

**Job’dan GitLab API’ni chaqirish, saqlangan token’siz:**

```yaml
script:
  - 'curl --header "JOB-TOKEN: $CI_JOB_TOKEN" "$CI_API_V4_URL/projects/$CI_PROJECT_ID/releases"'
```

## O’z-o’zini tekshirish

- Qaysi variable pipeline schedule tomonidan boshlanganini aytadi?
- `CI_COMMIT_BRANCH` job’ingizda bo’sh. Bu kutilgan ikki pipeline turini ayting.
- URL’da nega `CI_COMMIT_REF_NAME` emas, `CI_COMMIT_REF_SLUG`?
