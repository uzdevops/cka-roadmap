## Stage qadam-baqadamligidan chiqish

Stage’lar har job’ni oldingi stage’ning eng sekin job’ini kutishga majbur
qiladi. `needs:` bilan job *aynan* qaysi job’larga bog’liqligini e’lon
qiladi va ular tugashi bilan boshlanadi - stage’dan qat’i nazar. Pipeline
**yo’naltirilgan atsiklik graf**ga (DAG) aylanadi.

```yaml
stages: [build, test, deploy]

build-api:   { stage: build, script: [ "sleep 5;  echo api" ] }
build-web:   { stage: build, script: [ "sleep 60; echo web" ] }

test-api:
  stage: test
  needs: [build-api]              # 60 s emas, 5 s dan keyin boshlanadi
  script: echo testing api

test-web:
  stage: test
  needs: [build-web]
  script: echo testing web

deploy:
  stage: deploy
  needs: [test-api, test-web]
  script: echo deploy
```

`needs`siz `test-api` `build-web`ni kutib bir daqiqa bekor turardi. U bilan
pipeline’ning API yarmi web build kompilyatsiyani tugatmasidan tayyor.

## `needs` artifact’larni ham boshqaradi

`needs:`li job artifact’larni **faqat o’zi muhtoj job’lardan** yuklab oladi
(har oldingi stage’dan emas). Bog’liqlik bo’yicha o’chiring:

```yaml
deploy:
  needs:
    - job: build-api
      artifacts: true         # default
    - job: lint
      artifacts: false        # faqat tartib, yuklab olish yo’q
```

## Ixtiyoriy needs

Muhtoj job ma’lum pipeline’da mavjud bo’lmasa (chunki `rules:` uni chiqarib
tashlagan), pipeline **yaroqsiz** - agar bog’liqlik ixtiyoriy demasangiz:

```yaml
deploy:
  needs:
    - job: integration-tests
      optional: true           # bu safar job yaratilmagan bo’lsa ham yaxshi
```

## DAG’ni o’qish

Pipeline sahifasida stage ko’rinishi yonida **Needs** ko’rinishi bor; u
haqiqiy bog’liqlik grafini chizadi. Sog’lom DAG’ning ikki belgisi:

- hech bir job o’zi o’qimaydigan narsani kutmaydi;
- critical path (eng uzun zanjir) eng sekin job zanjiringiz haqiqatan
  talab qilganidek qisqa.

## `needs`ni qachon ishlatmaslik

- Tartib haqiqatan "N stage’dagi hamma narsa N+1 stage’dagi har narsadan
  oldin" bo’lganda - har testning o’tganini ko’rishi shart bo’lgan deploy.
  Stage’lar buni bir qatorda aytadi; `needs` har job’ni ro’yxatlashni talab qilardi.
- Job’lar dinamik yaratilganda (matrix, child pipeline’lar) va ro’yxat
  eskirib qoladigan bo’lsa.

Aralashtirish normal: release bosqichlari uchun stage’lar, ular ichida tez
narsalar birinchi ketishi uchun `needs:`.

## O’z-o’zini tekshirish

- `test-api`da `needs: [build-api]` bor. U hali ham `build` *stage’i*
  tugashini kutadimi?
- `needs:`li job - default bo’yicha kimning artifact’larini yuklab oladi?
- rules bilan chiqarilgan job’ga `needs:` butun pipeline’ni nega buzishi
  mumkin va buni qanday oldini olasiz?
