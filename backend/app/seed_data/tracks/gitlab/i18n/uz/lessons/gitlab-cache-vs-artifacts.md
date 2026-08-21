## `npm ci`ni to’rt marta bajarish narxi

4-hafta pipeline’i bog’liqliklarni `lint`, `unit-tests`,
`integration-tests` va `build`da o’rnatadi - o’sha `node_modules`ni to’rt
marta yuklab olish. **Cache** fayllarni job’lar va pipeline’lar orasida
saqlaydi, ikkinchi o’rnatish yuklab olish emas, nusxalash bo’ladi.

```yaml
variables:
  npm_config_cache: "$CI_PROJECT_DIR/.npm"

default:
  cache:
    key:
      files: [package-lock.json]          # har lock-fayl mazmuni uchun bitta cache
    paths:
      - .npm/                             # npm’ning yuklab olish cache’i, node_modules emas
    policy: pull-push

unit-tests:
  script:
    - npm ci --prefer-offline             # avval .npm/ ga uradi
    - npm test
```

Nega `node_modules/` emas, `.npm/`: `npm ci` baribir o’rnatishdan oldin
`node_modules`ni o’chiradi, uni cache’lash hech narsa bermaydi; npm’ning
*yuklab olish* cache’ini cache’lash `npm ci`ni tez va baribir aniq qiladi.

## Muhim kalit so’zlar

| Kalit | Ma’nosi |
|---|---|
| `key:` | satr yoki `files:` (o’sha fayllarning hash’i) - cache key bo’yicha qidiriladi |
| `key:prefix:` | `prefix: $CI_JOB_NAME` + files → lock o’zgarishida baribir yangilanadigan job bo’yicha cache’lar |
| `paths:` | nimani saqlash; loyiha katalogi ichida bo’lishi kerak |
| `policy:` | `pull-push` (default), `pull` (faqat o’qish - faqat iste’mol qiladigan job’larda), `push` (faqat yozish) |
| `fallback_keys:` | asosiy key yo’q bo’lsa shularni sinash (masalan `main-cache`) |
| `untracked: true` | git kuzatmaydigan barcha fayllarni cache’lash |
| `when:` | `on_success` / `on_failure` / `always` - yiqilgan job’dan keyin saqlash-saqlamaslik |

```yaml
install:
  stage: .pre
  script: npm ci
  cache:
    key: { files: [package-lock.json] }
    paths: [.npm/]
    policy: push                 # bu job cache’ni to’ldiradi…

unit-tests:
  cache:
    key: { files: [package-lock.json] }
    paths: [.npm/]
    policy: pull                 # …bular faqat o’qiydi va hech qachon qaytarib yuklamaydi
```

## Cache - imkon qadar

Cache **runner’da** yashaydi (yoki runner shunday sozlangan bo’lsa umumiy
object store’da - gitlab.com SaaS runner’lari shunday). Boshqa runner,
boshqa cache; yangi autoscaled VM’da umuman bo’lmasligi mumkin. Job’ingiz
**bo’sh** cache bilan ishlashi shart - sekinroq, buzilmagan. Qoida:

- **artifact’lar** - to’g’rilik: keyingi job’lar *muhtoj* natijalar;
- **cache** - tezlik: yo’q bo’lsa job qayta yig’a oladigan narsalar.

Yo’q cache job’ni buzsa, sizda cache qiyofasidagi artifact bor.

## Yomon cache’ni tozalash

*Build → Pipelines → Clear runner caches* ichki indeksni oshiradi, har key
yangi deb hisoblanadi. Cache zaharlanganda ishlating (yarim yozilgan
`node_modules`, vosita yangilanishi) - YAML’da key’larni qayta nomlashdan
arzon.

## O’z-o’zini tekshirish

- `npm ci` bilan nega `node_modules/` emas, `.npm/` cache’lanadi?
- Job `policy: pull` o’rnatadi. Oxirida cache’ni yuklaydimi?
- Kerakli fayl cache’da va cache bo’sh bo’lganda job yiqiladi. Dizayn xatosi nima?
