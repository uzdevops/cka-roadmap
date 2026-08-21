## Optional features, switched on per overlay

Overlays answer "dev vs prod". Components answer a different question:
**"with or without feature X"** - caching, an external database, LDAP auth,
a debug sidecar - where the same feature might be wanted in several overlays
and not in others, and copying its patches into each overlay is the drift
problem all over again.

A **component** is a reusable bundle of resources and patches that an
overlay **includes**. It is not a base (it does not stand alone) and not an
overlay (it does not produce a full application); it is a slice that can be
added to any kustomization.

```
k8s/
  base/                         the application
  components/
    caching/
      kustomization.yaml        kind: Component
      redis.yaml                a Redis Deployment + Service
      api-patch.yaml            sets REDIS_HOST on the api container
    external-db/
      kustomization.yaml        kind: Component
      db-patch.yaml             removes the bundled db, points the api at an external host
  overlays/
    dev/        resources: [../../base]                                      # plain
    prod/       resources: [../../base]; components: [../../components/caching, ../../components/external-db]
    staging/    resources: [../../base]; components: [../../components/caching]
```

## Writing one

```yaml
# components/caching/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component
resources:
  - redis.yaml
patches:
  - path: api-patch.yaml
```

```yaml
# components/caching/api-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  template:
    spec:
      containers:
        - name: api
          env:
            - name: REDIS_HOST
              value: redis
```

Note `kind: Component` and the `v1alpha1` apiVersion - a component is its
own kind. Its patches target resources that **the including overlay**
provides (here, the base's `api` Deployment); on its own, `kubectl kustomize
components/caching` fails because there is nothing to patch.

## Using one

```yaml
# overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
components:
  - ../../components/caching
  - ../../components/external-db
namespace: prod
```

```bash
kubectl kustomize overlays/prod | grep -E "^kind:|REDIS_HOST"     # Redis objects and the env var are present
kubectl kustomize overlays/dev  | grep -c redis                    # 0
```

Components are applied **after** `resources` are loaded and before the
overlay's own transformers and patches, in the order listed - so a later
component can patch what an earlier one added.

## Overlays vs components

| | Overlay | Component |
|---|---|---|
| answers | which environment | which optional feature |
| includes | a base (`resources`) | nothing on its own; is included via `components:` |
| `kind` | Kustomization | Component |
| combinable | one per environment | any number per overlay |

The combinatorics are the win: 3 environments × 4 optional features is 12
overlays without components, and 3 overlays plus 4 components with them.

:::exam-tip
If a task mentions components, check three things: the component file says
`kind: Component` with the `v1alpha1` apiVersion; the overlay lists it under
`components:` (not `resources:` - that is the error you will see); and the
component's patches target names that exist in the base. Then `kubectl
kustomize` the overlay and grep for what the component adds.
:::

## Check yourself

1. What question do components answer that overlays do not?
2. What are the `apiVersion` and `kind` of a component, and under which
   overlay field is it included?
3. Why does `kubectl kustomize components/caching` fail on its own?
