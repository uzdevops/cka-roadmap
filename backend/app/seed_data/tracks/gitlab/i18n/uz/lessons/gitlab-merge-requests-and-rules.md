## Merge request’lar o’ttiz soniyada

**Merge request** (MR) bir branch’ni boshqasiga merge qilishni taklif
qiladi va review shu yerda bo’ladi: diff, muhokama, approval’lar va - biz
uchun - natijasi merge’ni bloklaydigan yoki ruxsat beradigan pipeline.
*Settings → Merge requests → "Pipelines must succeed"* yashil pipeline’ni
talabga aylantiradi - bu continuous integration uchun minimal chegara.

```bash
git switch -c feature/healthcheck
git commit -am "add /healthz endpoint"
git push -u origin feature/healthcheck     # GitLab "create merge request" havolasini chiqaradi
```

Branch push qilish **branch pipeline** ishga tushiradi. MR ochish **merge
request pipeline** ishga tushirishi mumkin (`CI_PIPELINE_SOURCE ==
"merge_request_event"`). Qaysi biri mavjudligini `rules:` bilan hal
qilasiz - hech narsa hal qilmasangiz ikkalasini ham olasiz, ikkilangan
holda. `rules:` tuzatadigan birinchi narsa shu.

## `rules:` - job qachon yaratiladi

`rules:` **pipeline yaratilayotganda** yuqoridan pastga baholanadi;
birinchi mos rule job mavjud bo’lishini va qanday atributlar bilan
bo’lishini hal qiladi. Moslik yo’q → job yaratilmaydi.

```yaml
unit-tests:
  script: npm test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"     # MR pipeline’larda
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH          # va main’da
    # boshqa har qanday push → job yo’q
```

Har rule quyidagilarni tashishi mumkin:

| Kalit | Ma’nosi |
|---|---|
| `if:` | CI/CD variable ifodasi |
| `changes:` | rule faqat commit/MR’da shu yo’llar o’zgargandagina mos keladi |
| `exists:` | …faqat repo’da shunday fayllar bo’lsa |
| `when:` | `on_success` (default), `manual`, `delayed`, `always`, `never` |
| `allow_failure:` | qizil job, yashil pipeline |
| `variables:` | faqat shu rule mos kelganda variable’lar o’rnatish |

```yaml
build-docs:
  script: make docs
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes: [ "docs/**/*", "mkdocs.yml" ]
    - when: never

deploy-prod:
  script: ./deploy.sh prod
  rules:
    - if: $CI_COMMIT_TAG                  # faqat tag’larda…
      when: manual                        # …va faqat inson bosganda
      allow_failure: false                # pipeline shu paytgacha "blocked"

nightly-cleanup:
  script: ./cleanup.sh
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

## Rule’larni runner kabi o’qish

- Rule’lar yuqoridan pastga **yoki** bilan bog’lanadi; bitta rule ichidagi
  shartlar **va** bilan.
- Oxiridagi yalang’och `- when: never` - o’qilishi uchun odat: "fallthrough
  haqida o’yladim" deydi, garchi moslik yo’qligi allaqachon job yo’q degani.
- `allow_failure: false`siz `when: manual` keyingi stage’lar bosishni
  **kutmasdan** ishlashini anglatadi (manual job’larga default bo’yicha
  yiqilishga ruxsat). U bilan pipeline shu job’da to’xtaydi - haqiqiy gate.
- `rules:` va eskiroq `only:`/`except:` bir job’da aralashtirilmaydi. Hamma
  yangi narsa `rules:` ishlatadi.

## To’liq MR’ni biladigan skelet

```yaml
workflow:                      # keyingi dars - lekin shakli mana
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_COMMIT_TAG

stages: [test, build, deploy]

test:
  stage: test
  script: npm test            # MR’larda, main’da va tag’larda ishlaydi (workflow’dan meros)

build:
  stage: build
  script: docker build .
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_COMMIT_TAG

deploy:
  stage: deploy
  script: ./deploy.sh
  rules:
    - if: $CI_COMMIT_TAG
      when: manual
      allow_failure: false
```

## O’z-o’zini tekshirish

- Job’da ikkita rule: `if: A` keyin `if: B`. Pipeline ikkalasiga mos.
  Qaysi biri qo’llanadi?
- `allow_failure` default’ida qoldirilsa `when: manual` *keyingi*
  stage’ga nima qiladi?
- Ochiq MR’li branch’ga push qilasiz. Hech qayerda `rules:` bo’lmasa nechta
  pipeline ishlaydi?
