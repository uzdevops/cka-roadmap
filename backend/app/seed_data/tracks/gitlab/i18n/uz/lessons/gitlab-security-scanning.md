## Yozmaydigan, include qiladigan skanerlar

GitLab xavfsizlik skanerlarini template sifatida (va yangiroq, component
sifatida) yetkazadi. Birini qo’shish - bitta `include:` qatori; skaner job
GitLab MR’da va loyihaning xavfsizlik sahifalarida render qiladigan hisobot
artifact’i yaratadi.

```yaml
include:
  - template: Jobs/SAST.gitlab-ci.yml                 # manbaning statik tahlili
  - template: Jobs/Secret-Detection.gitlab-ci.yml     # tarixda sizib chiqqan token/kalitlar
  - template: Jobs/Dependency-Scanning.gitlab-ci.yml  # package-lock.json’da ma’lum CVE’lar
  - template: Jobs/Container-Scanning.gitlab-ci.yml   # yig’ilgan image’dagi CVE’lar

container_scanning:
  variables:
    CS_IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"   # hozirgina push qilganingizni skanerlang
  needs: [publish-image]
```

Har template `test` stage’ida (stage’larni qayta nomlagan bo’lsangiz
qo’shing) branch va MR’larda ishlaydigan `rules:`li job’lar yaratadi. Ular
default bo’yicha `allow_failure: true` - **hisobot beradi, bloklamaydi** -
birinchi hafta uchun to’g’ri; bloklash policy’lar bilan keladi.

| Skaner | Nimaga qaraydi | Odatiy topilma |
|---|---|---|
| SAST | manbangiz (til aniqlanadi) | satrlardan yig’ilgan SQL, `eval`, zaif kripto |
| Secret Detection | diff / tarix | "shunchaki test uchun" commit qilingan AWS kalit |
| Dependency Scanning | lock fayllar | `lodash < 4.17.21` prototype pollution |
| Container Scanning | image OS paketlari va kutubxonalari | bazaviy layer’da `openssl` CVE |
| DAST | ishlayotgan URL | aks ettirilgan XSS, yo’q header’lar (environment kerak) |

## Nimani ko’rasiz

- MR vidjeti: **Security scanning** - MR kiritgan yangi zaifliklar, jiddiylik
  va qator / paket / layer’ga havola bilan.
- *Secure → Vulnerability report*: default branch haqida ma’lum hamma narsa,
  triyaj qilinadigan (tasdiqlash, sabab bilan rad etish, issue yaratish).
- `gl-*-report.json` artifact’lari, audit uchun yuklab olinadigan.

## Hisobotlarni gate’larga aylantirish

Uchta kuchayib boruvchi variant:

1. **Merge request approval policy** (*Secure → Policies*): "har qanday
   yangi critical zaiflik @security approval’ini talab qiladi". MR
   bloklanmaydi, lekin o’sha odamsiz merge qila olmaydi.
2. **Scan execution policy**: guruhdagi har loyihada, YAML’i nima desa ham,
   shu skanerlarni majburan ishlatish - skanerlarni fayl tahrirlab olib
   tashlab bo’lmaydi.
3. Qattiq chegara uchun job’ni o’zingiz **yiqiting**:

```yaml
container_scanning:
  allow_failure: false
  variables:
    CS_SEVERITY_THRESHOLD: CRITICAL     # critical topilmalarda yiqil
```

1 va 2 dan boshlang. Bazaviy image’dagi har medium CVE’da yiqiladigan
pipeline - odamlar o’chiradigan pipeline.

## Allaqachon chiqib ketgan sirlar

Secret Detection kalit topgani kalit **buzilgan** degani: avval uni
almashtiring, keyin kerak bo’lsa tarixni qayta yozing. Dasturchilar
repo’laridagi pre-push hook’lar (`gitleaks`) commit mavjud bo’lishidan oldin
to’xtatadi; pipeline skaneri - to’r ostidagi to’r.

## O’z-o’zini tekshirish

- Skaner template pipeline’ga nima qo’shadi va uning merge’ga default ta’siri nima?
- Kimdir include qatorini o’chirsa ham skaner ishlashini qaysi mexanizm kafolatlaydi?
- MR’da sir aniqlandi. Birinchi harakat nima?
