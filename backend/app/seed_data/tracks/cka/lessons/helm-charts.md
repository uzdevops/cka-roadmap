## Anatomy of a chart

```bash
helm create hello            # scaffolds a chart
tree hello
```

```
hello/
├── Chart.yaml          # metadata: name, version, appVersion, description, dependencies
├── values.yaml         # default values - the chart's public interface
├── charts/             # dependency charts (subcharts), vendored
├── templates/          # the manifests, as Go templates
│   ├── _helpers.tpl    # named template snippets (labels, full name)
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── serviceaccount.yaml
│   ├── hpa.yaml
│   ├── NOTES.txt       # printed after install
│   └── tests/
│       └── test-connection.yaml   # a `helm test` Pod
└── .helmignore
```

## Chart.yaml

```yaml
apiVersion: v2                 # v2 = Helm 3 chart format
name: hello
description: A Helm chart for Kubernetes
type: application              # or library
version: 0.1.0                 # the CHART version - bump on any change to the chart
appVersion: "1.16.0"           # the version of the software it installs
dependencies:
  - name: postgresql
    version: "15.x.x"
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
```

`version` is what `helm search repo --versions` lists and what `--version`
pins. `dependencies` pull subcharts into `charts/` with `helm dependency
update`.

## Templates and values

```yaml
# templates/deployment.yaml (abridged)
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

`{{ .Values.x }}` reads the merged values; `.Chart` reads Chart.yaml;
`.Release.Name`/`.Release.Namespace` are the release's; `include` calls a
named template from `_helpers.tpl`; `default`, `toYaml`, `nindent`, `quote`
are the functions you see most. `{{- ` trims whitespace before it.

## Seeing what a chart will produce

```bash
helm template hello ./hello                          # render locally, no cluster
helm template hello ./hello --set replicaCount=3 | grep replicas
helm install hello ./hello --dry-run --debug         # render against the cluster (validates, runs lookups), do not apply
helm lint ./hello                                    # catch template and schema errors
```

`helm template` is also how you hand a chart to Kustomize, or inspect a
third-party chart before trusting it:

```bash
helm pull bitnami/nginx --untar && helm template x ./nginx | less
```

## Packaging and publishing

```bash
helm package ./hello                  # hello-0.1.0.tgz
helm repo index . --url https://charts.example.com     # an index.yaml for a directory of .tgz
helm push hello-0.1.0.tgz oci://registry.example.com/charts    # to an OCI registry
```

:::exam-tip
The CKA does not ask you to write a chart. It may hand you one (a directory
or a `.tgz`) and ask you to install it with values, or ask what a chart's
default for some key is - `helm show values ./chart` or `cat values.yaml`.
Recognise the layout; know that `templates/` is the YAML and `values.yaml`
is the knobs.
:::

## Check yourself

1. Which two files in a chart are the ones you read to understand it, and
   what does each tell you?
2. What is the difference between `version` and `appVersion` in Chart.yaml?
3. Which command renders a chart to plain YAML without touching a cluster?
