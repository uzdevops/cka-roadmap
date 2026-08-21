## `workflow:rules` - pipeline qachon yaratiladi

Job darajasidagi `rules:` qaysi job’lar mavjudligini hal qiladi.
`workflow:rules` **pipeline** umuman mavjud bo’lishini hal qiladi - biror
job ko’rib chiqilishidan oldin. Ikkilangan branch+MR pipeline’larini butunlay
to’xtatadigan yagona joy:

```yaml
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"          # MR pipeline’lar: ha
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS           # MR’i bor branch push’i: yo’q
      when: never                                              #   (MR pipeline uni qoplaydi)
    - if: $CI_COMMIT_BRANCH                                    # boshqa branch push’lari: ha
    - if: $CI_COMMIT_TAG                                       # tag’lar: ha
```

Job rule’lari bilan bir xil baholash - birinchi moslik g’olib, `when: never`
yoki moslik yo’qligi **pipeline yo’q** degani va GitLab hech narsa
ko’rsatmaydi - hech kim build qilishni so’ramagan commit uchun siz
xohlaydigan narsa shu.

`workflow:rules` pipeline bo’ylab variable’lar va nom ham o’rnata oladi:

```yaml
workflow:
  name: "$PIPELINE_NAME · $CI_COMMIT_REF_SLUG"
  rules:
    - if: $CI_COMMIT_TAG
      variables: { PIPELINE_NAME: release, DEPLOY_TIER: production }
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      variables: { PIPELINE_NAME: main,    DEPLOY_TIER: staging }
    - when: always
      variables: { PIPELINE_NAME: ci }
```

## Pipeline schedule’lar

*Build → Pipeline schedules → New schedule*: cron ifodasi, maqsad branch
yoki tag va ixtiyoriy variable’lar. Pipeline schedule egasi sifatida,
`CI_PIPELINE_SOURCE == "schedule"` bilan ishlaydi - job "faqat men, faqat
kechasi" deyishi shunday:

```yaml
nightly-e2e:
  script: npm run test:e2e
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule" && $NIGHTLY == "true"

unit-tests:
  script: npm test
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
      when: never                          # tungi ishni bularga sarflamang
    - when: on_success
```

Odatiy qo’llanishlar: tungi end-to-end yoki unumdorlik to’plamlari,
bog’liqliklarni yangilash, eski review environment’larni tozalash, xavfsizlik
yamoqlari kod o’zgarishisiz tushishi uchun bazaviy image’larni haftalik qayta
yig’ish.

Cron schedule’ning vaqt mintaqasida (aniq o’rnating); schedule’larni
to’xtatib turish, **Play** bilan talab bo’yicha ishga tushirish mumkin, va
ularning variable’lari job’da istalgan pipeline variable’i kabi chiqadi.

## Pipeline’ni ataylab o’tkazib yuborish

Ba’zan push hech narsa ishga tushirmasligi kerak - MR’siz branch’da
README’dagi xato tuzatish:

```bash
git commit -m "docs: fix typo [skip ci]"    # yoki [ci skip], commit xabarida
git push -o ci.skip                          # push option, commit xabari o’zgarmaydi
```

Ikkalasi **pipeline yaratmaydi** (kuzatuv uchun ro’yxatda o’tkazilgan
pipeline chiqadi). Tejab ishlating: ishlamagan pipeline - tekshirilmagan
o’zgarish, va "Pipelines must succeed" oxirgi commit’i CI’ni o’tkazib
yuborgan MR’ni bloklaydi.

Tuzilmali muqobil - `rules:changes` - "faqat docs o’zgargan bo’lsa build
ishlatma" - qarorni kimningdir commit xabarida emas, review qilinadigan
YAML’da saqlaydi.

## O’z-o’zini tekshirish

- Ochiq MR’li branch’ga push ikkita pipeline yaratadi. Qaysi to’rtta
  `workflow:rules` qatori buni tuzatadi?
- Job schedule tomonidan boshlanganini qanday biladi?
- `[skip ci]`ning bitta xavfini ayting.
