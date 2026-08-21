## Eng oddiy haqiqiy deploy

XYZ jamoasining dev serveri - Docker ishlaydigan bitta Linux VM. Deploy -
SSH orqali kirish, image’ni tortish, container’ni qayta ishga tushirish.
Bu to’rt qator - va atrofida to’g’ri qilinishi kerak bir nechta narsa.

## 1. Hisob ma’lumotlari: File variable sifatida SSH kalit

Mashinangizda deploy kalit yarating, **ochiq** yarmini serverning
`~deploy/.ssh/authorized_keys`ga qo’ying, **maxfiy** yarmini esa **File**
turidagi, *protected* va *mask qilinmagan* (ko’p qatorli kalitni mask qilib
bo’lmaydi - uni himoya va scope qo’riqlaydi) `SSH_PRIVATE_KEY` project
variable’i sifatida saqlang.

```bash
ssh-keygen -t ed25519 -N '' -f deploy_key -C "gitlab-ci xyz-team"
ssh-copy-id -i deploy_key.pub deploy@dev.xyz.example.com
```

`ssh-keyscan dev.xyz.example.com` natijasi bilan `SSH_KNOWN_HOSTS` (File)
ham saqlang - job ko’r-ko’rona qabul qilish o’rniga host’ni **tekshiradi** -
pipeline’dagi `StrictHostKeyChecking=no` - man-in-the-middle deploy hisob
ma’lumotlaringizni oladigan yo’l.

## 2. Job

```yaml
deploy-dev:
  stage: deploy
  image: alpine:3.20
  environment:
    name: dev
    url: http://dev.xyz.example.com:3000
  variables:
    IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
  before_script:
    - apk add --no-cache openssh-client
    - chmod 600 "$SSH_PRIVATE_KEY"                      # File variable = yo’l
    - mkdir -p ~/.ssh && cp "$SSH_KNOWN_HOSTS" ~/.ssh/known_hosts
  script:
    - |
      ssh -i "$SSH_PRIVATE_KEY" deploy@dev.xyz.example.com "
        set -e
        echo '$CI_REGISTRY_PASSWORD' | docker login -u '$CI_REGISTRY_USER' --password-stdin '$CI_REGISTRY'
        docker pull '$IMAGE'
        docker rm -f nodejs-app || true
        docker run -d --name nodejs-app --restart unless-stopped -p 3000:3000 '$IMAGE'
        docker logout '$CI_REGISTRY'
      "
    - sleep 3 && wget -qO- "$CI_ENVIRONMENT_URL/healthz"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

Qo’shtirnoqlarni diqqat bilan o’qing: tashqi `"…"` SSH’dan oldin **job
tomonidan** ochiladi, shuning uchun `$IMAGE` va registry variable’lari
serverga qiymat sifatida yetadi; serverga uzoq umrli token hech qachon
kerak emas - u bitta tortish davomida job token’i bilan login qiladi va
chiqadi.

## 3. Manual gate’lar

Dev har `main` commit’ida deploy bo’ladi. Staging inson kutishi kerak:

```yaml
deploy-staging:
  extends: deploy-dev
  environment: { name: staging, url: https://staging.xyz.example.com }
  variables: { DEPLOY_HOST: staging.xyz.example.com }     # …va ssh qatorida $DEPLOY_HOST ishlating
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
      allow_failure: false        # kimdir bosguncha pipeline’ni shu yerda blokla
```

Pipeline ko’rinishida job ▶ tugmasini ko’rsatadi; environment sahifasi ham.
Kim bosa olishini keyingi darsdagi **himoyalangan environment’lar** hal qiladi.

## Sirlar gigiyenasi ro’yxati

- Kalit - File variable, protected, environment’ga scope’langan.
- Host key tekshiriladi (`known_hosts`), hech qachon `StrictHostKeyChecking=no` emas.
- Server registry’ga job token’i bilan login qiladi, keyin chiqadi.
- Masofaviy skript ichida `set -e` - yiqilgan pull qayta ishga tushirishni to’xtatadi.
- Job `$CI_ENVIRONMENT_URL`ga health check bilan tugaydi.

## O’z-o’zini tekshirish

- Maxfiy kalit nega *File* turidagi variable va `$SSH_PRIVATE_KEY`da nima bor?
- `SSH_KNOWN_HOSTS` nimadan himoya qiladi?
- Qaysi ikki kalit deploy job’ni bloklovchi manual gate’ga aylantiradi?
