## XYZ jamoasining pipeline’i, doskada

YAML’dan oldin - shakl. Jamoa shunga kelishdi:

```text
 push / MR
    │
    ▼
┌─────────┐   ┌──────────────────────┐   ┌────────────┐   ┌───────────────┐
│  test   │ → │  build               │ → │  publish   │ → │  deploy       │
│ lint    │   │  docker build        │   │  image’ni  │   │  dev (avto)   │
│ unit    │   │                      │   │  GitLab    │   │  staging      │
│ coverage│   │                      │   │  registry’ga│  │  prod (manual)│
└─────────┘   └──────────────────────┘   └────────────┘   └───────────────┘
  4-hafta        5-hafta                    5-hafta           6-hafta
```

Yozib qo’yishga arziydigan qarorlar, chunki har biri keyinroq bitta
`rules:` qatori:

| Savol | Javob | Nega |
|---|---|---|
| `test` qayerda ishlaydi? | MR’lar, `main`, tag’lar | har o’zgarish tekshiriladi, boshqa hech narsa isrof bo’lmaydi |
| `build`/`publish` qayerda? | `main` va tag’lar | feature branch’larga image kerak emas |
| `deploy` qayerda? | `main` → dev avtomatik; tag’lar → staging, keyin tugma bilan prod | continuous *delivery*, prod’dan oldin inson bilan |
| Merge’ni nima bloklaydi? | qizil `test` stage’i | "Pipelines must succeed" |
| Image tag nima? | `$CI_COMMIT_SHORT_SHA`, plus `main`da `latest` va tag’larda tag nomi | kuzatiladigan va odam uchun qulay |

## Repozitoriyni import qiling

Ilova kurs resurslarida yashaydi; push’lar *sizning* pipeline’laringizni
ishga tushirishi uchun uni guruhingiz ostiga keltiring:

**New project → Import project → Repository by URL** →
`https://gitlab.com/<course-namespace>/nodejs-app.git` → `xyz-team`da
`nodejs-app` deb nomlang. Keyin klonlang va *Settings → CI/CD → Runners*
ostida shared runner’lar yoqilganini tasdiqlang.

## Shu hafta to’ldiriladigan skelet

```yaml
# .gitlab-ci.yml - XYZ nodejs-app
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS
      when: never
    - if: $CI_COMMIT_BRANCH
    - if: $CI_COMMIT_TAG

default:
  image: node:20-alpine

variables:
  npm_config_cache: "$CI_PROJECT_DIR/.npm"     # cache uchun, 5-hafta

stages:
  - test
  - build
  - publish
  - deploy

lint:
  stage: test
  script: [ "npm ci", "npm run lint" ]

unit-tests:
  stage: test
  script: [ "npm ci", "npm test" ]
```

`test`da ikkita job, ikkalasi bog’liqliklarni o’rnatadi - hozircha ataylab
sekin va takrorlangan. 5-haftaning cache darsi takrorni olib tashlaydi; bu
hafta shu job’lardan **to’g’ri** natijalar va **hisobotlar** olish haqida.

## Odat: pipeline’ni kichik qadamlarda commit qiling

Shu hafta har dars bitta job yoki bitta kalit so’z qo’shadi va push qiladi.
Qirqta kichik, yashil commit to’rt joyda birdan yiqiladigan bitta kattasidan
ko’proq o’rgatadi - va `.gitlab-ci.yml`dagi `git blame` qarorlar
changelog’iga aylanadi.

## O’z-o’zini tekshirish

- `build` va `publish` feature branch’larda nega ishlamaydi?
- Yuqoridagi `workflow:rules` ochiq MR’li branch’ga nima qiladi?
- `npm ci` takrori qayerda va nima bilan hal qilinadi?
