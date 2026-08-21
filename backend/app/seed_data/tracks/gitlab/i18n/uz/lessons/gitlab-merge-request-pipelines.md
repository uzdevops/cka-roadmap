## Branch pipeline va merge request pipeline

Branch’ga push o’sha branch commit’ida **branch pipeline** ishlatadi.
Branch’da ochiq MR bo’lsa GitLab **merge request pipeline** ham ishlatishi
mumkin - `CI_PIPELINE_SOURCE == "merge_request_event"` - u MR’ga xos
variable’larni tashiydi (`CI_MERGE_REQUEST_IID`, maqsad branch,
label’lar…) va natijalari MR’ga biriktiriladi.

3-haftadagi `workflow:rules` bilan MR mavjud bo’lganda branch pipeline
bosiladi, shunda har push MR’da **bitta** pipeline ko’rsatadi. Bu bazaviy
chiziq; ikki takomillashtirish uni yaxshilaydi.

## Merged results pipeline’lar

Oddiy MR pipeline’i **source branch**ni qanday bo’lsa shunday testlaydi.
U yashil bo’lishi mumkin, `main` esa uni buzadigan tarzda oldinga ketgan -
merge keyin qizil bo’lardi. *Settings → Merge requests → Merge options →
Enable merged results pipelines* MR pipeline’ini ichki ref’da source’ni
target’ga merge qilish **natijasi**ga qarshi ishlatadi. O’sha YAML,
o’zgarish kerak emas; `CI_MERGE_REQUEST_EVENT_TYPE` `merged_result` bo’ladi.

## Merge train’lar

Bir nechta MR `main`ga poygalashganda, hatto merged-results ham Merge
bosgan paytingizga eskirgan bo’lishi mumkin. **Merge train** MR’larni
navbatga qo’yadi va har biri uchun pipeline’ni *navbatda undan oldingilar
ustida* ishlatadi; pipeline o’tganda merge avtomatik bo’ladi. O’sha sozlama
ostida yoqing; train’larda ishlashi kerak job
`$CI_MERGE_REQUEST_EVENT_TYPE == "merge_train"`ni tekshiradi.

Deploy job’lar MR pipeline’lari yoki train’larga **tegishli emas** - ular
`main`/tag’larga tegishli. 4-haftadagi `rules:`ni saqlang: hamma joyda test,
`main` va tag’larda build/publish, o’sha yerdan deploy.

## Faqat o’zgargan narsani ishlating

```yaml
unit-tests:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        - "src/**/*"
        - "tests/**/*"
        - package-lock.json
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

MR pipeline’ida `changes:` maqsad branch bilan solishtiriladi, shuning
uchun faqat docs’li MR testlarni halol o’tkazib yuboradi. `main`da u oldingi
commit bilan solishtirardi - shuning uchun ikkinchi rule’da `changes:` yo’q.

## Badge’lar va MR vidjeti, yig’ilgan

Bu haftadagi hamma narsa bitta joyga quyiladi. Sog’lom MR’da endi ko’rasiz:

- pipeline holati va davomiyligi, **Test summary** (JUnit) va **Coverage**
  deltasi (regex / Cobertura) bilan;
- **Code Quality** topilmalari (ESLint hisoboti), diff’da inline;
- merge’dan keyin `main`dan yig’ilgan container image, registry’da;

va README’da:

```markdown
[![pipeline](https://gitlab.com/xyz-team/nodejs-app/badges/main/pipeline.svg)](https://gitlab.com/xyz-team/nodejs-app/-/pipelines)
[![coverage](https://gitlab.com/xyz-team/nodejs-app/badges/main/coverage.svg)](https://gitlab.com/xyz-team/nodejs-app/-/graphs/main/charts)
```

## O’z-o’zini tekshirish

- Merged results pipeline oddiy MR pipeline testlamaydigan nimani testlaydi?
- Deploy job’lar nega merge request pipeline’lardan tashqarida qolishi kerak?
- MR pipeline’ida `changes:` nima bilan solishtiriladi?
