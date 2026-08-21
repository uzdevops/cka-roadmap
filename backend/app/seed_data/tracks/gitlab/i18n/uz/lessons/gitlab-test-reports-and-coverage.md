## Log qatorlaridan merge request vidjetlarigacha

GitLab tuzilmali test va coverage natijalarini o’qib, ularni **MR’da**
ko’rsata oladi - qaysi test yiqilgani, coverage qanday o’zgargani - hech
kim log ochmasdan. Ikki artifact buni qiladi: **JUnit** hisoboti va
**coverage** hisoboti.

## JUnit test hisoboti

Jest’ga JUnit XML yozadigan reporter kerak:

```bash
npm install --save-dev jest-junit
```

```json
{
  "scripts": {
    "test": "jest --ci --coverage --reporters=default --reporters=jest-junit"
  },
  "jest-junit": { "outputDirectory": "reports", "outputName": "junit.xml" }
}
```

```yaml
unit-tests:
  stage: test
  script:
    - npm ci
    - npm test
  artifacts:
    when: always                       # hisobot testlar YIQILGANDA ENG muhim
    paths:
      - reports/junit.xml
    reports:
      junit: reports/junit.xml
    expire_in: 1 week
```

`artifacts:reports:junit` - sehrli kalit. Keyingi MR pipeline’idan so’ng MR
sahifasi **Test summary** ko’rsatadi - "6 tests, 1 failed" - va bosilsa
yiqilgan testni va xabarini nomlaydi. Pipeline sahifasida har test
davomiyligi bilan **Tests** tab’i paydo bo’ladi.

## Log’dan coverage

Eng oddiy coverage integratsiyasi - job log’i ustidan regular expression.
Jest jadvalida `All files | 92.15 |` qatori bor; GitLab’ga raqam qayerdaligini
ayting:

```yaml
unit-tests:
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
```

Birinchi capture guruhi job coverage’iga aylanadi - job yonida, MR’da
maqsad branch’ga nisbatan delta bilan **"Coverage 92.15%"** sifatida
ko’rsatiladi va README badge’ida ishlatiladi (`/badges/main/coverage.svg`).
*Settings → CI/CD → General pipelines → Test coverage parsing* o’sha
regex’ni loyiha bo’ylab saqlay oladi.

## Diff’dagi coverage

MR diff’ida qator darajasida ajratib ko’rsatish uchun **Cobertura** hisoboti
publish qiling:

```json
{ "jest": { "coverageReporters": ["text", "cobertura"] } }
```

```yaml
unit-tests:
  artifacts:
    reports:
      junit: reports/junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
```

Endi MR diff’i har o’zgargan qatorni test unga tekkan-tegmaganiga qarab
yashil/qizil belgilaydi - testsiz yetkazilgan o’zgarishni ko’rishning eng
tez yo’li.

## Qolganini arxivlang

Odam o’qiydigan HTML hisobotni ham saqlang - reviewer’lar yoqtiradi va job
allaqachon yaratgach hech narsaga tushmaydi:

```yaml
  artifacts:
    paths:
      - reports/
      - coverage/               # lcov-report/index.html ni o’z ichiga oladi
```

Job sahifasidagi **Browse** `coverage/lcov-report/index.html`ni to’g’ri
brauzerda ochadi.

## O’z-o’zini tekshirish

- Qaysi artifact kaliti test natijalarini MR vidjetiga aylantiradi?
- Hisobot artifact’i nega `when: always` ishlatishi shart?
- `coverage:` regex va `coverage_report` orasidagi farq nima?
