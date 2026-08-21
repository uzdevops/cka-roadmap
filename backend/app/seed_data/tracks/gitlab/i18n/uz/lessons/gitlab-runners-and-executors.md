## Job’ingizni kim bajaradi

**Runner** - HTTPS orqali GitLab’dan "menga job bormi?" deb so’rab
turadigan, birini olib, bajarib, log’ni qaytarib oqizadigan jarayon -
`gitlab-runner`. GitLab hech qachon runner’ga push qilmaydi; runner tortadi.
Shuning uchun runner ofisingizdagi NAT ortida turib ham gitlab.com’ga
xizmat qila oladi.

Runner’lar uchta scope’dan birida ro’yxatdan o’tkaziladi va job scope’i
loyihani o’z ichiga olgan har bir runner’ga taklif qilinadi:

| Scope | Qayerda ro’yxatdan o’tkazilgan | Odatiy qo’llanish |
|---|---|---|
| **instance** (shared) | butun GitLab instance | gitlab.com SaaS runner’lari; kompaniyangizning default parki |
| **group** | guruh va uning barcha loyihalari | jamoaning o’z mashinalari, repo’lar bo’ylab umumiy |
| **project** | bitta loyiha | maxsus mashina - GPU, litsenziya, deploy host |

gitlab.com’da **shared runner’lar** har loyiha uchun *Settings → CI/CD →
Runners* ostida yoqiladi. Ular har job uchun yaratilib, keyin yo’q
qilinadigan Linux VM’lar (Windows va macOS variantlari ham bor) - runner
taklif qila oladigan eng kuchli izolyatsiya va job hech qachon keyingisi
uchun "biror narsa qoldira olmasligi"ning sababi.

## Executor’lar - job qanday izolyatsiya qilinadi

Runner job *qayerda* taklif qilinishini hal qiladi; uning **executor**’i
job shell’i *qanday* yaratilishini.

| Executor | Job qayerda ishlaydi | Qachon tanlaysiz |
|---|---|---|
| `shell` | runner host’ining o’zidagi shell | bitta mashina, ishonchli job’lar, vositalar allaqachon o’rnatilgan |
| `docker` | `image:`dan yangi container | default - toza, takrorlanadigan, istalgan toolchain |
| `docker+machine` / autoscaler | job uchun yaratilgan VM’dagi container | SaaS runner’lar; katta parklar |
| `kubernetes` | klasterdagi Pod | Kubernetes’ni allaqachon boshqarasiz |
| `ssh`, `virtualbox`, `parallels`, `custom` | masofadagi host / VM / o’z skriptingiz | chekka holatlar |

Executor runner’ning xususiyati, job’niki emas: YAML’dan `docker` so’ray
olmaysiz. Nima *qila olasiz* - va `docker`da qilishingiz shart - bu
**image**’ni tanlash:

```yaml
job-on-node:
  image: node:20-alpine      # bu job shell’i boshlanadigan container
  script: node --version

job-on-python:
  image: python:3.12-slim
  script: python --version
```

`shell` executor’da `image:` e’tiborga olinmaydi va ikkala job ham host’da
qanday `node`/`python` bo’lsa shuni ishlatadi - pipeline self-managed
runner’da gitlab.com’dagidan boshqacha ishlashining eng keng tarqalgan
sababi.

## SaaS arxitekturasi, boshidan oxirigacha

```text
dasturchi ──push──► gitlab.com ──job navbatda──► runner manager (GitLab’niki)
                                                   │ VM yaratadi, docker’ni ishga tushiradi
                                                   ▼
                                            vaqtinchalik VM ── job’ni `image`da ishlatadi
                                                   │ log oqizadi, artifact’larni yuklaydi
                                                   ▼
                                               yo’q qilinadi
```

Shu hafta duch keladigan oqibatlar: katta image’larni tortish har job’da
vaqt oladi (VM yangi → image cache yo’q); `script`da o’rnatilgan hamma
narsa keyingi job’da yo’q; VM’dan chiqadigan tarmoq job uchun "internet".

## O’z-o’zini tekshirish

- `xyz-team` guruhidagi loyihada bitta project runner, guruhda ikkita bor.
  Shared’larni hisobga olmaganda nechta runner uning job’larini ola oladi?
- `image:` `shell` executor’da nega hech narsani o’zgartirmaydi?
- Har SaaS job’da image nega qayta tortiladi?
