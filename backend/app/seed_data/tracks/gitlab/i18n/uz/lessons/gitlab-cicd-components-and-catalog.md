## Shartnomali `include:`

`include:project` (5-hafta) YAML’ni bo’lishadi, lekin iste’molchi template
qaysi variable’larni kutishini bilmaydi va variable’dagi xato ish vaqtida
yiqiladi. **CI/CD component’lar** yetishmayotgan qismni qo’shadi:
input’larning e’lon qilingan **spec**’iga ega template, **katalog**ga
publish qilingan, versiya bo’yicha include qilinadigan.

## Component yozish

Component loyihasi - shunday tuzilmali oddiy GitLab loyihasi:

```text
ci-components/
├── templates/
│   └── node-test/
│       └── template.yml
└── README.md
```

```yaml
# templates/node-test/template.yml
spec:
  inputs:
    node_version:
      default: "20"
      description: Node.js major version
    stage:
      default: test
    coverage_regex:
      default: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
---
"$[[ inputs.stage ]]-node":
  stage: $[[ inputs.stage ]]
  image: node:$[[ inputs.node_version ]]-alpine
  script:
    - npm ci
    - npm test
  coverage: $[[ inputs.coverage_regex ]]
  artifacts:
    reports: { junit: reports/junit.xml }
```

`---`dan yuqoridagi hamma narsa - shartnoma; pastda **include vaqtida**
almashtiriladigan `$[[ inputs.x ]]`li oddiy pipeline YAML - noma’lum
input’lar va tur mosliksizliklari pipeline *yaratilishini* input’ni
nomlovchi xabar bilan yiqitadi. Loyihani tag’lang (`1.0.0`, `1.1.0`) -
tag’lar - versiyalar.

## Ishlatish

```yaml
include:
  - component: gitlab.com/xyz-team/ci-components/node-test@1.1.0
    inputs:
      node_version: "22"
      stage: verify
```

`@1.1.0` aniq relizni qotiradi; `@~latest` eng yangisiga ergashadi; `@main`
branch’ni kuzatadi (faqat ishlab chiqish uchun). **CI/CD Catalog** yozuvi
(*Settings → General → Visibility → CI/CD Catalog project*) component’ni
*Explore → CI/CD Catalog* ostida README va input’lari render qilingan holda
topiladigan qiladi.

## Input’lar variable emas

| | `spec:inputs` | CI/CD variable’lar |
|---|---|---|
| yechiladi | pipeline yaratilganda, YAML’da | job ishlaganda, shell’da |
| tipli / tekshiriladi | ha (string, number, boolean, array, options) | yo’q |
| job nomlari, stage’lar, rules’ni o’zgartira oladi | ha | yo’q |
| `script:`ga ko’rinadi | faqat siz yozgan joyda | ha, `$VAR` sifatida |

**Tuzilma** uchun input’lar (qaysi stage, qaysi image, nechta shard),
**ish vaqti qiymatlari** uchun variable’lar (hisob ma’lumotlari, host’lar,
toggle’lar).

## XYZ pipeline’ini ko’chirish

5-6 haftalardagi `.node` template, docker-build job va SSH deploy job -
jamoa birinchi publish qiladigan uchta component. Ilovaning
`.gitlab-ci.yml`i `include:` qatorlari plus deploy `rules:`gacha qisqaradi -
va build component’idagi xavfsizlik tuzatishi o’nlab MR emas, versiya
oshirish bilan har loyihaga yetadi.

## O’z-o’zini tekshirish

- `$[[ inputs.x ]]` qachon almashtiriladi va noma’lum input’da nima bo’ladi?
- `@`dan keyingi versiya nimaga ishora qiladi?
- Input’lar qila oladigan, variable’lar qila olmaydigan bitta narsani ayting.
