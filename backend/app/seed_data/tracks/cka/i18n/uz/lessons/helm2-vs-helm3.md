## Nega eski qo’llanmalarda Tiller tilga olinadi

Helm 2 versiyasining server yarmi bor edi: **Tiller** - `kube-system`dagi
Deployment; Helm klienti u bilan gaplashardi va manifestlarni aslida o’sha
apply qilardi. Tiller siz bergan ruxsatlar bilan ishlardi - odatda
cluster-admin, chunki u hamma uchun hamma narsani o’rnatardi - va o’sha
bitta service account klaster hajmidagi xavfsizlik teshigi edi. Helm 3
(2019-yil noyabr) uni olib tashladi. `helm init`, `tiller`,
`--tiller-namespace` deb yozilgan hamma narsa - bu Helm 2 va u endi yo’q.

| | Helm 2 | Helm 3 |
|---|---|---|
| server komponenti | klasterdagi Tiller | yo’q - CLI API server bilan o’zi gaplashadi |
| ruxsatlar | Tiller’ning service account’i | **sizniki** - sizning kubeconfig va RBAC’ingiz |
| release’ni saqlash | `kube-system`dagi ConfigMap’lar | **release namespace’idagi** Secret’lar |
| release nomlari | klaster bo’ylab yagona | **har bir namespace uchun** yagona |
| `helm init` | majburiy | mavjud emas |
| yangilashlar | 2 tomonlama merge | **3 tomonlama strategic merge** |
| chart bog’liqliklari | `requirements.yaml` | `Chart.yaml` ichida |
| `helm delete` | sukut bo’yicha tarixni saqlardi | `helm uninstall` uni o’chiradi (saqlash uchun `--keep-history`) |
| kutubxonalar, value’lar uchun JSON schema, OCI | yo’q | ha |

## Uch tomonlama merge

Bu siz ko’radigan xatti-harakatni o’zgartiradigan farq. Helm 2 eski chart
chiqishini yangi chart chiqishi bilan solishtirar va farqni apply qilardi.
Agar shu orada kimdir release’ning Deployment’ini `kubectl edit` qilgan
bo’lsa - aytaylik, replika sonini qo’lda oshirgan bo’lsa - Helm 2 buni
bilmasdi va `helm rollback` uni tiklamasdi.

Helm 3 esa **uchta** narsani solishtiradi: oldingi chart chiqishi, yangi
chart chiqishi va **jonli obyekt**. Helm’dan tashqarida qilingan qo’lda
o’zgarish sezib olinadi va upgrade paytida, agar chart o’sha maydonga
tegmagan bo’lsa, saqlanadi, teggan bo’lsa - ustidan yoziladi; rollback
paytida ham jonli holat hisobga olinadi. Bu aynan core-concepts
bosqichidagi `kubectl apply`ning uch tomonlama merge’i ortidagi mantiq.

```bash
kubectl scale deployment my-site-wordpress --replicas=3     # Helm'dan tashqarida
helm upgrade my-site bitnami/wordpress --set someOtherValue=x
kubectl get deployment my-site-wordpress                      # replicas hali ham 3 - Helm 3 o'ziniki bo'lmagan maydonga tegmadi
```

(Helm 2 uni chart’dagi qiymatga qaytargan bo’lardi.)

## Reviziyalar va rollback, Helm 3 uslubida

```bash
helm history my-site
# REVISION  UPDATED                   STATUS      CHART             DESCRIPTION
# 1         Mon Aug 18 10:00:00 2026  superseded  wordpress-22.1.0  Install complete
# 2         Mon Aug 18 11:00:00 2026  superseded  wordpress-22.2.0  Upgrade complete
# 3         Mon Aug 18 11:30:00 2026  deployed    wordpress-22.1.0  Rollback to 1
helm rollback my-site 1
```

Rollback - bu **yangi reviziya** (3), uning mazmuni esa 1-reviziyaniki -
xuddi `kubectl rollout undo` kabi naqsh. Tarix cheklangan
(`--history-max`, sukut bo’yicha 10).

:::warning
Rollback Kubernetes **obyektlarini** tiklaydi - volume’dagi ma’lumotlarni
emas, ma’lumotlar bazasidagi qatorlarni emas. Ma’lumotlar bazasi
chart’ining upgrade’ini rollback qilish eski Deployment va eski image’ni
qaytaradi; agar yangi versiya schema’ni migratsiya qilgan bo’lsa, eski
image ishga tushmasligi mumkin. Helm manifestlarni rollback qiladi;
ma’lumotlarni esa backup qaytaradi.
:::

## Helm 2 versiyasidan migratsiya

`helm-2to3` plagini Helm 2 release’larini joyida konvertatsiya qilardi
(config, repolar, release storage). Buni endi hech kim qilmasligi kerak;
agar Tiller bor klasterga duch kelsangiz, bu klasterga Helm yangilanishidan
ko’proq narsa kerakligining belgisi.

:::exam-tip
Imtihonda Helm 2 bilan bog’liq hech narsa yo’q. Agar topshiriq matnida yoki
namunaviy manifestda Tiller yoki `helm init` tilga olinsa, bu chalg’ituvchi
yoki juda eski README - Helm 3 versiyasida ikkalasi ham yo’q va server
komponentisiz ishlaydigan `helm` - siz ishlatadigan yagona Helm.
:::

## O’zingizni tekshiring

1. Tiller nima edi va uni olib tashlash nega xavfsizlikni yaxshiladi?
2. Helm 3 uch tomonlama merge’da Helm 2 qaramagan nimaga qaraydi va bundan
   qanday xatti-harakat o’zgaradi?
3. `helm rollback` PersistentVolume’dagi ma’lumotlarni tiklaydimi? U nimani
   tiklaydi?
