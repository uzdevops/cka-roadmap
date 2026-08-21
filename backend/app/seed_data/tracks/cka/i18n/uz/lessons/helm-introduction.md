## Kubernetes uchun paket menejeri

Klasterga WordPress’ni qo’lda o’rnatish - bu Deployment, Service,
PersistentVolumeClaim, ma’lumotlar bazasi paroli uchun Secret, MariaDB uchun
ikkinchi Deployment va Service, uning o’z PVC va Secret’i, ehtimol Ingress -
nomlar, label’lar, portlar va parollar bo’yicha bir-biriga mos kelishi kerak
bo’lgan sakkiz yoki to’qqizta manifest. Yangilash - ularning hammasini
tahrirlash; o’chirish - ularning hammasini eslab qolish.

Helm bu butun to’plamni **bitta narsa** deb qaraydi, xuddi `apt` dasturning
fayllarini bitta paket deb qaragani kabi:

```bash
helm install my-site bitnami/wordpress --set wordpressPassword=secret
helm upgrade my-site bitnami/wordpress --set replicaCount=2
helm rollback my-site 1
helm uninstall my-site
```

Bitta buyruq to’qqizta obyektning hammasini bir xil nomlar bilan o’rnatadi;
bittasi hammasini o’chiradi; bittasi yangilaydi va bittasi yangilashni bekor
qiladi.

## Lug’at

| Atama | Ma’nosi |
|---|---|
| **Chart** | paket: obyektlar uchun shablonlar + standart value’lar + metama’lumot (`Chart.yaml`) |
| **Release** | klasterga biror nom ostida o’rnatilgan chart; bir chart’ni ikki marta o’rnatsangiz, ikkita release bo’ladi |
| **Revision** | release’ning har bir `install`/`upgrade`/`rollback` amali raqamlangan reviziya; tarix saqlanadi |
| **Values** | sozlagichlar: chart’dagi `values.yaml` standart qiymatlarni beradi; siz `--set` yoki `-f` bilan ustidan yozasiz |
| **Repository** | chart’larning HTTP indeksi (`helm repo add`) yoki OCI registry (`oci://`) |
| **Artifact Hub** | artifacthub.io - ochiq repozitoriylar bo’ylab qidiruv tizimi |

```
chart (shablonlar + values.yaml) ──value'laringiz bilan render──▶ YAML ──apply──▶ klasterdagi obyektlar = release
```

## Nega skriptlar emas, chart’lar

`kubectl apply` buyruqlaridan iborat shell skript ham WordPress’ni o’rnatgan
bo’lardi. Chart qo’shadigan narsalar:

- **Parametrlash** - sizning o’rnatishingiz bilan meningki orasidagi har bir
  farq - bu value, tahrir emas.
- **Versiyalash** - chart’ning versiyasi bor, u o’rnatadigan ilovaning ham
  versiyasi bor va `helm upgrade` ular orasida harakatlantiradi.
- **Holat** - Helm nimani o’rnatganini yozib qo’yadi (namespace’dagi Secret
  sifatida), shuning uchun `upgrade` nimani o’zgartirishni, `uninstall` esa
  nimani o’chirishni biladi.
- **Hook va testlar** - upgrade’dan oldin Job ishga tushiring, install’dan
  keyin test.
- **Tarqatish** - `helm repo add` qilasiz va sizda mingta chart bor.

## Helm ekotizimda qayerda turadi

Klaster add-on’larining ko’pchiligi chart sifatida tarqatiladi:
ingress-nginx, cert-manager, metrics-server, Prometheus
(kube-prometheus-stack), Argo CD, CSI drayverlari, cloud kontrollerlari.
README’dagi "X’ni o’rnating" ko’pincha uchta Helm satridan iborat bo’ladi.
CKA buni dasturga shuning uchun qo’ygan - chart yozish uchun emas, ular bilan
komponentlarni o’rnatish va boshqarish uchun.

```bash
helm search hub wordpress                  # Artifact Hub, CLI'dan
helm search repo bitnami/nginx             # siz qo'shgan repozitoriy
helm show values bitnami/wordpress | less  # chart ochadigan har bir sozlagich
```

:::tip
`helm show values <chart>` - "buni qanday sozlayman" degan savolni "bu
kalitlardan qaysi birini belgilayman" degan savolga aylantiradigan buyruq.
Uni faylga yo’naltiring, o’zgartirgan uchta satringizni o’zingizning
`values.yaml` faylingiz sifatida saqlang va uni commit qiling.
:::

## O’zingizni tekshiring

1. Chart va release orasidagi farq nima?
2. `kubectl apply` buyruqlaridan iborat skript bermaydigan, Helm beradigan
   uchta narsani ayting.
3. Qaysi buyruq chart’ning har bir sozlanadigan value’sini ko’rsatadi?
