## Qismlar va ular qanday bog’lanadi

```
 helm CLI ──reads──▶ chart (from a repo, an OCI registry, or a local dir)
          ──reads──▶ values (chart defaults + your overrides)
          ──renders─▶ manifests
          ──applies─▶ API server ──▶ objects in a namespace
          ──records─▶ release Secret (sh.helm.release.v1.<name>.v<N>) in that namespace
```

| Komponent | U nima |
|---|---|
| **helm** | CLI; hamma narsa shu yerda sodir bo’ladi |
| **chart** | paket (keyingi dars) |
| **repository** | HTTP ortidagi `index.yaml` va `.tgz` chart’lar - yoki OCI registry |
| **values** | parametrlar: chart ichidagi `values.yaml` standartlari, ustiga sizdan `-f` fayllar va `--set` flaglar |
| **release** | chart’ning nomlangan, versiyalangan o’rnatmasi |
| **release secret** | Helm’ning o’z yozuvi: render qilingan manifestlar va value’lar, base64+gzip, har bir reviziya uchun bittadan |
| **hooks** | hayot tsiklining ma’lum nuqtasida ishlashi uchun annotatsiyalangan manifestlar (`pre-install`, `post-upgrade`, `test`) |

## Repozitoriylar

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
cat ~/.config/helm/repositories.yaml          # `repo add` nima yozgani
helm repo update
helm search repo bitnami/nginx --versions     # indeksdagi har bir chart versiyasi
helm pull bitnami/nginx --untar               # ichini ko'rish uchun chart'ni yuklab olish
```

Repozitoriy - bu statik fayllar: chart nomlari, versiyalari va `.tgz`
URL’larini sanab beruvchi `index.yaml`. GitHub Pages, S3 bucket, Nexus yoki
Harbor nusxasi - fayl uzatadigan har qanday narsa Helm repo bo’la oladi.
`helm repo update` indeksni yuklab oladi; usiz siz eskirgan nusxa ichida
qidirasiz.

## Release’lar va reviziyalar

```bash
helm install web bitnami/nginx -n apps --create-namespace
helm install web2 bitnami/nginx -n apps           # bir xil chart, ikkinchi release
helm list -n apps
# NAME  NAMESPACE  REVISION  STATUS    CHART         APP VERSION
# web   apps       1         deployed  nginx-18.1.0  1.27.0
# web2  apps       1         deployed  nginx-18.1.0  1.27.0
helm status web -n apps
helm get values web -n apps                       # siz bergan value'lar
helm get values web -n apps --all                 # chart standartlari bilan birga
helm get manifest web -n apps                     # Helm apply qilgan YAML
helm history web -n apps
```

Odamlar chalkashtiradigan ikkita ustun: **CHART** versiyasi (`nginx-18.1.0`,
paketning o’zi) va **APP VERSION** (`1.27.0`, ichidagi nginx). Chart
yangilanishi ilova versiyasini o’zgartirishi ham, o’zgartirmasligi ham
mumkin.

Bularning hammasi qayerda saqlanadi:

```bash
kubectl get secret -n apps -l name=web,owner=helm
# sh.helm.release.v1.web.v1   helm.sh/release.v1
kubectl get secret sh.helm.release.v1.web.v1 -n apps -o jsonpath='{.data.release}' | base64 -d | base64 -d | gunzip | head -c 500
```

O’sha Secret’larni o’chirsangiz, Helm release borligini unutadi - obyektlar
esa boshqarilmagan holda qolaveradi. Bu ba’zan foydali ("release’ni asrab
olish"), odatda esa tasodif.

## Value’lar, qatlamma-qatlam

Ustunlik, pastdan yuqoriga:

1. chart ichidagi `values.yaml`
2. `-f first.yaml`
3. `-f second.yaml` (keyingi fayllar ustun keladi)
4. `--set key=value` (hammasidan ustun)

```bash
helm install web bitnami/nginx -f base.yaml -f prod.yaml --set replicaCount=5
helm upgrade web bitnami/nginx --reuse-values --set image.tag=1.27.1   # oldingi value'larni saqlab, bittasini o'zgartiradi
helm upgrade web bitnami/nginx -f prod.yaml                             # --reuse-values BO'LMASA: oldingi --set value'lari tashlab yuboriladi
```

Ana o’sha oxirgi satr - kundalik tuzoq: `helm upgrade` chart standartlaridan
va **shu safar** siz uzatgan narsalardan boshlaydi, o’tgan safar
uzatganingizdan emas. Value’laringizni faylda saqlang va uni har doim
uzating, yoki `--reuse-values`’ni ataylab ishlating.

:::exam-tip
Imtihonni to’rtta fe’l va bitta flag qoplaydi: `install`, `upgrade`,
`rollback`, `uninstall` va `-n <namespace>`. Har bir
`helm list`/`upgrade`/`rollback` release’ning namespace’ini nomlashi kerak,
aks holda u indamay `default` ichiga qaraydi va "release not found" deydi.
:::

## O’zingizni tekshiring

1. Helm 3 release haqidagi yozuvni qayerda saqlaydi va uni o’chirsangiz nima
   bo’ladi?
2. CHART versiyasi va APP VERSION orasidagi farq nima?
3. Kecha `helm install web chart --set replicaCount=3` buyrug’ini, bugun esa
   `helm upgrade web chart --set image.tag=2` buyrug’ini bajardingiz. Hozir
   nechta replika bor va nega?
