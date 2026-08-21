## Bu yo’nalish nega mavjud

XYZ jamoasi bilan tanishing. Ularda Node.js ilova, bir nechta dasturchi va
bitta muhandisning boshida yashaydigan release jarayoni bor: kodni tortib
olish, testlarni qo’lda ishga tushirish, image yig’ish, serverga ko’chirish,
umid qilish. Har bir release tushdan keyingi butun vaqtni oladi va har
ikkinchi release testlar ushlab qoladigan narsani buzadi - agar kimdir
ularni ishga tushirganida.

Butun yo’nalish qarshi ishlaydigan **muammo bayoni** shu. Oxirida o’sha
jamoada har push’da ishlaydigan, har o’zgarishni testlaydigan, image yig’ib
publish qiladigan, staging’ga o’zi, production’ga esa tugma bilan deploy
qiladigan pipeline bo’ladi - va bularning hammasini bir necha daqiqada, har
safar bir xil tarzda bajaradi.

## CI/CD aslida nimani anglatadi

- **Continuous Integration** - har bir o’zgarish tez-tez merge qilinadi va
  avtomatik tekshiriladi: build, unit testlar, linting, xavfsizlik
  tekshiruvlari. Maqsad - `main` har doim ma’lum-yaxshi holatda bo’lishi.
- **Continuous Delivery** - har bir tekshirilgan o’zgarish *deploy qilsa
  bo’ladigan* holatda: paketlangan, versiyalangan va staging orqali avtomatik
  o’tkazilgan, production’ga qachon yetishini esa inson hal qiladi.
- **Continuous Deployment** - o’sha oxirgi qadamdan ham inson olib tashlanadi:
  `main`dagi yashil pipeline *o’zi* production release.

GitLab CI/CD uchalasini repozitoriyingizdagi bitta fayl bilan qamraydi:

```yaml
# .gitlab-ci.yml - butun pipeline o’zi build qiladigan kod yonida yashaydi
stages: [test, build, deploy]

unit-tests:
  stage: test
  image: node:20-alpine
  script:
    - npm ci
    - npm test
```

Shu faylni commit qiling - GitLab uni ishga tushiradi. Sozlanadigan server
yo’q, alohida konfiguratsiya UI’si yo’q - pipeline ilova kodi kabi
versiyalanadi, review qilinadi va orqaga qaytariladi.

## Yo’nalish qanday qurilgan

| Haftalar | Bosqich | Nimani qila olasiz |
|---|---|---|
| 1-2 | Asoslar | runner, stage, job va artifact’larni tushuntirish, ko’p job’li pipeline yozish |
| 3 | Pipeline konfiguratsiyasi | job’lar *qachon* va *qanday* ishlashini boshqarish: variable’lar, rules, schedule’lar, matrix’lar |
| 4-5 | Continuous integration | XYZ Node.js ilovasini testlash, hisobot berish, build va publish qilish |
| 6 | Continuous deployment | manual gate’lar, review app’lar va Kubernetes bilan environment’larga deploy |
| 7 | Optimallashtirish va xavfsizlik | pipeline’ni tez, modulli va xavfsiz qilish - cache, child pipeline’lar, skanerlash |
| 8 | Runner’lar va Auto DevOps | o’z runner’laringizni ishlatish va GitLab’ga pipeline generatsiya qildirish |

Har hafta: beshta dars, haqiqiy GitLab loyihasida bajariladigan bitta lab
va review quiz. Birinchi kundan GitLab loyihasini ikkinchi tab’da ochiq
tuting - bu yo’nalishdagi har bir YAML parchasi o’qish uchun emas,
joylashtirib ishga tushirish uchun.

## O’z-o’zini tekshirish

- Har biriga bir jumla: continuous delivery va continuous deployment
  orasidagi farq nima?
- GitLab pipeline ta’rifi qayerda yashaydi va bu nega yaxshi?
