## Bitta fayl har doim to’g’ri o’lcham emas

Backend, frontend va docs’li monorepo; tuzilmasi nima o’zgarganiga bog’liq
pipeline; hech kim tahrirlashga jur’at etmaydigan 600 qatorli YAML. Yechim -
**pipeline’larni boshlaydigan pipeline’lar**: o’sha loyihada **child
pipeline’lar**ni ishga tushiradigan parent, yoki boshqa loyihadagi
**multi-project** pipeline.

## Child pipeline’lar

```yaml
# .gitlab-ci.yml (parent)
stages: [triggers]

backend:
  stage: triggers
  trigger:
    include: backend/.gitlab-ci.yml
    strategy: depend                 # parent child’ni kutadi va holatini aks ettiradi
  rules:
    - changes: [ "backend/**/*" ]

frontend:
  stage: triggers
  trigger:
    include: frontend/.gitlab-ci.yml
    strategy: depend
  rules:
    - changes: [ "frontend/**/*" ]
```

Har child - o’z stage’lariga ega to’liq pipeline, parent ostida ichma-ich
ko’rsatiladi (**downstream**). `strategy: depend` parent’ning trigger
job’ini child bilan muvaffaqiyatli yoki yiqilgan qiladi; usiz trigger job
child *boshlangan* zahoti yashil. Variable’lar `trigger:` → `variables:`
yoki `forward:` bilan pastga oqadi; artifact’lar faqat ochiq yuqoriga oqadi
(parent’ning keyingi job’larida `needs:project`/`needs:pipeline`).

## Dinamik child pipeline’lar

Child YAML’i **oldingi job tomonidan generatsiya qilinib** artifact sifatida
uzatilishi mumkin - pipeline o’z pipeline’ini yozadi:

```yaml
generate:
  stage: build
  image: python:3.12-slim
  script:
    - python tools/generate-pipeline.py > generated.yml    # masalan diskdagi har servis uchun bitta job
  artifacts:
    paths: [generated.yml]

run-generated:
  stage: test
  trigger:
    include:
      - artifact: generated.yml
        job: generate
    strategy: depend
```

Servislar, test to’plamlari yoki terraform workspace’lari matrix’i qo’lda
yuritilish o’rniga *ma’lumotdan* boshqarilishi shu.

## Multi-project pipeline’lar

```yaml
deploy-infra:
  stage: deploy
  trigger:
    project: xyz-team/infrastructure
    branch: main
    strategy: depend
  variables:
    APP_IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
```

Downstream loyiha pipeline’i trigger qilgan foydalanuvchi sifatida ishlaydi
(unga u yerda ruxsat kerak) va `APP_IMAGE`ni ko’radi. "Ilova repo’si
platforma repo’siga uzatadi" uchun shuni ishlating; boshqa loyiha job’idan
aniq artifact tortish uchun teskari yo’nalishda `needs:project:`.

## Qaysi birini tanlash

| Ehtiyoj | Ishlating |
|---|---|
| bitta katta faylni qismlarga bo’lish, o’sha repo | `include:`li child pipeline’lar |
| shakl nima o’zgarganiga bog’liq | child + `rules:changes` |
| shakl ish vaqtida topilgan ma’lumotga bog’liq | dinamik child (artifact) |
| boshqa repozitoriyga uzatish | multi-project `trigger:project` |
| yangi pipeline’siz job ta’riflarini qayta ishlatish | `include:` / component’lar (keyingi dars) |

## O’z-o’zini tekshirish

- Trigger job’ga `strategy: depend` qo’shganda nima o’zgaradi?
- Dinamik child pipeline YAML’ini qanday oladi?
- Boshqa loyihadagi downstream pipeline ruxsat xatosi bilan boshlanmaydi - kimning ruxsatlari?
