## Unit test job’i

```yaml
unit-tests:
  stage: test
  image: node:20-alpine
  before_script:
    - node --version && npm --version
    - npm ci --prefer-offline --no-audit --progress=false
  script:
    - npm test
```

Push qiling, job log’ini oching va ikki kun oldingi lokal ishga tushirish
bilan solishtiring:

- `npm ci` aynan lock-fayl daraxtini o’rnatadi. *"npm ci can only install
  packages when your package.json and package-lock.json are in sync"* bilan
  yiqilsa, kimdir `package.json`ni lock’ni yangilamasdan tahrirlagan -
  review’dan oldin ushlangan haqiqiy xato.
- `jest --ci` o’sha `Tests: 6 passed` va coverage jadvalini chiqaradi.
- Job yashil, chunki `npm test` 0 bilan chiqdi.

## Toolchain’ni qotiring

`node:20-alpine` har 20.x relizida suzadi - odatda yaxshi, ba’zan
kutilmagan. Versiya muhim bo’lsa, ayting:

```yaml
default:
  image: node:20.17-alpine3.20
```

va `package.json`da `"engines": { "node": "20.x" }` saqlang - `npm` ular
ajralganda ogohlantiradi.

## Service kerak testlar

XYZ ilovasining unit testlari ma’lumotlar bazasini mock qiladi. Integratsion
testlar yo’q - har test ishga tushirishini sekinlashtirish o’rniga ularni
service’li **ikkinchi** job sifatida qo’shing:

```yaml
integration-tests:
  stage: test
  image: node:20-alpine
  services:
    - name: postgres:16-alpine
      alias: db
  variables:
    POSTGRES_USER: app
    POSTGRES_PASSWORD: app
    POSTGRES_DB: app_test
    DATABASE_URL: postgres://app:app@db:5432/app_test
  before_script:
    - npm ci
    - npm run db:migrate
  script:
    - npm run test:integration
```

Ikkala job `stage: test`da va parallel ishlaydi; ikkalasidan biridagi
yiqilish merge’ni bloklaydi.

## Testni yiqiting, nima bo’lishini kuzating

`tests/app.test.js`da assertion’ni buzing, branch’ga push qiling, MR oching:

- pipeline `unit-tests`da qizil bo’ladi;
- MR **"Pipeline failed"** ko’rsatadi va **Merge** tugmasi o’chirilgan
  ("Pipelines must succeed" yoqiq bo’lsa);
- job log’i Jest yiqilishini ko’rsatadi - lekin qaysi test ekanini topish
  uchun *log’ni ochib, aylantirish* kerak. Ertangi dars o’sha yiqilishni
  MR’ning o’ziga qo’yadi.

Buzilishni qaytaring, push qiling va MR hech kim tegmasdan yashil bo’lishini
kuzating. O’sha sikl - push, qizil, tuzatish, yashil - bu haftaning
mahsuloti.

## Exit kodlar - shartnoma

Job `script`dagi oxirgi buyruq 0 bilan chiqqanda yashil. Ikki tuzoq:

```yaml
script:
  - npm test || true          # HECH QACHON: yiqilishlarni yashiradi
  - npm test; echo done       # echo’ning exit kodi (0) job’niki bo’ladi
```

Yiqiladigan buyruqdan keyin haqiqatan biror narsa ishlatish kerak bo’lsa
`after_script` yoki job’da `allow_failure` ishlating - hech qachon
`|| true` emas.

## O’z-o’zini tekshirish

- `npm ci` `package.json` va lock mos emasligi haqida yiqiladi. Bu CI
  muammosimi yoki ilova muammosi?
- Integratsion testlar nega `unit-tests`ning qismi emas, alohida job?
- Skriptning oxirgi qatori sifatida `npm test; echo done`da nima noto’g’ri?
