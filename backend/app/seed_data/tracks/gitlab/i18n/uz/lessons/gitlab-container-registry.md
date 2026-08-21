## Har loyihada registry bor

*Deploy → Container Registry*. Manzil bashorat qilinadi -
`registry.gitlab.com/<group>/<project>` - va pipeline uni va qanday login
qilishni allaqachon biladi:

| Variable | Qiymat |
|---|---|
| `CI_REGISTRY` | `registry.gitlab.com` |
| `CI_REGISTRY_IMAGE` | `registry.gitlab.com/xyz-team/nodejs-app` |
| `CI_REGISTRY_USER` | `gitlab-ci-token` |
| `CI_REGISTRY_PASSWORD` | job’ning `CI_JOB_TOKEN`i - faqat job ishlayotganda yaroqli |

```yaml
publish-image:
  stage: publish
  image: docker:27
  services: [ docker:27-dind ]
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
    IMAGE_SHA: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
  before_script:
    - echo "$CI_REGISTRY_PASSWORD" | docker login -u "$CI_REGISTRY_USER" --password-stdin "$CI_REGISTRY"
  script:
    - docker build --pull -t "$IMAGE_SHA" .
    - docker push "$IMAGE_SHA"
    # odamlar uchun harakatlanuvchi tag, faqat ma’no bor joyda
    - |
      if [ "$CI_COMMIT_BRANCH" = "$CI_DEFAULT_BRANCH" ]; then
        docker tag "$IMAGE_SHA" "$CI_REGISTRY_IMAGE:latest" && docker push "$CI_REGISTRY_IMAGE:latest"
      fi
    - |
      if [ -n "$CI_COMMIT_TAG" ]; then
        docker tag "$IMAGE_SHA" "$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG" && docker push "$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG"
      fi
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_COMMIT_TAG
```

Hech qanday token yaratilmadi, saqlanmadi, almashtirilmadi: `CI_JOB_TOKEN`
har job uchun zarb qilinadi va u bilan o’ladi. Job GitLab’ning o’ziga qarshi
qiladigan *hamma narsa* uchun namuna shu - registry, package registry, API,
boshqa loyiha artifact’larini yuklab olish.

## Tag strategiyasi

| Tag | Harakatlanadimi? | Kim ishlatadi |
|---|---|---|
| `:<short-sha>` | hech qachon | deploy job’lar - aniq, commit’gacha kuzatiladi |
| `:<git tag>` (`v1.4.0`) | hech qachon | release eslatmalari, versiyaga rollback |
| `:latest` / `:main` | ha | sinab ko’rayotgan odamlar; deploy job’lar **emas** |

O’zgarmas tag bilan deploy qiling. Ishlayotgan deployment ostida
harakatlangan `:latest` - hech kim yoqtirmaydigan debug sessiyasi.

## Bir marta yig’, ko’p marta ko’tar

`publish`da yig’ib push qiling, keyin har deploy job SHA bo’yicha **o’sha
image’ni tortadi**. Hech qachon har environment uchun qayta yig’mang -
deploy job’idagi qayta yig’ish siz testlagan artifact’dan boshqa artifact.

```yaml
deploy-staging:
  stage: deploy
  image: alpine:3.20
  script:
    - ./deploy.sh staging "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
```

## Boshqa loyihadan yoki tashqaridan tortish

- Boshqa GitLab loyihasining image’i: o’sha loyiha ruxsat bersa `CI_JOB_TOKEN`
  ishlaydi (*Settings → CI/CD → Job token permissions*).
- Docker Hub yoki xususiy registry: `docker login`da ishlatiladigan token’li
  project variable; yoki `DOCKER_AUTH_CONFIG` (JSON `config.json`) - shunda
  **runner** xususiy `image:`/`services:`ni ham torta oladi.

## Tozalash

*Settings → Packages and registries → Cleanup policies*: har image uchun N
tag saqlash, regex’ga mos X’dan eski tag’larni o’chirish, `v.*`ni himoya
qilish. Policy’siz band loyihaning registry’si har SHA bilan abadiy o’sadi.

## O’z-o’zini tekshirish

- Qaysi variable’lar job’ni loyiha registry’siga login qiladi va parol qancha vaqt yaroqli?
- Nega `:latest` emas, SHA bo’yicha deploy?
- Production deploy job’ida image’ni qayta yig’ishda nima noto’g’ri?
