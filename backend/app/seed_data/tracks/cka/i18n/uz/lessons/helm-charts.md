## Chart anatomiyasi

```bash
helm create hello            # chart'ning skeletini yaratadi
tree hello
```

```
hello/
├── Chart.yaml          # metama'lumot: name, version, appVersion, description, dependencies
├── values.yaml         # standart value'lar - chart'ning ommaviy interfeysi
├── charts/             # bog'liq chart'lar (subchart'lar), ichiga joylangan
├── templates/          # manifestlar, Go shablonlari ko'rinishida
│   ├── _helpers.tpl    # nomlangan shablon bo'laklari (label'lar, to'liq nom)
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── serviceaccount.yaml
│   ├── hpa.yaml
│   ├── NOTES.txt       # install'dan keyin chop etiladi
│   └── tests/
│       └── test-connection.yaml   # `helm test` uchun Pod
└── .helmignore
```

## Chart.yaml

```yaml
apiVersion: v2                 # v2 = Helm 3 chart formati
name: hello
description: A Helm chart for Kubernetes
type: application              # yoki library
version: 0.1.0                 # CHART versiyasi - chart'dagi har qanday o'zgarishda oshiring
appVersion: "1.16.0"           # u o'rnatadigan dasturiy ta'minot versiyasi
dependencies:
  - name: postgresql
    version: "15.x.x"
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
```

`version` - `helm search repo --versions` sanab beradigan va `--version`
biriktiradigan narsa. `dependencies` esa subchart’larni `helm dependency
update` bilan `charts/` ichiga tortadi.

## Shablonlar va value’lar

```yaml
# templates/deployment.yaml (qisqartirilgan)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "hello.fullname" . }}
  labels:
    {{- include "hello.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  template:
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          ports:
            - containerPort: {{ .Values.service.port }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
```

```yaml
# values.yaml
replicaCount: 1
image:
  repository: nginx
  tag: ""
service:
  type: ClusterIP
  port: 80
resources: {}
```

`{{ .Values.x }}` birlashtirilgan value’larni o’qiydi; `.Chart` Chart.yaml’ni
o’qiydi; `.Release.Name`/`.Release.Namespace` - release’niki; `include`
`_helpers.tpl`dan nomlangan shablonni chaqiradi; `default`, `toYaml`,
`nindent`, `quote` - eng ko’p uchraydigan funksiyalar. `{{- ` o’zidan
oldingi bo’sh joyni kesadi.

## Chart nima ishlab chiqarishini ko’rish

```bash
helm template hello ./hello                          # lokal render, klastersiz
helm template hello ./hello --set replicaCount=3 | grep replicas
helm install hello ./hello --dry-run --debug         # klasterga qarab render (tekshiradi, lookup bajaradi), apply qilmaydi
helm lint ./hello                                    # shablon va schema xatolarini topadi
```

`helm template` - bu chart’ni Kustomize’ga uzatish yoki uchinchi tomon
chart’iga ishonishdan oldin uni ko’rib chiqish usuli ham:

```bash
helm pull bitnami/nginx --untar && helm template x ./nginx | less
```

## Paketlash va chop etish

```bash
helm package ./hello                  # hello-0.1.0.tgz
helm repo index . --url https://charts.example.com     # .tgz katalogi uchun index.yaml
helm push hello-0.1.0.tgz oci://registry.example.com/charts    # OCI registry'ga
```

:::exam-tip
CKA sizdan chart yozishni so’ramaydi. U sizga chart berishi mumkin (katalog
yoki `.tgz`) va uni value’lar bilan o’rnatishni so’rashi mumkin, yoki
chart’da biror kalitning standart qiymati nima ekanini so’rashi mumkin -
`helm show values ./chart` yoki `cat values.yaml`. Tuzilmani taniy oling;
`templates/` - bu YAML, `values.yaml` esa sozlagichlar ekanini biling.
:::

## O’zingizni tekshiring

1. Chart’ni tushunish uchun o’qiydigan ikkita fayl qaysi va ularning har
   biri sizga nima aytadi?
2. Chart.yaml’dagi `version` va `appVersion` orasidagi farq nima?
3. Qaysi buyruq chart’ni klasterga tegmasdan oddiy YAML’ga render qiladi?
