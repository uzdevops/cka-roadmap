## Har bir pipeline’ning shakli

Vosita qanday bo’lmasin, pipeline bir xil g’oya: **event** bilan ishga
tushadigan, **agent** tomonidan qayerdadir bajariladigan, har biri
**job**’lardan iborat **stage**’lar ketma-ketligi. GitLab’da ular shunday
ataladi:

| Tushuncha | GitLab atamasi | Qayerda ta’riflanadi |
|---|---|---|
| ta’rif | `.gitlab-ci.yml` | repozitoriy ildizi |
| birga ishlaydigan job’lar guruhi | `stage` | `stages:` ro’yxati |
| o’z log’iga ega bitta ish birligi | `job` | `script`ga ega istalgan yuqori darajali kalit |
| job’ni bajaradigan mashina | **runner** | loyiha/guruh/instance’ga ro’yxatdan o’tkazilgan |
| trigger | push, merge request, schedule, API, manual | noaniq, `rules:` bilan shakllanadi |

```yaml
stages:
  - build
  - test
  - deploy

compile:
  stage: build
  script: echo "building"

unit:
  stage: test
  script: echo "testing"

lint:
  stage: test
  script: echo "linting"

release:
  stage: deploy
  script: echo "deploying"
```

**Bir stage’dagi job’lar parallel ishlaydi** (yetarli runner bo’sh bo’lsa);
stage oldingisi tugagandagina boshlanadi. `unit` va `lint` yonma-yon
ishlaydi; `release` ikkalasini kutadi. Hammasi GitLab’da rangli
doirachalar grafi - **pipeline ko’rinishi** - sifatida chiqadi va har bir
doiracha job log’ini ochadi.

## Job aslida nima qiladi

Job - runner’dagi shell sessiyasi. `script:` ostidagi har bir qator tartib
bilan bajariladi; birinchi nol bo’lmagan exit kod job’ni yiqitadi. Job’lar
orasida siz ochiq **artifact** sifatida uzatgan narsadan (keyingi dars)
boshqa hech narsa saqlanmaydi - har job repozitoriyning toza
checkout’idan boshlanadi.

```bash
hello:
  script:
    - echo "Running on $(hostname)"
    - ls -la
    - cat README.md | head -5
```

Hozir o’zlashtirib olish kerak bo’lgan uchta narsa - keyinroq "lekin
lokalda ishlagan edi" holatlarining ko’pini shu tushuntiradi:

1. Job **runner’da** ishlaydi - laptopingizda emas, GitLab serverida ham
   emas. Runner’da nima o’rnatilgan bo’lsa, sizda shu bor.
2. Ishchi katalog - pipeline’ni ishga tushirgan commit’dagi repozitoriyning
   **toza klon**i.
3. Job artifact yoki cache ishlatmasangiz oldingi job’lar yoki
   pipeline’larni **eslamaydi**.

## Nega aynan GitLab CI/CD

- Bitta mahsulot: repozitoriy, pipeline, registry, issue tracker va deploy
  environment’lari bitta ruxsat modeli va bitta UI’ni bo’lishadi.
- Pipeline - **Git’dagi oddiy YAML** - merge request’larda review qilinadi,
  branch’larda testlanadi, diff qilinadi, revert qilinadi.
- gitlab.com’da SaaS runner’lar nol sozlash bilan mavjud va o’sha YAML
  o’zingiz host qiladigan runner’larda o’zgarishsiz ishlaydi (8-hafta).

## O’z-o’zini tekshirish

- Ikkita job bir stage’da. Ular ketma-ket ishlaydimi yoki birga?
- Job `/tmp`da fayl yaratadi. Keyingi stage uni o’qiy oladimi? Nega yo’q?
