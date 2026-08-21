## Optimallashtirishdan oldin o’lchang

*Build → Pipelines → pipeline → **Duration** va stage grafi*, trend uchun
*Analyze → CI/CD analytics*. O’qiladigan uchta raqam:

- **umumiy davomiylik** - dasturchilar kutadigan narsa;
- **critical path** - bog’liq job’larning eng uzun zanjiri (Needs ko’rinishi
  ko’rsatadi); boshqa tezlashtirgan hech narsa pipeline’ni qisqartirmaydi;
- har job uchun **navbatda turgan vaqt** - job’lar runner kutsa, yechim
  YAML emas, runner’lar.

## Vositalar, taxminan foyda tartibida

### 1. Kamroq ishlating

`rules:changes`, `workflow:rules` va `interruptible:`:

```yaml
default:
  interruptible: true      # o’sha ref’da yangiroq pipeline bunikining ishlayotgan job’larini bekor qiladi
```

*Settings → CI/CD → General pipelines → Auto-cancel redundant pipelines*ni
yoqing va ketma-ket tez push’lar to’planishni to’xtatadi. Deploy job’larni
`interruptible: false` belgilang - yarim ishlagan deploy sekinidan yomon.

### 2. Tezroq boshlang

`needs:` (2-hafta) - tez job’lar butun stage’ni kutmasin. Odatiy yutuq: lint
va unit testlar endi `build` boshlanishidan oldin 4 daqiqalik integratsion
to’plam tugashini kutmaydi.

### 3. Har job’da kamroq qiling

- bog’liqliklarni cache’lang (`.npm/`, `.m2/`, pip cache) lock fayl key bilan;
- tarix kerak bo’lmagan job’lar uchun `GIT_DEPTH: 1` (sayoz klon);
- faqat artifact iste’mol qiladigan job’lar uchun `GIT_STRATEGY: none`;
- kichik image’lar (`alpine`, `-slim`) va har job’da `apk add` o’rniga
  maxsus image.

```yaml
variables:
  GIT_DEPTH: 1
  FF_USE_FASTZIP: "true"                 # artifact/cache arxivlash tezroq
  ARTIFACT_COMPRESSION_LEVEL: fast
  CACHE_COMPRESSION_LEVEL: fast
```

### 4. Sekin narsani bo’ling

Testlarni bo’laklash uchun `parallel:`; build’lar uchun `parallel:matrix`;
sekin, mustaqil qism uchun **child pipeline** (keyingi dars).

### 5. Tez yiqiling

Arzon tekshiruvlarni birinchi qo’ying va pipeline’ni erta o’ldirishga
ruxsat bering: 10 daqiqalik build’ni to’xtatadigan `.pre`dagi 20 s lint -
har yomon push’da tejalgan daqiqalar. `retry:` faqat infratuzilma
yiqilishlari uchun, hech qachon beqaror testlar uchun emas - testlarni
tuzating.

```yaml
default:
  retry:
    max: 2
    when: [runner_system_failure, api_failure, stuck_or_timeout_failure]
```

## Yozib qo’yishga arziydigan oldin/keyin

```text
oldin: test(4m, kutadi)  → build(3m) → publish(1m) → deploy(1m)   = 9m critical path
keyin: lint 20s ─┐
       unit 1m  ─┼─ needs → build(3m, cache’langan deps 1m) → publish → deploy = ~3.5m
       integ 4m ─┘ (build bilan yonma-yon ishlaydi; faqat deploy’ni bloklaydi)
```

## O’z-o’zini tekshirish

- Qaysi raqam YAML optimallashtirish yoki runner qo’shishni aytadi?
- Deploy job’lar nega `interruptible: false` bo’lishi kerak?
- Job checkout’ini qisqartirishning ikki yo’lini ayting.
