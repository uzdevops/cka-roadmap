## Ko’tarish yo’li

```text
main commit ──► deploy-dev (avto) ──► deploy-staging (manual) ──► deploy-prod (manual, himoyalangan)
tag v1.4.0  ───────────────────────► deploy-staging (avto)   ──► deploy-prod (manual, himoyalangan)
```

Bitta image, bir marta yig’ilgan, SHA bo’yicha uchta environment orqali
**ko’tarilgan**. Uchtadan ikkitasi gate’langan; oxirgisi *qo’riqlangan* ham:
faqat ma’lum odamlar tugmani bosa oladi va faqat ma’lum ref’lardan.

## Himoyalangan environment’lar

*Settings → CI/CD → Protected environments*: `production`ni tanlang, **kim
deploy qila olishi**ni tanlang (guruh, rol, aniq foydalanuvchilar) va
ixtiyoriy **talab qilinadigan approval’lar** (job o’ynatilishidan oldin N
kishi deploy’ni tasdiqlashi kerak). Himoyalanmagan branch’dan himoyalangan
environment’ga mo’ljallangan job **bloklanadi** - feature branch pipeline’i
YAML’i shunday degani uchun "production’ga deploy" qila oladigan teshik
yopiladi.

Buni **himoyalangan branch** `main` (*Settings → Repository → Protected
branches*: hech kim to’g’ridan-to’g’ri push qilmaydi, merge’lar yashil
pipeline’li MR talab qiladi) va himoyalangan `v*` tag’lar bilan juftlang.
Himoyalangan variable’lar - production sirlari - keyin faqat o’sha
ref’lardagi pipeline’larga ochiladi.

## Production job

```yaml
deploy-prod:
  extends: .deploy
  environment:
    name: production
    url: https://xyz.example.com
  variables: { DEPLOY_HOST: prod.xyz.example.com }
  resource_group: production
  rules:
    - if: $CI_COMMIT_TAG
      when: manual
      allow_failure: false
```

Production faqat **tag’lardan** deploy bo’ladi - aniq "bu release" harakati,
environment tarixida o’qiy oladigan nom bilan - `main` esa dev va staging’ni
uzluksiz boqadi.

## Rollback va qayta deploy

*Operate → Environments → production* har deploy’ni ro’yxatlaydi. Eskiroq
qatordagi **Rollback** o’sha deploy job’ini **uning** commit’i va image’i
bilan qayta ishlatadi - bu yangi pipeline emas, eskisining qaytarilishi -
o’zgarmas SHA bilan deploy shuning uchun muhim: rollback o’shanda jonli
bo’lgan aynan narsani deploy qiladi.

Boshqa rollback - oldinga: commit’ni revert qiling, pipeline ishlasin. Yomon
o’zgarish kodda bo’lganda uni afzal ko’ring; eski versiya *hozir* kerak
bo’lib, keyin tekshirmoqchi bo’lsangiz tugmani.

## Xavfsizlik klapanlari

| Muammo | Kalit so’z / sozlama |
|---|---|
| production’ga bir vaqtda ikki deploy | `resource_group: production` |
| staging’dan keyin, aytaylik, 10 daqiqa kutishi kerak deploy | `when: delayed` + `start_in: 10 minutes` |
| runner’ni ushlab turgan tiqilgan deploy | `timeout: 15 minutes` |
| noto’g’ri odam play bosishi | himoyalangan environment + approval’lar |
| feature branch’dan deploy | himoyalangan environment + himoyalangan branch/tag’lar |

```yaml
deploy-prod:
  when: delayed
  start_in: 10 minutes          # staging’dan keyin pishish oynasi; UI’dan bekor qilinadi
```

## O’z-o’zini tekshirish

- YAML’ida shunday job bo’lsa ham feature-branch pipeline’i `production`ga deploy qilishini nima to’xtatadi?
- Rollback ishonchli bo’lishi uchun nega o’zgarmas image tag’lar kerak?
- "Production’dan oldin N kishi tasdiqlashi shart"ni odat emas, qoida qiladigan mexanizm qaysi?
