## The problem both solve

You have a Deployment, a Service, a ConfigMap and an Ingress for one
application. You need it in `dev`, `staging` and `prod`, with different
replica counts, images, hostnames and resource limits. Copying the four
files three times gives twelve files that drift apart the first week.

**Helm** and **Kustomize** are the two mainstream answers, and they take
opposite approaches.

| | Helm | Kustomize |
|---|---|---|
| Idea | **templates** with placeholders, filled from a values file | **plain YAML** bases, modified by overlays and patches |
| Unit | a **chart** - a package with templates, default values, metadata | a directory with a `kustomization.yaml` |
| Install | `helm install name chart -f values.yaml` | `kubectl apply -k dir/` |
| Tracks state | yes - **releases** with revisions, history, rollback | no - it renders YAML; `kubectl apply` does the rest |
| Distribution | repositories and registries of charts (Artifact Hub) | Git, any directory |
| Learning curve | Go templates, chart structure | YAML, a few concepts |
| Built into kubectl | no (separate CLI) | **yes** (`kubectl apply -k`, `kubectl kustomize`) |

## Helm in one screen

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install my-db bitnami/postgresql --set auth.postgresPassword=secret
helm list
helm upgrade my-db bitnami/postgresql --set primary.persistence.size=20Gi
helm rollback my-db 1
helm uninstall my-db
```

Someone wrote a chart once - templates for every object PostgreSQL needs,
with every knob exposed as a value - and you set the three values you care
about. That is Helm's strength: **installing other people's software**.

## Kustomize in one screen

```
app/
  base/
    deployment.yaml   service.yaml   kustomization.yaml   (resources: [deployment.yaml, service.yaml])
  overlays/
    dev/   kustomization.yaml   (resources: [../../base]; replicas patch: 1; namePrefix: dev-)
    prod/  kustomization.yaml   (resources: [../../base]; replicas patch: 5; images: newTag 2.1.0)
```

```bash
kubectl kustomize overlays/prod | less       # see the rendered YAML
kubectl apply -k overlays/prod
```

The base is real, valid YAML you could apply as-is; overlays describe only
what differs. That is Kustomize's strength: **managing your own manifests
across environments** without a template language.

## When to use which

- Installing a third-party component (ingress controller, cert-manager,
  monitoring, a database) → **Helm** - the chart exists, use it.
- Your own application's manifests, in Git, per environment → **Kustomize**
  - readable diffs, no templating bugs.
- Both at once is normal: `helm template` renders a chart to YAML and
  Kustomize patches it (`helmCharts:` in a kustomization does exactly
  that); Argo CD and Flux support both natively.

:::exam-tip
The 2025 CKA adds both to the curriculum: "use Helm and Kustomize to install
cluster components". Expect `helm repo add / install / upgrade / rollback /
uninstall` and `kubectl apply -k` with a kustomization that uses resources,
a transformer and a patch. The next lessons go through each, then the labs
make your hands do it.
:::

## This week's map

| Days | Topic |
|---|---|
| Helm | what it is, installing it, Helm 2 vs 3, components, charts, everyday verbs, custom values, lifecycle |
| Kustomize | the problem and idea, vs Helm, installing, `kustomization.yaml`, output, directories, transformers, patches, overlays, components |

## Check yourself

1. State the one-sentence difference between how Helm and Kustomize reuse
   manifests.
2. Which one tracks what it installed and can roll back, and which one is
   built into kubectl?
3. You need to install cert-manager, and you need to deploy your own API in
   three environments. Which tool for which?
