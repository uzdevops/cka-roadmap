## JSON uchun so’rov tili

Har bir `kubectl get ... -o json` - bu JSON hujjat, JSONPath esa undan bitta
qiymatni sug’urib olish uchun mo’ljallangan kichik til. Uni avval oddiy
hujjatda o’rganing; keyingi dars uni kubectl’ga ulaydi.

```json
{
  "car": {
    "color": "blue",
    "price": "$20,000",
    "wheels": [
      {"model": "KDA", "location": "front-right"},
      {"model": "KDB", "location": "front-left"},
      {"model": "KDC", "location": "rear-right"},
      {"model": "KDD", "location": "rear-left"}
    ]
  },
  "bus": {"color": "white", "price": "$120,000"}
}
```

## Dictionary’lar: nuqtalar

```
$.car.color            →  "blue"
$.bus.price            →  "$120,000"
$.car                  →  butun car obyekti
```

`$` - hujjatning ildizi. `.key` esa dictionary ichiga kiradi. So’rov natijasi
har doim mosliklarning **ro’yxati** bo’ladi (`["blue"]`) - bu yerda bitta
moslik, quyida esa ko’p bo’lishi mumkin.

## Ro’yxatlar: kvadrat qavslar

```
$.car.wheels[0]        →  {"model": "KDA", "location": "front-right"}
$.car.wheels[0].model  →  "KDA"
$.car.wheels[*].model  →  ["KDA", "KDB", "KDC", "KDD"]     - * "har bir element" degani
$.car.wheels[0,3]      →  0 va 3-elementlar
$.car.wheels[0:2]      →  0 va 1-elementlar (oxirgisi kirmaydi)
$.car.wheels[-1:]      →  oxirgi element
```

Yuqori darajadagi ro’yxat ustidagi so’rov `$[...]` bilan boshlanadi:

```json
["Apple", "Google", "Microsoft", "Amazon"]
```

```
$[0]                   →  "Apple"
$[1:3]                 →  ["Google", "Microsoft"]
$[*]                   →  hammasi
```

## Filtrlar: qavs ichidagi shartlar

```
$.car.wheels[?(@.location == "rear-right")].model     →  "KDC"
$[?(@ > 40)]                                           →  raqamlar ro'yxatida: 40 dan kattalari
```

`?()` filtrni boshlaydi; uning ichida `@` - "tekshirilayotgan element"
degani. Operatorlar: `==`, `!=`, `>`, `<`, `>=`, `<=`, ba’zi
implementatsiyalarda `in`/`nin` ham bor. `[?(@.location == "rear-right")]`’ni
"location’i rear-right bo’lgan elementlar" deb o’qing.

## Wildcard’lar va birikmalar

```
$.*.color                       →  ["blue", "white"]   - har bir yuqori darajadagi kalitning color'i
$.car.wheels[*].location        →  hamma to'rtta location
$.car.wheels[?(@.model != "KDA")].location
```

## Hammasini birlashtirib

| Nima kerak | So’rov |
|---|---|
| mashinaning rangi | `$.car.color` |
| har bir g’ildirakning modeli | `$.car.wheels[*].model` |
| orqa chap g’ildirakning modeli | `$.car.wheels[?(@.location == "rear-left")].model` |
| ikkinchi g’ildirak | `$.car.wheels[1]` |
| har bir transportning rangi | `$.*.color` |

:::tip
So’rovni yo’l kabi ovoz chiqarib ayting: "ildiz, car, wheels, ularning har
biri, model". Ayta olsangiz, yoza olasiz. Va natija bitta moslik uchun ham
ro’yxat ekanini unutmang - kubectl chiqishi siz uni ochishni
o’rganmaguningizcha ko’pincha shuning uchun `[value]` ko’rinishida bo’ladi.
:::

## O’zingizni tekshiring

1. Avtobusning narxi uchun so’rov yozing.
2. Barcha g’ildiraklarning location’lari uchun so’rov yozing.
3. Location’i `front-left` bo’lgan g’ildirakning modeli uchun so’rov yozing.
