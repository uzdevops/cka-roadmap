## Akkaunt va loyiha yarating

Bu yo’nalishdagi hamma narsa **gitlab.com**da (SaaS nashri) ishlaydi -
bepul tarif shared runner’lar va o’rganish uchun yetarlidan ortiq oylik
compute kvotasini o’z ichiga oladi. Self-managed GitLab bir xil ishlaydi;
faqat hostname o’zgaradi.

1. <https://gitlab.com/users/sign_up> da ro’yxatdan o’ting, e-mail’ni
   tasdiqlang va ikki bosqichli autentifikatsiyani yoqing (Preferences →
   Account).
2. **Guruh** yarating - masalan `xyz-team` - shunda loyihalar keyinroq
   variable’lar va runner’larni bo’lisha oladi.
3. Uning ichida README’li bo’sh **loyiha** `pipeline-basics` yarating.
4. SSH kalit qo’shing (Preferences → SSH Keys) yoki HTTPS push’lar uchun
   **personal access token** ishlating:

```bash
git clone git@gitlab.com:xyz-team/pipeline-basics.git
cd pipeline-basics
git config user.email you@example.com
```

## Kurs resurslari

KodeKloud kursi har bir YAML va 4-haftadan ishlatiladigan Node.js ilovaga
ega resurslar repozitoriysi bilan keladi. Uni bir marta import qiling -
**Project → New project → Import project → Repository by URL** - shunda u
o’z guruhingiz ostida turadi; tajriba qiladigan loyihadan alohida saqlang.
Asl nusxa tegilmaydi; siz o’z nusxangizni buzasiz.

```text
xyz-team/
├── pipeline-basics      ← 1-3 haftalar uchun qoralama loyiha
├── gitlab-cicd-resources← import qilingan kurs kodi, faqat o’qish uchun
└── nodejs-app           ← siz yetkazib beradigan ilova (4-haftadan)
```

## Pipeline ko’rinadigan ikkita joy

- **Build → Pipelines** har bir pipeline’ni holati, trigger’i (branch,
  merge request, schedule, manual) va davomiyligi bilan ro’yxatlaydi.
- **Build → Jobs** pipeline’lar bo’ylab har bir job’ni ro’yxatlaydi. Birini
  oching - log runner nomini, tortib olingan image’ni, natijasidan oldin
  echo qilingan har bir `script` qatorini ko’rsatadi.

Job log’ini o’qishni erta o’rganing. Birinchi 30 qator u *qayerda*
ishlaganini va *nimadan* boshlaganini aytadi; pipeline savollarining o’ntadan
to’qqiztasiga javob shu yerda.

## Pipeline editor

**Build → Pipeline editor** `.gitlab-ci.yml`ni jonli validatsiya bilan
ochadi: stage’larni chizadigan **Visualize** tab’i, include va
template’lar kengaytirilgandan *keyingi* YAML’ni ko’rsatadigan **Full
configuration** tab’i, va ishga tushirishni simulyatsiya qiladigan
**Validate** tab’i. Bu yo’nalishdagi har bir o’zgarish uchun uni ishlating -
editor’da ushlangan sintaksis xatosi runner daqiqalarini behuda sarflamagan
pipeline demak.

## O’z-o’zini tekshirish

- Loyihalardan oldin nega guruh yaratish kerak?
- Job yiqilganda avval qayerga qaraysiz va log’ning birinchi qatorlari nimani aytadi?
