## Manifestga tegmasdan image’ni o’zgartirish

Muhitlar orasidagi eng keng tarqalgan farq - image tegi: `dev` `main`’ni
ishlatadi, `prod` esa `2.1.0`’ni. `images` transformer’i barcha resurslardagi
har bir konteyner va initContainer ichidagi image havolalarini o’zgartiradi
va moslikni image **nomi** bo’yicha topadi.

```yaml
# base/deployment.yaml
containers:
  - name: web
    image: nginx:1.25
```

```yaml
# overlays/prod/kustomization.yaml
resources: [../../base]
images:
  - name: nginx                 # `image: nginx:<anything>`'ga mos keladi - nom qismi, konteyner nomi emas
    newTag: "1.27.1"
```

```bash
kubectl kustomize overlays/prod | grep image:
#   image: nginx:1.27.1
```

## Uchta maydon

```yaml
images:
  - name: nginx
    newName: registry.example.com/mirror/nginx     # repozitoriyni o'zgartiradi
    newTag: "1.27.1"                               # tegni o'zgartiradi
  - name: myapp
    digest: sha256:4f3e2a...                       # teg o'rniga digest bilan qotiradi
```

| Maydon | `image: nginx:1.25`’ga ta’siri |
|---|---|
| `newTag: "1.27.1"` | `nginx:1.27.1` |
| `newName: registry.example.com/nginx` | `registry.example.com/nginx:1.25` |
| ikkalasi | `registry.example.com/nginx:1.27.1` |
| `digest: sha256:...` | `nginx@sha256:...` (teg tushib qoladi) |

`name` - bu **manifestlarda qanday yozilgan bo’lsa, o’shandagi** image nomi
(tegsiz). Uni konteynerning `name:` maydoni bilan chalkashtirish oson - ular
bir-biriga aloqador emas. `newTag` - string; raqamga o’xshash teglarni
qo’shtirnoqqa oling (`"1.27"`), aks holda YAML uni raqam deb o’qiydi.

## Nega bu ish uchun patch’dan yaxshiroq

Patch uchun konteynerga yo’l kerak bo’lardi: `/spec/template/spec/containers/0/image`
- har bir Deployment uchun, har bir konteyner indeksi uchun. `images` esa
image nomining har bir resursdagi har bir ishlatilishini topadi, keyin
qo’shganlaringizni ham. Har bir image uchun bitta qator, uni nechta
Deployment ishlatishidan qat’i nazar.

## Registry mirror bilan yoki butunlay boshqa nom bilan

```yaml
images:
  - name: docker.io/library/postgres
    newName: harbor.corp/cache/postgres
```

`newTag`’siz `newName` original tegni saqlab qoladi - butun overlay’ni ichki
mirror’ga aynan shu tarzda yo’naltirish mumkin.

## Pipeline ichida

```bash
kustomize edit set image nginx=nginx:1.27.2                  # joriy katalogdagi kustomization.yaml'ni tahrirlaydi
kustomize edit set image myapp=registry.example.com/myapp:$GIT_SHA
git commit -am "deploy $GIT_SHA" && git push                 # GitOps uni ilib oladi
```

`kustomize edit set image` `images` yozuvini siz uchun yozadi - CI shablonsiz
versiyani ko’taradigan odatiy yo’l.

:::exam-tip
"Bu overlay’dagi Deployment’larning image’ini X:Y ga o’zgartiring" - bu
`images` yozuvi, patch emas. `kubectl kustomize | grep image:` bilan
tasdiqlang. Agar manifestlar image’ga registry prefiksi bilan murojaat qilsa,
`name` uni aynan o’sha ko’rinishda o’z ichiga olishi kerak (`nginx` emas,
`registry.k8s.io/nginx`), aks holda hech narsa mos kelmaydi - Kustomize esa
hech narsaga mos kelmagan `images` yozuvi haqida ogohlantirmaydi.
:::

## O’zingizni tekshiring

1. `images: [{name: nginx, newTag: "2"}]`’da `name` nima bilan solishtiriladi
   - konteyner nomi bilanmi yoki image nomi bilanmi?
2. `postgres:16`’ni `harbor.corp/postgres:16`’ga ko’chiradigan yozuvni yozing.
3. Uchta Deployment ishlatadigan tegni o’zgartirish uchun nega `images` patch’dan
   yaxshiroq?
