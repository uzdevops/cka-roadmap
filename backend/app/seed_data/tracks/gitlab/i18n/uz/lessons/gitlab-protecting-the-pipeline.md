## Pipeline - production kod

Job loyiha registry’si, variable’lari va unga bergan har qanday hisob
ma’lumotlari bilan ishlaydi. Sirlar bilan ishlaydigan ref’da
`.gitlab-ci.yml`ni o’zgartira oladigan har kim o’sha sirlarni o’qiy oladi.
Quyidagi himoyalar bu jumlani feature branch’lar va begonalar uchun rost
bo’lishidan saqlaydi.

## Himoyalangan ref’lar, himoyalangan variable’lar

- **Himoyalangan branch/tag’lar** (*Settings → Repository*): `main` va `v*`
  - kim push qila oladi (hech kim; MR orqali merge), kim merge qila oladi
  (maintainer’lar).
- **Himoyalangan variable’lar**: har production siri. Faqat himoyalangan
  ref’lardagi job’larga ochiladi. `$PROD_TOKEN`ni chiqaradigan
  feature-branch pipeline bo’sh satr ko’radi.
- **Himoyalangan environment’lar**: kim `production`ga deploy qila oladi,
  talab qilinadigan approval’lar bilan.

Birgalikda: kodning production’ga tega oladigan pipeline’ga yetishining
yagona yo’li - himoyalangan branch’ga review qilingan MR orqali - va sirlar
shungacha u yerda yo’q.

## Token’lar uchun minimal huquq

| Token | Yashaydi | Nima uchun |
|---|---|---|
| `CI_JOB_TOKEN` | bitta job | registry, package registry, API o’qishlari, ruxsat berilgan loyihalar artifact’lari; **Job token permissions** qaysi loyihalar ishlata olishini ro’yxatlaydi |
| project / group **access token** | muddat tugaguncha (qo’ying!) | job token’idan ko’proq kerak avtomatlashtirish, rol (Reporter/Developer) va scope’lar bilan |
| **deploy token** | muddat tugaguncha | klaster yoki serverdan faqat o’qish tortishlari |
| personal access token | inson | pipeline’da hech qachon |

Job token’ini afzal ko’ring; qolganlarini minimal rolga scope’lang; hamma
narsaga muddat qo’ying; kimdir ketganda almashtiring.

## Approval’lar va code owner’lar

- **Merge request approval’lar** (*Settings → Merge requests*): N approval
  talab qilish, yangi commit’larda qayta tiklash, muallifning o’zini
  tasdiqlashini taqiqlash.
- Repo’dagi **`CODEOWNERS`**: `/.gitlab-ci.yml @platform-team` - pipeline’ning
  o’zidagi o’zgarishlar platforma jamoasi approval’ini talab qiladi. Bu
  CI/CD supply-chain xavfiga qarshi yagona eng samarali nazorat.

```text
# CODEOWNERS
/.gitlab-ci.yml       @xyz-team/platform
/ci/                  @xyz-team/platform
/deploy/              @xyz-team/platform @xyz-team/sre
```

## Fork’lar va tashqi hissa qo’shuvchilar uchun pipeline’lar

Fork’ning MR’i pipeline’ini **fork’da**, fork’ning (bo’sh) variable’lari
bilan ishlatadi - sirlaringiz unga hech qachon yetmaydi. Maintainer’lar fork
MR’i uchun parent loyiha runner’larini xohlasa, GitLab diff’ni o’qigandan
keyin aniq tasdiqlashni so’raydi ("Run pipeline"). Buni hech qachon
avtomatlashtirmang.

## Audit

Har variable o’zgarishi, himoyalangan branch o’zgarishi, deploy va token
yaratish **audit events** log’ida (guruh/instance). Har environment uchun
deploy tarixi kim nimani, qachon, qaysi commit uchun bosganini ko’rsatadi.

## XYZ pipeline’i uchun ro’yxat

- [ ] `main` va `v*` himoyalangan; to’g’ridan-to’g’ri push o’chiq
- [ ] production sirlari **himoyalangan** va **environment’ga scope’langan**
- [ ] `production` - approval’li himoyalangan environment
- [ ] `.gitlab-ci.yml` va `ci/` da code owner’lar bor
- [ ] access token’larda muddat va minimal rol; variable’larda personal token yo’q
- [ ] skanerlar faqat include qatorlari emas, guruh policy’si bilan majburlangan

## O’z-o’zini tekshirish

- Feature branch job’i himoyalangan variable’ni echo qiladi. U nimani chiqaradi?
- `.gitlab-ci.yml`dagi `CODEOWNERS` nega xavfsizlik nazorati?
- Fork’ning MR pipeline’i parent loyiha variable’larini nega ko’rmaydi?
