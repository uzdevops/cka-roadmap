## Pod’lar asosan o’zgarmas

Pod bir marta yaratilgach, siz uning faqat qisqa ro’yxatdagi maydonlarini
o’zgartira olasiz:

- `spec.containers[*].image`
- `spec.initContainers[*].image`
- `spec.activeDeadlineSeconds`
- `spec.tolerations` (faqat qo’shish)
- `spec.terminationGracePeriodSeconds` (ba’zi hollarda faqat qisqartirish uchun)
- `metadata` ichidagi label va annotation’lar

Qolgan hamma narsa - resurslar, muhit o’zgaruvchilari, volume’lar, command,
security context, nodeName, yangi konteyner - **o’zgarmas**. Urinib ko’ring,
API server buni o’zi aytadi:

```bash
kubectl edit pod web
# error: pods "web" is invalid: spec: Forbidden: pod updates may not change fields other than
#   `spec.containers[*].image`, `spec.initContainers[*].image`, ...
```

## O’zgarmas maydonni o’zgartirishning ikkita halol usuli

**1. O’zingiz boshqaradigan fayldan o’chirib qayta yarating.**

```bash
kubectl get pod web -o yaml > web.yaml
# web.yaml ni tahrirlang
kubectl replace --force -f web.yaml
# or: kubectl delete pod web $now ; kubectl apply -f web.yaml
```

**2. `kubectl edit` rad etilgan tahriringizni saqlab qo’ysin, keyin uni
majburlang.**

`kubectl edit` rad etilganda, u tahrirlangan nusxangizni saqlab qoladi va
yo’lini chiqaradi:

```
A copy of your changes has been stored to "/tmp/kubectl-edit-1a2b3c.yaml"
error: At least one of apiVersion, kind and name was changed
```

```bash
kubectl replace --force -f /tmp/kubectl-edit-1a2b3c.yaml
```

Natija bir xil va tahrirni qaytadan qilishingiz shart emas. Imtihonda shu
yurish qilinadi.

:::warning
Ikkala holatda ham Pod **o’chiriladi**. Uning IP’si o’zgaradi, emptyDir
volume’lari tozalanadi va agar uni kontroller yaratmagan bo’lsa, siz qayta
yaratmaguningizcha hech kim uni tiklamaydi. Yolg’iz Pod uchun bu -
o’zgarishning narxi. Topshiriqda "Pod’ni o’chirmasdan" deyilmaganini
tekshiring - agar shunday deyilgan bo’lsa, siz o’zgartirmoqchi bo’lgan maydon,
ehtimol, o’zgaruvchan maydonlardan biridir.
:::

## Deployment’lar boshqacha

Deployment’ning Pod shabloni to’liq tahrirlanadi, chunki Deployment ishlab
turgan Pod’larni o’zgartirmaydi - u yangi shablon bilan yangi ReplicaSet
yaratadi va unga o’tadi. Shuning uchun:

```bash
kubectl edit deployment web          # resurs, env, volume - nimani xohlasangiz
kubectl set image deployment/web nginx=nginx:1.27
kubectl set resources deployment/web --limits=memory=512Mi
kubectl set env deployment/web MODE=prod
```

... bularning har biri rollout’ni ishga tushiradi: yangi spec bilan yangi
Pod’lar ko’tariladi, eski Pod’lar ketadi, qo’lda o’chirish umuman yo’q.
`kubectl rollout status deployment/web` buni kuzatib turadi.

Pod shabloni bor har qanday obyekt uchun ham xuddi shunday: ReplicaSet,
DaemonSet, StatefulSet, Job (yaratilgach shabloni o’zgarmas), CronJob.

:::exam-tip
Topshiriqda "X Deployment’ining Pod’lari"ning resurs/env/volume’ini
o’zgartirish so’ralsa, Deployment’ni tahrirlang - hech qachon Pod’larni emas.
Qo’lda tahrirlangan Pod’lar Deployment moslashtirish qilishi bilanoq ustidan
yozib yuboriladi va siz ballni ikki marta yo’qotasiz: bir marta rad etilgan
tahrir uchun, bir marta o’zgarishsiz qaytib kelgan Pod uchun.
:::

## Tez qaror jadvali

| Nimani o’zgartirmoqchisiz | Yalang’och Pod’da | Deployment’da |
|---|---|---|
| image | `kubectl set image pod/...` | `kubectl set image deployment/...` |
| resurslar, env, volume’lar, command | o’chirib qayta yaratish | `kubectl edit deployment` / `set resources` / `set env` |
| label’lar | `kubectl label pod ...` | `kubectl edit` (shablon label’lari baribir selektorga mos kelishi shart) |
| konteyner qo’shish | o’chirib qayta yaratish | `kubectl edit deployment` |

## O’zingizni tekshiring

1. Joyida o’zgartira oladigan uchta Pod maydonini va o’zgartira olmaydigan
   uchtasini ayting.
2. `kubectl edit pod` o’zgarishingizni rad etdi. Eng tez to’g’ri keyingi
   buyruq qaysi?
3. Nega Deployment’ning resurslarini "jonli" o’zgartirsa bo’ladi-yu,
   Pod’nikini bo’lmaydi?
