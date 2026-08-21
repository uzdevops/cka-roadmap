## Birinchi `.gitlab-ci.yml`ingiz

`pipeline-basics`da faylni **Pipeline editor** orqali yarating - validatsiya
bepul:

```yaml
stages:
  - build
  - test

build-job:
  stage: build
  script:
    - echo "Compiling the code..."
    - echo "Compile complete."

unit-test-job:
  stage: test
  script:
    - echo "Running unit tests... This will take about 10 seconds."
    - sleep 10
    - echo "Code coverage is 90%"

lint-test-job:
  stage: test
  script:
    - echo "Linting code... This will take about 5 seconds."
    - sleep 5
    - echo "No lint issues found."
```

`main`ga commit qiling. Bir necha soniyada **Build → Pipelines** ishlayotgan
pipeline’ni ko’rsatadi: avval `build-job`, keyin `unit-test-job` va
`lint-test-job` birga. Job’ni bosing. Log shared runner job’ni olganini,
default image’ni tortganini (siz o’rnatmasangiz gitlab.com’da `ruby:3.1` -
shuning uchun keyingi qiladigan ishingiz image o’rnatish), repozitoriyni
klonlaganini va har buyruqni bajarishdan oldin echo qilganini ko’rsatadi.

## Job’ni ataylab yiqiting

Pipeline’lar buzilganda eng yaxshi o’rgatadi. `lint-test-job`ni o’zgartiring:

```yaml
lint-test-job:
  stage: test
  script:
    - echo "Linting..."
    - exit 1
```

Job qizil bo’ladi, *pipeline* qizil bo’ladi, `unit-test-job` baribir o’tadi
(bir stage, mustaqil) va keyingi stage’da hech narsa ishlamaydi. Yiqilgan
job’ni oching: log `ERROR: Job failed: exit code 1` bilan tugaydi.
**Retry** bosing - o’sha commit, yangi job, o’sha natija - chunki retry
job’ni qayta ishga tushiradi, faylni qayta o’qimaydi. Faylni tuzating va
push qiling: *yangi* pipeline.

## Har job’da ishlatadigan buyruqlar

```yaml
explore:
  image: alpine:3.20
  script:
    - pwd                      # /builds/<group>/<project>
    - ls -la                   # repo’ning toza kloni
    - git log -1 --oneline     # bu pipeline’ni ishga tushirgan commit
    - env | grep ^CI_ | sort   # predefined variable’lar (3-hafta)
    - cat /etc/os-release      # siz aslida ishlayotgan image
```

Buni tushunmagan istalgan pipeline’ga joylashtiring. *Men qayerdaman,
menda nima bor, meni kim ishga tushirdi* savollariga besh qatorda javob
beradi.

## O’z-o’zini tekshirish

- YAML’ni tuzatgach yiqilgan job’da Retry bosasiz. Nega u hali ham yiqiladi?
- Yuqoridagi uch job’li pipeline’da `lint-test-job` yiqilganda
  `unit-test-job`ga nima bo’ladi?
