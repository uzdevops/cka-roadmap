## Ishni tartiblash: stage’lar

Stage’lar - dag’al tartiblash vositasi. Bir stage’dagi job’lar birga
ishlaydi; keyingi stage hammasi muvaffaqiyatli tugaganda (yoki yiqilishga
ruxsat berilganda) boshlanadi.

```yaml
stages:
  - build
  - test
  - package
  - deploy

build:     { stage: build,   script: [ "echo build" ] }
unit:      { stage: test,    script: [ "echo unit" ] }
integ:     { stage: test,    script: [ "echo integration" ] }
package:   { stage: package, script: [ "echo package" ] }
deploy:    { stage: deploy,  script: [ "echo deploy" ] }
```

Pipeline grafi: `build` → (`unit` ‖ `integ`) → `package` → `deploy`. `integ`
yiqilsa, `package` va `deploy` hech qachon boshlanmaydi va pipeline qizil -
keyingi stage oldingilari bajarilganiga va’da.

## `stage` va `stages`

Doimo chalkashtiriladigan ikkita kalit so’z:

- `stages:` (ko’plik, yuqori daraja) **tartibni e’lon qiladi**. Bu ro’yxat.
- `stage:` (birlik, job ichida) **job’ni joylashtiradi** ulardan biriga.

`stage:`i `stages:`da yo’q narsani nomlagan job - konfiguratsiya xatosi, va
pipeline editor buni aytadi. `stage:`siz job `test`ga tushadi - u default
bo’yicha mavjud, lekin `stages:`ni usiz qayta ta’riflamagan bo’lsangizgina.

```yaml
stages: [build, deploy]     # endi "test" yo’q

lint:
  script: echo lint         # XATO: "test" stage’i mavjud emas
```

## Bog’liq job’lar va "bog’liq" nimani anglatadi

"B job A job’ga bog’liq" ikki xil narsani anglatishi mumkin:

1. **Tartib** - B A tugamasdan boshlanmasligi kerak. A oldingi stage’da
   bo’lsa stage’lar buni bepul beradi.
2. **Ma’lumot** - B A yaratgan fayllarga muhtoj. Stage’lar buni bermaydi:
   har job toza klondan boshlanadi. Sizga **artifact’lar** kerak (keyingi dars).

```yaml
compile:
  stage: build
  script:
    - mkdir -p out && echo "binary" > out/app
  artifacts:
    paths: [out/]          # faylni oldinga uzating

test-binary:
  stage: test
  script:
    - test -f out/app      # mavjud, chunki oldingi stage’lar artifact’lari yuklab olinadi
```

`artifacts:` blokini olib tashlang - `test-binary` "No such file" bilan
yiqiladi: tartib hali to’g’ri, ma’lumot yo’q.

## Stage’lar bepul emas

Har bir stage chegarasi - sinxronizatsiya nuqtasi: pipeline keyingisi
boshlanishidan oldin stage’dagi *eng sekin* job’ni kutadi. Har birida bitta
job’li beshta stage - sizdagi har bir parallel runner’ni behuda sarflaydigan
ketma-ket pipeline. Qoida: stage’lar **release bosqichlari** uchun (build,
test, deploy), `needs:` (ikki darsdan keyin) ularning ichidagi **mayda
bog’liqliklar** uchun.

## O’z-o’zini tekshirish

- Job’da `stage:` yo’q. U qayerda ishlaydi va bu qachon buzilishi mumkin?
- Keyingi stage’dagi job oldingisida yaratilgan faylni nega *ko’rmaydi*?
- Ko’p stage’ga ega bo’lishning bitta narxini ayting.
