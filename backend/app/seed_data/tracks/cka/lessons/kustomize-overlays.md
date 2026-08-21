## The layout that makes environments cheap

```
k8s/
  base/
    kustomization.yaml        # resources: [deployment.yaml, service.yaml, configmap.yaml]
    deployment.yaml
    service.yaml
    configmap.yaml
  overlays/
    dev/
      kustomization.yaml
    staging/
      kustomization.yaml
      replicas-patch.yaml
    prod/
      kustomization.yaml
      resources-patch.yaml
      hpa.yaml                # an object that exists ONLY in prod
```

The base is complete and valid. Each overlay is `resources: [../../base]`
plus its differences - and, when an environment needs something the others
do not, an **extra resource** of its own.

```yaml
# overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources: [../../base]
namespace: dev
nameSuffix: -dev
images: [{name: myapi, newTag: main}]
replicas: [{name: api, count: 1}]
```

```yaml
# overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
  - hpa.yaml                            # prod-only object
namespace: prod
images: [{name: myapi, newTag: "2.1.0"}]
replicas: [{name: api, count: 5}]
patches:
  - path: resources-patch.yaml          # bigger limits in prod
labels:
  - pairs: {env: prod}
    includeSelectors: false
```

```bash
kubectl apply -k k8s/overlays/dev
kubectl apply -k k8s/overlays/prod
diff <(kubectl kustomize k8s/overlays/dev) <(kubectl kustomize k8s/overlays/prod)
```

## What belongs where

| In the base | In an overlay |
|---|---|
| everything that is true everywhere: the Deployment's shape, the Service, probes, labels that define the app | replica counts, image tags, resource sizes, hostnames, namespace, env-specific ConfigMap values |
| sensible defaults (1 replica, small limits) - dev-like | objects only one environment has (HPA, PDB, a debug sidecar) |
| | secrets references (the Secret itself usually comes from elsewhere) |

If you find the same patch in every overlay, it belongs in the base. If you
find an `if prod` anywhere, you are missing an overlay.

## Overlays on overlays

An overlay can use another overlay as its base - `overlays/prod-eu`
including `../prod` and changing a region label and a hostname. Kustomize
composes without limit. Keep it to two levels unless you enjoy reading
`kubectl kustomize` output to find where a value came from.

## Generated ConfigMaps per environment

```yaml
# overlays/prod/kustomization.yaml
configMapGenerator:
  - name: app-config
    behavior: merge                # merge into the base's app-config (or replace / create)
    literals:
      - LOG_LEVEL=warn
      - DB_HOST=db.prod.svc
```

With the default name-suffix hash, a changed value produces a new ConfigMap
name (`app-config-7f9b2c`) and Kustomize rewrites the Deployment's reference
- so a config change **rolls the Pods**, which `kubectl edit configmap` never
does.

:::exam-tip
An exam overlay task usually gives you the base and asks for an overlay
that "sets replicas to N, uses image tag T, and puts everything in namespace
X" - three fields (`replicas`, `images`, `namespace`) and `resources:
[../../base]`. Create the directory, write those five lines, `kubectl
kustomize` to check, `kubectl apply -k`. Under two minutes.
:::

## Check yourself

1. What goes in the base and what goes in an overlay, in one sentence each?
2. How does an environment get an object (say an HPA) that the others do not
   have?
3. Why does changing a generated ConfigMap's value roll the Pods, when
   editing a ConfigMap by hand does not?
