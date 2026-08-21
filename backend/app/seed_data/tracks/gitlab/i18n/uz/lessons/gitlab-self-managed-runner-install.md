## Shared runner’lar yetmaganda

XYZ jamoasi o’z runner’ini o’rnatish sabablari: job’lar xususiy tarmoqqa
(dev server, ichki registry) yetishi kerak, SaaS’dagi compute daqiqalari
tugayapti, build’larga GPU yoki katta cache kerak, yoki siyosat kod
birovning VM’ida bajarilmasin deydi. YAML o’zgarmaydi; faqat qayerda
ishlashi.

## `gitlab-runner`ni o’rnating

Linux host’da (Ubuntu/Debian ko’rsatilgan; RPM va binary’lar ham bor):

```bash
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash
sudo apt-get install gitlab-runner
sudo gitlab-runner --version
```

Bu `gitlab-runner` tizim foydalanuvchisi va systemd service yaratadi.
`docker` executor uchun runner’ga **Docker** kerak:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker gitlab-runner
```

## Ro’yxatdan o’tkazing

GitLab’da avval runner’ni yarating - *Settings → CI/CD → Runners → New
project runner* (yoki group / instance) - tag’larni tanlang, xohlasangiz
"run untagged jobs", va **authentication token**’ni (`glrt-…`) nusxalang.
Keyin:

```bash
sudo gitlab-runner register \
  --non-interactive \
  --url https://gitlab.com \
  --token glrt-XXXXXXXXXXXXXXXXXXXX \
  --executor docker \
  --docker-image alpine:3.20 \
  --description "xyz-build-01"
```

Runner bir necha soniyada **online** ko’rinadi. Ro’yxatdan o’tkazish
`/etc/gitlab-runner/config.toml`ga `[[runners]]` blokini yozadi (keyingi
dars); service uni avtomatik oladi.

> Eski oqim - runner’lar orasida bo’lishiladigan *registration* token -
> eskirgan. Har runner’ni UI’da yarating va o’z authentication token’i bilan
> ro’yxatdan o’tkazing; token’ni runner bo’yicha bekor qilishni ham shu
> beradi.

## Tag’lar: job’larni runner’larga yo’naltirish

`docker`, `linux`, `internal` tag’li runner faqat ularning qism to’plamini
so’ragan job’larni oladi ("run untagged" yoqilmagan bo’lsa). Job’lar
`tags:` bilan so’raydi:

```yaml
deploy-dev:
  tags: [internal]            # dev serverni ko’ra oladigan runner’da ishlashi shart
  script: ./deploy.sh dev

unit-tests:
  tags: [docker, linux]       # jamoaning istalgan docker runner’i
  script: npm test
```

Tag’siz job’lar tag’siz ishni qabul qiladigan runner’larga boradi -
gitlab.com’da bu shared park. Xususiy runner’ingizni **tag’langan va
untagged-o’chiq** qiling, aks holda loyihadagi har job unga tushadi.

## Scope va kim ishlata olishi

- **Project runner**: faqat shu loyiha.
- **Group runner**: guruh loyihalari - jamoa uchun odatiy tanlov.
- **Instance runner**: hamma (faqat self-managed GitLab, admin).

Runner’ni **to’xtatib turish** (yangi job olmaydi), loyihasiga **qulflash**
va **himoyalash** (faqat himoyalangan ref’lardan job ishlatadi - production
deploy runner’lari bilan juftlang) mumkin.

## O’z-o’zini tekshirish

- Runner *scope*’i va *tag*’lari orasidagi farq nima?
- Xususiy runner nega tag’siz job’larni qabul qilmasligi kerak?
- Yangi authentication-token ro’yxatdan o’tkazish eski umumiy token’dan nimasi bilan yaxshi?
