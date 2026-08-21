## Rollout nima

Deployment’ning Pod shablonini o’zgartiring - image’ni, env o’zgaruvchini,
resurs request’ini - va Deployment kontrolleri ishlab turgan Pod’larga
tegmaydi. U yangi shablon bilan **yangi ReplicaSet** yaratadi va replikalarni
eski ReplicaSet’dan yangisiga ko’chiradi. Ana shu ko’chish - rollout, u
qanday sodir bo’lishi esa - **strategiya**.

```bash
kubectl get rs -l app=web
# NAME             DESIRED   CURRENT   READY   AGE
# web-5d4b9c8f7    0         0         0       2d     <- eski, nolga tushirilgan
# web-7c6f9b4d2    3         3         3       1m     <- joriy
```

Har bir rollout eski ReplicaSet’ni nol replika bilan ortda qoldiradi
(`revisionHistoryLimit`’gacha, sukut bo’yicha 10). Bular - sizning rollback
nishonlaringiz.

## Ikkita strategiya

```yaml
spec:
  strategy:
    type: RollingUpdate            # sukut bo'yicha
    rollingUpdate:
      maxSurge: 25%                # rollout paytida kutilgandan ortiq ruxsat etilgan Pod'lar
      maxUnavailable: 25%          # kutilgandan kam bo'lishiga ruxsat etilgan Pod'lar
```

| Strategiya | Xatti-harakati | Qachon ishlatiladi |
|---|---|---|
| **RollingUpdate** | eskilari tushayotganda yangi Pod’lar ko’tariladi, `maxSurge`/`maxUnavailable` doirasida | deyarli har doim - nol uzilish |
| **Recreate** | avval barcha eski Pod’lar o’ldiriladi, keyin yangilari yaratiladi | ilova bir vaqtda ikki versiyani ishlata olmasa (schema lock, yagona yozuvchi) |

`maxSurge: 1, maxUnavailable: 0` - ehtiyotkor rolling sozlama: hech qachon
sig’imdan pastga tushmaydi, ko’pi bilan bitta qo’shimcha Pod.
`maxUnavailable: 100%` va `maxSurge: 0` - amalda Recreate.

## Rollout’ni boshqarish

```bash
kubectl set image deployment/web nginx=nginx:1.27          # odatdagi trigger
kubectl edit deployment web                                # shablondagi har qanday o'zgarish trigger
kubectl apply -f web.yaml

kubectl rollout status deployment/web                      # tugagunicha (yoki qotguncha) kutadi
kubectl rollout history deployment/web
# REVISION  CHANGE-CAUSE
# 1         <none>
# 2         <none>
kubectl rollout history deployment/web --revision=2        # o'sha revision ning shabloni
kubectl rollout pause deployment/web                       # bir necha o'zgarish qiling, keyin
kubectl rollout resume deployment/web
kubectl rollout restart deployment/web                     # yangi ReplicaSet, o'sha shablon: restart
```

`CHANGE-CAUSE` `kubernetes.io/change-cause` annotatsiyasidan to’ldiriladi -
topshiriq tarix o’qiladigan bo’lishini xohlasa, uni o’zingiz
`kubectl annotate deployment web kubernetes.io/change-cause="image 1.27"`
bilan qo’ying.

## Rollback qilish

```bash
kubectl rollout undo deployment/web                        # oldingi revision ga
kubectl rollout undo deployment/web --to-revision=1
kubectl rollout status deployment/web
```

Undo o’zi ham rollout: bir xil strategiya ostida eski ReplicaSet ko’tariladi,
joriysi tushiriladi. Tarix yangi revision raqamini oladi (qaytib borilgan
shablon eng yangi revision bo’lib qoladi), bu birinchi safar odamlarni
chalkashtiradi.

:::exam-tip
Hech qachon tugamaydigan rollout - `rollout status` "1 of 3 updated replicas
are available" da osilib qolgani - yangi Pod’lar Ready bo’lmayotganini
anglatadi: noto’g’ri image tegi (ImagePullBackOff), crash bo’layotgan
konteyner, o’tmayotgan readiness probe. Eski Pod’lar hali ham xizmat
qilyapti, ya’ni ilova ishlamay qolgani yo’q. `kubectl get pods`’ni o’qing,
shablonni tuzating yoki `rollout undo` qiling - shunda u tugaydi.
:::

## Deployment holatini o’qish

```bash
kubectl describe deployment web | grep -E "StrategyType|RollingUpdateStrategy|Replicas:|Conditions" -A1
kubectl get deployment web -o jsonpath='{.spec.strategy}'
kubectl get deployment web
# NAME   READY   UP-TO-DATE   AVAILABLE   AGE
# web    3/3     3            3           5d
```

- **READY** - tayyor Pod’lar / kutilgan son.
- **UP-TO-DATE** - *joriy* shablon bilan ishlayotgan Pod’lar. Rollout paytida
  bu 0 dan kutilgan songacha ko’tariladi.
- **AVAILABLE** - `minReadySeconds` davomida Ready bo’lib turgan Pod’lar.

`3/3` READY, lekin `1` UP-TO-DATE ko’rsatayotgan Deployment rollout
o’rtasida yoki qotib qolgan.

:::tip
`kubectl rollout` DaemonSet va StatefulSet’lar bilan ham ishlaydi (`rollout
status ds/kube-proxy -n kube-system`), ularning o’z strategiya maydonlari
bilan.
:::

## O’zingizni tekshiring

1. Image’ni o’zgartirganingizda Deployment kontrolleri qanday obyekt yaratadi
   va eskisiga nima bo’ladi?
2. `maxSurge: 1, maxUnavailable: 0`’ni bir jumlada tushuntiring va uning
   o’rniga `Recreate`’ni tanlaydigan holatni ayting.
3. `rollout status` besh daqiqadan beri qotib turibdi. Ilova ishlamay
   qoldimi? Nimaga qaraysiz va tez chiqish yo’li qanday?
