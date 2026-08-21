## List’ni patch qilish

Containers, env vars, ports, volumes, volumeMounts, tolerations - spec’ning
list bo’lgan qismlariga yana bitta g’oya kerak: **qaysi element ekanini
qanday aytish**. JSON 6902 **indeks**dan foydalanadi; strategic merge esa
elementning **merge key**’idan (ko’pchiligida bu - `name`).

Boshlang’ich nuqta:

```yaml
spec:
  template:
    spec:
      containers:
        - name: api
          image: myapi:1.0
          env:
            - name: MODE
              value: dev
```

## Element maydonini almashtirish

```yaml
# JSON 6902: indeks bo'yicha
- op: replace
  path: /spec/template/spec/containers/0/image
  value: myapi:2.0
```

```yaml
# strategic merge: nom bo'yicha
spec:
  template:
    spec:
      containers:
        - name: api              # merge key - qaysi konteyner
          image: myapi:2.0
```

Strategic shakl tartib o’zgarishiga chidamli; indeksli shakl esa undan
oldin konteyner qo’shilsa buziladi. Nomlarni afzal ko’ring.

## Element qo’shish

```yaml
# JSON 6902: `-` bilan oxiriga qo'shing yoki indeksga kiriting
- op: add
  path: /spec/template/spec/containers/-
  value:
    name: sidecar
    image: fluent-bit:2.2
- op: add
  path: /spec/template/spec/containers/0/env/-
  value: {name: DEBUG, value: "true"}
```

```yaml
# strategic merge: yangi nomni sanang - u oxiriga qo'shiladi
spec:
  template:
    spec:
      containers:
        - name: sidecar
          image: fluent-bit:2.2
```

Konteynerlar `name` bo’yicha birlashgani uchun, nomi aslida yo’q konteyner
**qo’shiladi**; nomi mos kelgani esa **birlashtiriladi**. Xuddi shu narsa
env vars, ports va volumes uchun ham amal qiladi.

## Elementni o’chirish

```yaml
# JSON 6902: indeks bo'yicha - yagona toza usul
- op: remove
  path: /spec/template/spec/containers/1
```

```yaml
# strategic merge: delete direktivasi
spec:
  template:
    spec:
      containers:
        - name: sidecar
          $patch: delete
```

Merge key yonidagi `$patch: delete` o’sha elementni o’chiradi. Bu - yodlab
olishga arziydigan yagona strategic merge direktivasi.

## Butun list’ni almashtirish

```yaml
# strategic merge: list elementi sifatidagi replace direktivasi BUTUN listni almashtiradi
spec:
  template:
    spec:
      containers:
        - name: api
          env:
            - $patch: replace
            - name: MODE
              value: prod
```

`- $patch: replace` elementisiz `MODE` mavjud env list’iga birlashtirilar
va boshqa o’zgaruvchilar saqlanib qolar edi. U bilan esa list aynan patch
aytgan narsaga aylanadi. "butun list’ni almashtir, birlashtirma" degani
uchun JSON 6902 xuddi shu narsani direktivasiz aytadi:

```yaml
- op: replace
  path: /spec/template/spec/containers/0/env
  value:
    - name: MODE
      value: prod
```

## Merge key’i yo’q list’lar

Ba’zi list’lar oddiy satrlardan iborat (`args`, `command`, `finalizers`).
Ularda merge key yo’q, shuning uchun strategic merge butun list’ni
**almashtiradi**; JSON 6902 esa elementlarga indeks bo’yicha murojaat
qiladi:

```yaml
- op: add
  path: /spec/template/spec/containers/0/args/-
  value: --verbose
- op: replace
  path: /spec/template/spec/containers/0/command
  value: ["python", "server.py", "--port", "8080"]
```

:::exam-tip
List’lar uchun amaliy qoidalar: **nomlangan elementni o’zgartirish yoki
qo’shish** → `name` bo’yicha strategic merge; **elementni o’chirish** →
indeks bo’yicha JSON 6902 `remove` (0 dan sanang, avval `kubectl kustomize`
chiqishida tartibni tekshiring) yoki `$patch: delete`; **oddiy satrli
list’lar** → JSON 6902. Har doim `kubectl kustomize | grep -A<n>
containers:` bilan tasdiqlang - indeks xatolari siz qaramaguningizcha
jimgina turadi.
:::

## O’zingizni tekshiring

1. `api` Deployment’iga `log` sidecar konteynerini (image
   `fluent-bit:2.2`) qo’shadigan strategic merge patch’ini yozing.
2. Ikkinchi konteynerni JSON 6902 bilan va strategic merge bilan qanday
   o’chirasiz?
3. Nega strategic merge `args` list’ini birlashtirish o’rniga almashtiradi?
