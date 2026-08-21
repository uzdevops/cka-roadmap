## Siz yozmagan pipeline

**Auto DevOps** - GitLab saqlaydigan `.gitlab-ci.yml`: tilingizni aniqlaydi,
Cloud Native Buildpacks bilan image yig’adi, testlar, code quality va
xavfsizlik skanerlarini ishlatadi va review app’lar, staging va production
bilan Kubernetes’ga deploy qiladi - **umuman pipeline fayli yo’q**
repozitoriydan. 1-7 haftalarda qo’lda qilgan hamma narsangiz, default
sifatida.

Yoqish: *Settings → CI/CD → Auto DevOps → Default to Auto DevOps pipeline*
(loyiha, guruh yoki instance bo’yicha). Faqat loyihada o’z `.gitlab-ci.yml`i
bo’lmaganda qo’llanadi.

## Generatsiya qilingan pipeline nimalardan iborat

| Stage | Job’lar (qisqartirilgan) | Kerak |
|---|---|---|
| build | `build` - buildpack’lar (yoki bo’lsa Dockerfile’ingiz) → `$CI_REGISTRY_IMAGE` | registry |
| test | `test` (buildpack orqali til testi), `code_quality`, SAST, secret detection, dependency va container scanning, license scanning | - |
| review | `review` - har MR uchun review app, `stop_review` | Kubernetes + agent |
| dast | review app’ga qarshi DAST | review app |
| staging | `staging` (`STAGING_ENABLED` bo’lsa) | Kubernetes |
| canary | `canary` (`CANARY_ENABLED` bo’lsa) | Kubernetes |
| production | `production` - rolling yoki incremental rollout | Kubernetes + domen |
| performance | production’ga qarshi brauzer unumdorligi | - |
| cleanup | MR yopilganda `stop_review` | - |

Klastersiz faqat `build` va `test` stage’i ishlaydi; deploy job’lar
yiqilmaydi, o’tkazib yuboriladi. Klasterni **agent** bilan ulang (6-hafta),
`KUBE_CONTEXT`ni (yoki eski sertifikat integratsiyasini) va
`KUBE_INGRESS_BASE_DOMAIN`ni (masalan klaster ingress’iga wildcard DNS
yozuvli `apps.xyz.example.com`) o’rnating - deploy stage’lari yonadi.

## Talablar, tartibda

1. **Registry** yoqilgan (gitlab.com’da yoqilgan).
2. Ingress controller’li **Kubernetes** klaster; loyihaga `ci_access`li
   agent ulangan.
3. **Bazaviy domen** variable’i `KUBE_INGRESS_BASE_DOMAIN` va wildcard DNS.
4. Ixtiyoriy: har environment uchun birga keladigan PostgreSQL uchun
   `POSTGRES_ENABLED=true` (review app’lar uchun yaxshi, production uchun
   hech qachon), o’z Helm chart’ingizni ishlatish uchun
   `AUTO_DEVOPS_CHART`/`AUTO_DEVOPS_CHART_REPOSITORY`.

## Buildpack’lar va Dockerfile

Repo’da `Dockerfile` bo’lsa Auto DevOps u bilan yig’adi. Aks holda Cloud
Native Buildpacks (`heroku/builder` default) Node/Python/Java/Go/… ni
aniqlaydi va konfiguratsiyasiz image yaratadi - birinchi marta sekin,
keyin ishonchli. `AUTO_DEVOPS_BUILD_IMAGE_EXTRA_ARGS` `--build-arg`lar
uzatadi; `BUILDPACK_URL` aniq buildpack’ni qotiradi.

## Nega muhim va nega hamma narsa uchun emas

Auto DevOps - "bo’sh repo"dan "skanerlar bilan deploy qilingan"gacha eng
tez yo’l - ichki vositalar, prototiplar va platforma guruhi yo’q jamoalar
uchun a’lo. U fikrli: deploy’i - uning Helm chart’i, stage’lari - uning
stage’lari, va ma’lum nuqtadan nariga sozlash (keyingi dars) yana pipeline
saqlayotganingizni anglatadi, faqat o’zingiz boshlamagan. U nimani
generatsiya qilishini bilish - *to’liq* pipeline nimalarni o’z ichiga
olishining eng yaxshi ma’lumotnomasi ham.

## O’z-o’zini tekshirish

- Auto DevOps loyihaga qachon qo’llanadi?
- Deploy stage’lari ishlashidan oldin qaysi ikki narsa mavjud bo’lishi kerak?
- Image buildpack’lar yoki Dockerfile bilan yig’ilishini nima hal qiladi?
