## XYZ pipeline’i, yig’ilgan

Sakkiz hafta oldin release bitta muhandisning boshidagi tushdan keyingi vaqt
edi. `nodejs-app/.gitlab-ci.yml` hozir shunday ko’rinadi - va uning har
qatori siz ishga tushirgan narsa:

```yaml
include:
  - component: gitlab.com/xyz-team/ci-components/node-test@1.1.0
    inputs: { node_version: "20" }
  - component: gitlab.com/xyz-team/ci-components/docker-build@2.0.1
  - template: Jobs/Secret-Detection.gitlab-ci.yml
  - template: Jobs/Dependency-Scanning.gitlab-ci.yml
  - template: Jobs/Container-Scanning.gitlab-ci.yml

workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS
      when: never
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_COMMIT_TAG

default:
  interruptible: true
  retry: { max: 1, when: [runner_system_failure, stuck_or_timeout_failure] }

stages: [test, build, publish, deploy]

lint:
  stage: test
  extends: .node
  script: npx eslint . --format gitlab --output-file gl-codequality.json
  artifacts: { when: always, reports: { codequality: gl-codequality.json } }
  allow_failure: { exit_codes: [1] }

container_scanning:
  needs: [publish-image]
  variables: { CS_IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA" }

.deploy:
  stage: deploy
  interruptible: false
  tags: [deploy]
  resource_group: $CI_ENVIRONMENT_NAME
  script:
    - ./deploy.sh "$CI_ENVIRONMENT_NAME" "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
    - curl -fsS "$CI_ENVIRONMENT_URL/healthz"

deploy-review:
  extends: .deploy
  environment: { name: review/$CI_COMMIT_REF_SLUG, url: https://$CI_ENVIRONMENT_SLUG.review.xyz.example.com, on_stop: stop-review, auto_stop_in: 2 days }
  rules: [ { if: $CI_PIPELINE_SOURCE == "merge_request_event" } ]

stop-review:
  extends: .deploy
  script: ./deploy.sh stop "$CI_ENVIRONMENT_SLUG"
  environment: { name: review/$CI_COMMIT_REF_SLUG, action: stop }
  variables: { GIT_STRATEGY: none }
  rules: [ { if: $CI_PIPELINE_SOURCE == "merge_request_event", when: manual } ]

deploy-dev:
  extends: .deploy
  environment: { name: dev, url: https://dev.xyz.example.com }
  rules: [ { if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH } ]

deploy-staging:
  extends: .deploy
  environment: { name: staging, url: https://staging.xyz.example.com }
  rules:
    - if: $CI_COMMIT_TAG
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
      allow_failure: false

deploy-prod:
  extends: .deploy
  environment: { name: production, url: https://xyz.example.com }
  rules: [ { if: $CI_COMMIT_TAG, when: manual, allow_failure: false } ]
```

Plus, fayldan tashqarida: himoyalangan `main` va `v*`, approval’li
himoyalangan `production`, himoyalangan va scope’langan variable’lar, faqat
himoyalangan ref’larni oladigan `deploy` runner, pipeline’da `CODEOWNERS`,
guruh scan-execution va approval policy’lari, registry’da cleanup
policy’lar va pipeline hamda coverage badge’li README.

## Uni ro’yxat sifatida qayta o’qish

| Hafta | Fayldagi nima buni isbotlaydi |
|---|---|
| 1-2 | stage’lar, job’lar, image’lar, artifact’lar, component’lar ichidagi `needs` |
| 3 | `workflow:rules`, har `rules:` bloki, `resource_group`, `interruptible` |
| 4 | JUnit + coverage + code quality hisobotlari, `allow_failure:exit_codes` |
| 5 | component orqali `.node`/cache, docker-build component, registry, MR’ni biladigan workflow |
| 6 | environment’lar, review app’lar, manual gate’lar, tag bilan boshqariladigan production |
| 7 | versiyali component’lar, skanerlar, fayl atrofidagi himoyalar |
| 8 | self-managed himoyalangan runner’dagi `tags: [deploy]`; endi siz ustun bo’lgan Auto DevOps ma’lumotnoma sifatida |

## Keyin qayerga

- **GitLab Certified CI/CD Associate** - imtihon bu yo’nalishga yaqin mos
  keladi; amaliy qismi - kichik XYZ pipeline’i.
- **GitOps** - Flux yoki Argo CD pipeline’ingiz yozadigan manifest
  repo’sidan tortsin; `deploy` stage’i commit’ga aylanadi.
- **Pipeline kuzatuvi** - *Analyze*dagi DORA ko’rsatkichlari, pipeline
  davomiyligi trendlari va XYZ jamoasi endi tushdan keyin kutib o’tirgan
  odamlarga ko’rsata oladigan deploy chastotasi grafigi.

## O’z-o’zini tekshirish (haqiqiysi)

O’zingiz egalik qiladigan repozitoriyni oling va unga xotiradan bering:
workflow bilan filtrlangan pipeline, testlangan va hisobot berilgan `test`
stage’i, SHA bo’yicha publish qilingan image, avtomatik deploy qilingan dev
environment va himoyalangan manual gate ortidagi production. Buni shu
yo’nalishni qayta ochmasdan qila olsangiz - u bilan ishingiz tugagan.
