## Release vaqt o’tishi bilan

Install, upgrade, nimadir buziladi, rollback, yana upgrade, uninstall:
release’ning hayoti shundan iborat va Helm har bir qadamni raqamlaydi.

```bash
helm install nginx-release bitnami/nginx --version 15.9.0
helm list
# NAME            REVISION  STATUS    CHART         APP VERSION
# nginx-release   1         deployed  nginx-15.9.0  1.25.3
```

## upgrade

```bash
helm upgrade nginx-release bitnami/nginx --version 18.1.0
helm list
# nginx-release   2         deployed  nginx-18.1.0  1.27.0
helm history nginx-release
# REVISION  STATUS      CHART         APP VERSION  DESCRIPTION
# 1         superseded  nginx-15.9.0  1.25.3       Install complete
# 2         deployed    nginx-18.1.0  1.27.0       Upgrade complete
kubectl get pods                         # Deployment rollout'i orqali yangi image'li yangi Pod'lar
```

Helm ikkita render qilingan manifest orasidagi farqni hisoblaydi (jonli
obyektlarni ham hisobga oladi - uch tomonlama birlashtirish) va faqat
o’zgarganini apply qiladi. Yangi image’li Deployment rollout qiladi; yangi
ma’lumotli ConfigMap yangilanadi; chart’dan yo’qolgan obyekt o’chiriladi.

## rollback

```bash
helm rollback nginx-release 1
helm history nginx-release
# 1   superseded   nginx-15.9.0   Install complete
# 2   superseded   nginx-18.1.0   Upgrade complete
# 3   deployed     nginx-15.9.0   Rollback to 1
```

3-reviziya - bu 1-reviziyaning manifestlari bilan yaratilgan yangi reviziya.
Deployment eski image’ga qaytadi; ConfigMap va Service’lar eski mazmuniga
qaytadi.

**Rollback nimani tiklamaydi**: Helm yaratgan Kubernetes obyekti bo’lmagan har
qanday narsani. 15.x dan 16.x ga yangilangan ma’lumotlar bazasi chart’i
o’zining PersistentVolume’idagi ma’lumotni migratsiya qilgan bo’lishi mumkin;
chart’ni rollback qilish eski image’ni qaytaradi, u esa yangi ma’lumot
formatini o’qiy olmaydi. Stateful chart’lar uchun: upgrade’dan oldin backup
qiling va chart’ning upgrade eslatmalarini o’qing.

## Reviziya yozuvi

```bash
helm get manifest nginx-release --revision 2        # 2-reviziya nimani apply qilgan
helm get values nginx-release --revision 1
helm diff revision nginx-release 1 2                 # helm-diff plagini: ikki reviziya orasidagi o'zgarish
kubectl get secrets -l owner=helm,name=nginx-release
# sh.helm.release.v1.nginx-release.v1
# sh.helm.release.v1.nginx-release.v2
# sh.helm.release.v1.nginx-release.v3
```

`--history-max 10` (sukut bo’yicha) oxirgi o’nta reviziyani saqlaydi; undan
eskiroq Secret’lar tozalab yuboriladi.

## hook’lar va testlar

Chart’lar hayot tsiklining ma’lum nuqtalarida Job ishga tushira oladi -
`pre-upgrade` (sxema migratsiyasi), `post-install` (biror joyda ro’yxatdan
o’tish), `pre-delete` (backup). Ular `templates/` ichidagi oddiy manifestlar,
ustiga annotatsiya qo’yilgan:

```yaml
metadata:
  annotations:
    "helm.sh/hook": pre-upgrade
    "helm.sh/hook-weight": "0"
    "helm.sh/hook-delete-policy": hook-succeeded
```

Ishdan chiqqan hook upgrade’ni ham ishdan chiqaradi (`helm history` `failed`
ko’rsatadi; release oldingi reviziyaning obyektlarida qolib ketadi). `helm
test <release>` esa chart’ning `templates/tests/` Pod’larini ishga tushiradi -
har qanday upgrade’dan keyin bajarsa bo’ladigan smoke test.

```bash
helm test nginx-release
helm upgrade nginx-release bitnami/nginx --atomic        # upgrade ishdan chiqsa avtomatik rollback qiladi
helm upgrade nginx-release bitnami/nginx --wait --timeout 3m
```

`--atomic` - production odati: ishdan chiqqan upgrade (hook nosozligi,
`--timeout` ichida Pod’lar hech qachon Ready bo’lmasligi) o’sha buyruqning
o’zida rollback qilinadi.

## uninstall

```bash
helm uninstall nginx-release
helm uninstall nginx-release --keep-history     # reviziya Secret'larini saqlaydi; `helm history` hamon ishlaydi; `helm rollback` tiriltira oladi
helm list -a                                    # tarixi saqlangan, uninstall qilingan release'lar `uninstalled` bo'lib ko'rinadi
```

:::exam-tip
Imtihon odatda kutadigan ketma-ketlik: nomi aytilgan chart versiyasiga
`helm upgrade`, `helm list` / `helm history` bilan tasdiqlash, keyin `helm rollback
<release> <revision>` va yana tasdiqlash. Ball yo’qotadigan ikkita tafsilot:
`-n`’ni unutish va **noto’g’ri reviziya raqamiga** rollback qilish - avval
`helm history`’ni o’qing, keyin CHART ustuni topshiriq aytganiga mos
keladigan reviziyaga rollback qiling.
:::

## O’zingizni tekshiring

1. Install, upgrade va rollback’dan keyin nechta reviziya bor va qaysi biri
   deployed holatda?
2. Rollback nimani tiklaydi va nimani tiklamaydi?
3. Upgrade’da `--atomic` nima qiladi va qaysi holatda uni xohlamaysiz?
