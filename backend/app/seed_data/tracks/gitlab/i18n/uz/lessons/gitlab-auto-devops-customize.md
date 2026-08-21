## Pipeline’ni fork qilmasdan tugmalarni burash

Deyarli har Auto DevOps xulqi - **CI/CD variable**. Ularni loyiha yoki guruh
darajasida o’rnating, generatsiya qilingan pipeline moslashadi - YAML yo’q.

| Variable | Ta’siri |
|---|---|
| `STAGING_ENABLED=1` | `staging` environment qo’shadi; `production` manual bo’ladi |
| `CANARY_ENABLED=1` | production’dan oldin manual canary deploy qo’shadi |
| `INCREMENTAL_ROLLOUT_MODE=manual` / `timed` | production manual qadamlar yoki 5 daqiqalik taymerlar bilan 10% → 25% → 50% → 100% chiqadi |
| `REPLICAS`, `PRODUCTION_REPLICAS`, `<ENV>_REPLICAS` | har environment uchun pod sonlari |
| `ADDITIONAL_HOSTS`, `<ENV>_ADDITIONAL_HOSTS` | qo’shimcha ingress hostname’lar |
| `AUTO_DEVOPS_DEPLOY_DEBUG=1` | Helm qiymatlari va buyruqlarini chiqaradi |
| `TEST_DISABLED=1`, `CODE_QUALITY_DISABLED=1`, `SAST_DISABLED=1`, `DAST_DISABLED=1`, `CONTAINER_SCANNING_DISABLED=1`, `REVIEW_DISABLED=1`, `PERFORMANCE_DISABLED=1` | job’ni tashlab yuborish |
| `AUTO_DEVOPS_BUILD_IMAGE_EXTRA_ARGS` | build uchun `--build-arg`lar |
| `HELM_UPGRADE_EXTRA_ARGS`, `HELM_UPGRADE_VALUES_FILE` | chart’ga qiymatlar uzatish |
| `K8S_SECRET_<NAME>` | deploy qilingan pod’larda `<NAME>` muhit o’zgaruvchisi bo’ladi (Kubernetes Secret) - ilovaga `DATABASE_URL`ini berish yo’li |

```text
# loyiha variable’lari
STAGING_ENABLED=1
INCREMENTAL_ROLLOUT_MODE=manual
K8S_SECRET_DATABASE_URL=postgres://…        (himoyalangan, scope: production)
PRODUCTION_REPLICAS=3
```

## Template’larni include qiling va job’larni bekor qiling

Variable yetmaganda **Auto DevOps’ni saqlang, lekin uni include qiladigan va
kerakli narsani bekor qiladigan `.gitlab-ci.yml` yozing**:

```yaml
include:
  - template: Auto-DevOps.gitlab-ci.yml

variables:
  STAGING_ENABLED: "1"

# bitta generatsiya qilingan job’ni bekor qiling: o’sha nom, o’zgarishlaringiz merge bo’ladi
test:
  image: node:20-alpine
  script:
    - npm ci
    - npm test
  artifacts:
    reports: { junit: reports/junit.xml }

# template’da yo’q job qo’shing
notify:
  stage: production
  needs: [production]
  script: ./notify-slack.sh "deployed $CI_COMMIT_SHORT_SHA"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

Template job’i bilan bir xil nomli job siz o’rnatgan kalitlarni
**almashtiradi** va qolganini saqlaydi - `extends` merge qilgandek.
Generatsiya qilingan job’ni butunlay olib tashlash uchun uning `*_DISABLED`
variable’ini o’rnating yoki `rules: [ { when: never } ]` bering.

Auto DevOps’ning **faqat qismlarini** ham include qilishingiz mumkin -
`Jobs/Build.gitlab-ci.yml`, `Jobs/Deploy.gitlab-ci.yml`,
`Jobs/Test.gitlab-ci.yml` - qolganini o’zingiz yozing, bu ko’pincha oltin
o’rta: ularning build va deploy’i, sizning testlaringiz.

## O’z chart’ingiz

`AUTO_DEVOPS_CHART_REPOSITORY` (va `_USERNAME`/`_PASSWORD`) bilan
`AUTO_DEVOPS_CHART=xyz-charts/web-app` birga keladigan `auto-deploy-app`
chart’ini siznikiga almashtiradi;
`HELM_UPGRADE_VALUES_FILE=.gitlab/auto-deploy-values.yaml` - yengilroq
variant - chart’ni saqlang, repo’da values fayl yetkazing.

## Auto DevOps o’zini oqlamay qo’yadigan chiziq

O’zingizni `build`, `production` va uchta skanerni bekor qilayotgan, values
fayl va chart saqlayotgan holda topsangiz, sizda katta include’li maxsus
pipeline bor. Bu yaxshi - lekin uni component’lardan (7-hafta) qurilgan
*o’z* `.gitlab-ci.yml`ingiz sifatida yozing va template job’larini
tushunganingiz sari bittalab oling. Auto DevOps sizni birinchi kun
production’ga yetkazdi; bu yo’nalishning qolgani - u yerdan uni qanday
egallashingiz.

## O’z-o’zini tekshirish

- YAML’ga tegmasdan deploy qilingan ilovaga maxfiy muhit o’zgaruvchisini qanday berasiz?
- `.gitlab-ci.yml`ingiz template job’i bilan bir xil nomli job ta’riflaganda nima bo’ladi?
- Auto DevOps’dan o’sib chiqqaningizning bitta belgisini ayting.
