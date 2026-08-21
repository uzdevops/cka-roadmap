## Loyiha holati yig’ilishi

Uch hafta o’tib XYZ jamoasi pipeline yoza oladi. Endi ularga haqiqiy narsa
uchun pipeline kerak: **Node.js web ilovasi** - bir nechta route’li Express
server, Jest’dagi test to’plami va hali hech kim CI’da ishlatmagan
Dockerfile. Bundan keyin har dars shu ilova ustida ishlaydi; shu hafta
yozadigan YAML’ingiz - jamoa yetkazib beradigan pipeline.

## Ilova, besh daqiqada

```text
nodejs-app/
├── app.js              # Express ilova: /, /healthz, /api/todos route’lari
├── server.js           # app.js’ni $PORT’da ishga tushiradi (default 3000)
├── package.json        # script’lar: start, test, lint, build
├── package-lock.json   # qotirilgan bog’liqliklar daraxti - npm ci unga muhtoj
├── tests/
│   └── app.test.js     # Jest + supertest: route’larga so’rov, tekshiruv
├── Dockerfile
└── .gitlab-ci.yml      # hozircha bo’sh - bu haftaning ishi shu
```

```json
{
  "scripts": {
    "start": "node server.js",
    "test": "jest --ci --coverage",
    "lint": "eslint .",
    "build": "echo 'nothing to compile - static assets are served as-is'"
  }
}
```

## Avval o’z mashinangizda ishlating

Pipeline - qo’lda qiladigan ishingizning skripti. Bir marta qo’lda qiling,
"ishlayapti" qanday ko’rinishini bilasiz:

```bash
git clone git@gitlab.com:xyz-team/nodejs-app.git && cd nodejs-app
node --version                 # ilova package.json "engines"da Node 20 ni qotiradi
npm ci                         # lock fayldan aniq versiyalar
npm test                       # Jest tests/ ni ishlatadi, coverage jadvalini chiqaradi
npm start &                    # :3000 da tinglaydi
curl -s localhost:3000/healthz # {"status":"ok"}
```

Test natijasi qanday ko’rinishiga e’tibor bering - `Tests: 6 passed` qatori
va coverage jadvali - chunki pipeline log’da **o’sha raqamlarni topib**,
hisobotga aylantirishi kerak bo’ladi.

```text
PASS tests/app.test.js
  GET /healthz
    ✓ returns ok (31 ms)
  ...
----------|---------|----------|---------|---------|
File      | % Stmts | % Branch | % Funcs | % Lines |
All files |   92.15 |    83.33 |     100 |   92.15 |
```

## Ilova uchun "CI’ga tayyor" nimani anglatadi

Avtomatlashtirishdan oldin ilovani pipeline’ga yaroqli qiladigan uchta
narsani tekshiring:

1. **Takrorlanadigan o’rnatish** - lock fayl va `npm ci`. Usiz CI sizdan
   biroz boshqacha daraxt o’rnatadi.
2. **Interaktiv bo’lmagan test buyrug’i** - `jest --ci` hech qachon tugma
   bosilishini kutmaydi; brauzer yoki ma’lumotlar bazasi kerak testlar buni
   mashina ta’minlay oladigan tarzda aytadi (3-haftadagi `services:`).
3. **Biror narsani anglatadigan exit kod** - `npm test` test yiqilganda
   nol bo’lmagan kod bilan chiqadi. O’sha exit kod job’ning qizil/yashili
   *o’zi*.

Uchtadan biri yetishmasa, pipeline’dan oldin ilovani tuzating. Pipeline
testlab bo’lmaydigan ilovani testlab bo’ladigan qila olmaydi; u faqat bu
holatni tezroq ayta oladi.

## O’z-o’zini tekshirish

- Pipeline yozishdan oldin ilovani nega lokal ishlatish kerak?
- "CI’ga tayyor" uchta xususiyatdan qaysi birini `jest --ci` beradi?
- Pipeline’da coverage foizi qayerdan keladi?
