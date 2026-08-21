## Fayllarni oldinga uzatish

**Artifact’lar** - job tugaganda GitLab’ga yuklaydigan, bir muddat
saqlanadigan va keyingi job’larning ishchi maydoniga yuklab olinadigan
fayllar. Ular bir job natijasi boshqa job kiritmasiga aylanishining
*yagona* rasmiy yo’li.

```yaml
build:
  stage: build
  image: node:20-alpine
  script:
    - npm ci
    - npm run build                 # dist/ yozadi
  artifacts:
    paths:
      - dist/
    expire_in: 1 week

package:
  stage: package
  image: alpine:3.20
  script:
    - ls dist/                      # avtomatik yuklab olingan
    - tar czf app.tgz dist/
  artifacts:
    paths: [app.tgz]
    expire_in: 30 days
```

Bilish kerak:

- `paths:` loyiha ildiziga nisbatan va glob’larni qo’llaydi (`logs/*.log`).
  `exclude:` mosliklarni olib tashlaydi.
- `expire_in:` - `1 hour`, `2 days`, `never`. Branch’dagi har job’ning eng
  oxirgi artifact’i muddatdan qat’i nazar **saqlanadi** (*Settings → CI/CD →
  Artifacts* buni o’chira oladi). Hamma narsaga muddat qo’ying; artifact
  saqlash cheklangan va pullik.
- Default bo’yicha job **oldingi stage’lardagi barcha job’lar**ning
  artifact’larini yuklab oladi. Bu isrof bo’lsa `dependencies:` bilan cheklang:

```yaml
package:
  dependencies: [build]           # faqat build’niki, boshqa hech narsa
```

`dependencies: []` hech narsa yuklab olmaydi.

## `when:` - yiqilgan job’lardan artifact’lar

```yaml
test:
  script: npm test
  artifacts:
    when: always                    # on_success (default) | on_failure | always
    paths: [test-results/]
```

Test log’lari testlar yiqilganda eng qimmatli, `on_success` esa aynan
shularni tashlab yuborardi. Hisobot va log’lar uchun `always` ishlating.

## Yuklab olish va ko’rib chiqish

Har job sahifasida artifact’lari uchun **Browse** va **Download** bor, va
ular URL bo’yicha murojaat qilinadi - `/-/jobs/artifacts/<ref>/download?job=<name>`
namunasi README badge’i yoki hamkasb uchun barqaror "main’ning oxirgi
build’i" havolasini beradi.

```bash
curl --header "PRIVATE-TOKEN: $TOKEN" -L \
  "https://gitlab.com/api/v4/projects/<id>/jobs/artifacts/main/download?job=build" \
  -o dist.zip
```

## Artifact’lar cache emas

| | artifact’lar | cache |
|---|---|---|
| maqsad | **natijalarni** keyingi job’lar / odamlarga uzatish | bog’liqliklarni **qayta yig’ish**ni tezlashtirish |
| kafolatlanganmi? | ha - GitLab’da saqlanadi | yo’q - imkon qadar, runner bo’yicha |
| qamrov | shu pipeline (va yuklab olishlar) | pipeline’lar bo’ylab, key bo’yicha |
| misol | `dist/`, test hisobotlari, paket | `node_modules/`, `.m2/` |

`node_modules/`ni artifact’ga qo’yish "ishlaydi" va har job’da yuzlab
megabayt yuklaydi. 5-hafta cache’ni to’g’ri qamraydi; hozircha artifact’lar
natijalarni tashiydi, boshqa hech narsani.

## O’z-o’zini tekshirish

- 2-stage job’ga 1-stage’dan fayl kerak. Qaysi ikki qator buni amalga oshiradi?
- Testlar yiqilganda test hisobotlaringiz hech qachon chiqmaydi. Qaysi kalit so’z tuzatadi?
- `node_modules/` nega artifact’ga qo’yish uchun noto’g’ri narsa?
