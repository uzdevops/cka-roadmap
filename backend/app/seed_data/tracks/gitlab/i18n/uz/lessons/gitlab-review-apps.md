## Har merge request uchun environment

Reviewer’lar diff’ni yomon o’qiydi, tugmalarni yaxshi bosadi. **Review app**
MR branch’ini o’z URL’li tashlab yuboriladigan environment’ga deploy qiladi,
MR’ga **View app** tugmasini qo’yadi va MR merge yoki yopilganda
environment’ni buzadi. Butun mexanizm - deploy job’dagi uchta kalit so’z va
mos stop job.

```yaml
deploy-review:
  stage: deploy
  extends: .deploy
  variables:
    IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
  script:
    - ./deploy-review.sh up "$CI_ENVIRONMENT_SLUG" "$IMAGE"
  environment:
    name: review/$CI_COMMIT_REF_SLUG            # dinamik: har branch’ga bitta environment
    url: https://$CI_ENVIRONMENT_SLUG.review.xyz.example.com
    on_stop: stop-review                        # qaysi job uni buzadi
    auto_stop_in: 2 days                        # hech kim MR’ni yopmasa ham
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

stop-review:
  stage: deploy
  extends: .deploy
  script:
    - ./deploy-review.sh down "$CI_ENVIRONMENT_SLUG"
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: manual                              # merge/yopishda avtomatik ham ishga tushadi
  variables:
    GIT_STRATEGY: none                          # bu ishlaganda branch yo’q bo’lishi mumkin
```

Tushdan keyingi vaqtni tejaydigan eslatmalar:

- `$CI_COMMIT_REF_SLUG` - DNS’ga xavfsiz branch nomi; `$CI_ENVIRONMENT_SLUG`
  - DNS’ga xavfsiz environment nomi (maks 24 belgi, yagona) - hostname’larda
  ikkinchisini ishlating.
- Stop job’ga `GIT_STRATEGY: none` kerak, chunki u branch o’chirilgandan keyin
  ishlashi mumkin; u checkout’ga muhtoj bo’lmasligi kerak.
- `on_stop` job’lar MR merge/yopilganda yoki environment `auto_stop_in`i
  tugaganda avtomatik ishlaydi.
- Image’ni deploy-review’dan **oldin** yig’ing (MR pipeline’iga
  `publish-image` job ham kerak - `merge_request_event` uchun `rules:` va
  branch’lar bir-birini yozib yubormasligi uchun ref slug’li tag bilan).

## `deploy-review.sh` nima qiladi

Skript platformangizga nima kerak bo’lsa shu: wildcard DNS yozuvi va
hostname bo’yicha marshrutlaydigan reverse proxy’li umumiy review host’da
`docker run -p`; Kubernetes’dagi `review` namespace’ga `helm upgrade --install
review-$SLUG`; shablonlangan manifest’ning `kubectl apply`i. Pipeline’ga
farqi yo’q - unga `up` `$CI_ENVIRONMENT_URL`ni javob beradigan qilishi va
`down` uni olib tashlashi muhim.

```bash
#!/usr/bin/env sh
set -eu
cmd="$1"; slug="$2"; image="${3:-}"
case "$cmd" in
  up)   ssh review-host "docker rm -f $slug 2>/dev/null; docker run -d --name $slug --network web \
          -l traefik.http.routers.$slug.rule=Host\(\`$slug.review.xyz.example.com\`\) $image" ;;
  down) ssh review-host "docker rm -f $slug || true" ;;
esac
```

## Nimaga erishasiz

- MR vidjeti: **View app** → branch, ishlab turgan holda.
- *Operate → Environments* → har ochiq MR uchun bittadan qatorli `review/`
  papkasi, har biri Stop bilan.
- Nol xarajatli tozalash: yopilgan MR’lar o’zlarini tozalaydi; unutilganlar
  muddati tugaydi.

## O’z-o’zini tekshirish

- Stop job’da nega `GIT_STRATEGY: none` o’rnatilgan?
- `auto_stop_in` nimadan himoya qiladi?
- Review hostname’ini qaysi variable tashkil qilishi kerak va nega to’g’ridan-to’g’ri branch nomi emas?
