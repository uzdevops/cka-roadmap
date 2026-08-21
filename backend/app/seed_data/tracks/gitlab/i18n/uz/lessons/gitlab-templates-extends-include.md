## O’sha olti qator, sakkiz marta

Hozirga kelib `nodejs-app/.gitlab-ci.yml` har job’da `image: node:20-alpine`,
cache blokini va `npm ci`ni takrorlaydi. Uchta vosita takrorni olib
tashlaydi, kuch ortib borishida: YAML anchor’lar, `extends`, `include`.

## Yashirin job’lar va `extends`

Nomi `.` bilan boshlanadigan job **ishlamaydi** - bu template. Boshqa
job’lar uni `extends:` bilan meros qiladi (chuqur merge: map’lar
birlashadi, ro’yxatlar almashtiriladi):

```yaml
.node:
  image: node:20-alpine
  cache:
    key: { files: [package-lock.json] }
    paths: [.npm/]
    policy: pull
  before_script:
    - npm ci --prefer-offline

lint:
  extends: .node
  stage: test
  script: npm run lint

unit-tests:
  extends: .node
  stage: test
  script: npm test
  artifacts:
    reports: { junit: reports/junit.xml }
```

`extends` ro’yxat ola oladi (`extends: [.node, .on-mr]`) - keyingilari
oldingilarini bekor qiladi. Nusxa-ko’chirgan bo’lardingiz har narsa uchun
`extends` ishlating; u niyat sifatida o’qiladi ("bu node job").

## Haqiqatan global narsalar uchun `default:`

```yaml
default:
  image: node:20-alpine
  interruptible: true            # yangiroq pipeline boshlansa meni bekor qil (7-hafta)
  retry:
    max: 1
    when: [runner_system_failure, stuck_or_timeout_failure]
```

`default:` kalitni bekor qilmagan har job’ga qo’llanadi. `image`, `retry`,
`interruptible`, `tags` uchun yaxshi; `script` uchun yomon (job’lar juda
turlicha).

## YAML anchor’lar - faqat oddiy YAML kerak bo’lganda

```yaml
.cache-node: &cache-node
  key: { files: [package-lock.json] }
  paths: [.npm/]

unit-tests:
  cache: *cache-node
```

Anchor’lar sof YAML, GitLab faylni ko’rishidan oldin yechiladi va `include`
chegaralaridan o’ta olmaydi. GitLab YAML’ida `extends`ni afzal ko’ring;
anchor’ga faqat butun job bo’lmagan parcha uchun murojaat qiling.

## `include:` - fayllardan yasalgan pipeline’lar

```yaml
include:
  - local: ci/test.yml                      # o’sha repo
  - local: ci/deploy.yml
  - project: xyz-team/ci-templates         # instance’dagi boshqa loyiha
    ref: v2.1.0                            # qotiring!
    file: /templates/docker-build.yml
  - remote: https://example.com/ci/lint.yml
  - template: Security/SAST.gitlab-ci.yml  # GitLab bilan keladi
```

Include qilingan fayllar bitta konfiguratsiyaga birlashtiriladi; pipeline
editor’dagi **Full configuration** tab’i natijani ko’rsatadi - "bu job
qayerdan keladi"ni shu yerda debug qilasiz. Versiyalangan ref’li
template’lar loyihasi (`ci-templates`) - platforma jamoasi yigirma repo’ga
bitta `docker-build` job’ini berib, ularni tasodifan emas, ataylab
yangilashining yo’li. 7-hafta buni tipli input’li **CI/CD component’lar**ga
aylantiradi.

## `!reference` - parchani qayta ishlatish

```yaml
.setup:
  script:
    - echo "setting up"

deploy:
  script:
    - !reference [.setup, script]
    - ./deploy.sh
```

`extends`dan farqli, `!reference` ma’lum kalit qiymatini ro’yxatga
qo’shadi - "shu qatorlarni *va* menikini ishlat" uchun vosita.

## O’z-o’zini tekshirish

- Ikki job `.node`ni extend qiladi; biri o’z `before_script`ini o’rnatadi.
  Template’niki ham ishlaydimi?
- Full configuration tab’i faylning o’zi ko’rsatmaydigan nimani ko’rsatadi?
- `project:` include’da nega `ref:`ni qotirish kerak?
