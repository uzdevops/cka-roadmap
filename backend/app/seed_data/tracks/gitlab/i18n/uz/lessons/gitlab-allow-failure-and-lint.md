## Pipeline’ni yiqitmasdan job’ga yiqilishga ruxsat berish

Ba’zi tekshiruvlar maslahat xarakterida: jamoa hali tozalab ulgurmagan
yangi linter qoidasi, eksperimental test, "bilib qo’yish yaxshi" skan.
Ular ishlashi, hisobot berishi va jamoa yetib olguncha merge’ni
**bloklamasligi** kerak.

```yaml
lint:
  stage: test
  script:
    - npm ci
    - npm run lint
  allow_failure: true
```

Job baribir qizil bo’ladi; pipeline **sariq ogohlantirish** belgisini
ko’rsatadi va o’tgan deb hisoblanadi; keyingi stage’lar ishlaydi. MR
"passed with warnings" deydi. Qarz tozalangach `allow_failure`ni olib
tashlashda qat’iy bo’ling - abadiy maslahat bo’lib qoladigan tekshiruv -
odamlar e’tibor bermaslikni o’rganadigan shovqin.

`allow_failure`ni ma’lum exit kodlarga toraytirish ham mumkin - "muammolar
topildi"ni "vosita buzildi"dan shunday ajratasiz:

```yaml
lint:
  script: npm run lint
  allow_failure:
    exit_codes: [1]           # eslint "problems found" - maslahat…
                              # …boshqa har qanday kod (vosita buzilgan, 2+) job’ni haqiqatan yiqitadi
```

## MR tushunadigan hisobotli ESLint

```yaml
lint:
  stage: test
  script:
    - npm ci
    - npx eslint . --format gitlab --output-file gl-codequality.json
  artifacts:
    when: always
    reports:
      codequality: gl-codequality.json
  allow_failure: true
```

`eslint-formatter-gitlab` o’rnatilgan bo’lsa (`npm i -D
eslint-formatter-gitlab`) `codequality` hisoboti MR vidjetida yangi va
tuzatilgan muammolarni ko’rsatadi, diff esa inline izohlar oladi -
GitLab’ning o’z Code Quality skaneri ishlatadigan mexanizm.

## Sokin tuzoq: `allow_failure` va `needs`

Yiqilishga ruxsat berilgan job’ga `needs:` qiladigan job u **tugashi
bilan, yashil yoki qizil** boshlanadi. Odatda siz xohlagan narsa shu
(gate maslahat) - lekin bunday job yiqilgan job artifact’lari mavjudligiga
jimgina tayanmasligiga ishonch hosil qiling.

## Manual job’larga default bo’yicha yiqilishga ruxsat

```yaml
deploy-prod:
  script: ./deploy.sh prod
  when: manual                     # allow_failure: true ni nazarda tutadi …
  allow_failure: false             # … boshqacha demasangiz: endi pipeline SHU YERDA BLOKLANADI
```

3-haftadagi bu juftlikni eslang; "pipeline’im manual gate’dan nega o’tib
ketdi" savolining eng keng tarqalgani shu.

## Exit kodlar, yana bir bor, his bilan

Pipeline’dagi har vosita GitLab bilan bitta butun son orqali gaplashadi.
Vositalaringizning kelishuvlarini biling:

| Vosita | 0 | 1 | 2+ |
|---|---|---|---|
| `eslint` | toza | muammolar topildi | config / buzilish |
| `jest` | hammasi o’tdi | testlar yiqildi | config xatosi |
| `npm audit` | darajada/undan yuqori muammo yo’q | zaifliklar topildi | - |
| `trivy --exit-code 1` | toza | topilmalar | xato |

`allow_failure:exit_codes`ni shular atrofida loyihalang - "biror narsa
topdi"da maslahat, "vosita ishlay olmadi"da qattiq yiqilish.

## O’z-o’zini tekshirish

- `allow_failure: true`li job yiqiladi. Pipeline qanday rangda va keyingi
  stage’lar ishlaydimi?
- Linter topilmalari maslahat bo’lsin, lekin linter’ning o’zi buzilganda
  yiqilsin - qanday?
- Manual deploy job’i bosilguncha pipeline’ni to’xtatishi kerak. Qaysi ikki
  kalitni o’rnatasiz?
