## Change everything at once

A transformer is a kustomization field that modifies **every** resource the
kustomization produces. Four of them cover almost all real use.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources: [../../base]

namespace: prod               # set metadata.namespace on every namespaced object
namePrefix: prod-             # name: web  ->  prod-web
nameSuffix: -v2               # name: web  ->  web-v2   (both: prod-web-v2)
commonLabels:                 # add to metadata.labels AND selectors/templates
  org: KodeKloud
  env: prod
commonAnnotations:
  owner: platform-team
```

```bash
kubectl kustomize overlays/prod | grep -E "^  name:|namespace:|org:|owner:"
```

## namespace

Sets `metadata.namespace` on every namespaced resource, overriding whatever
the files said. Cluster-scoped objects (Namespace, ClusterRole, CRD) are left
alone. It does **not** create the Namespace - include a Namespace manifest in
`resources` or create it first.

## namePrefix / nameSuffix

Rename every object - and, crucially, **fix every reference** to it: a
Service's name in an Ingress backend, a ConfigMap's name in a Deployment's
`envFrom`, a ServiceAccount name in a RoleBinding. That reference-fixing is
what makes prefixes usable; without it every overlay would break its own
wiring.

## commonLabels vs labels

`commonLabels` adds the labels to `metadata.labels` **and** to every
selector: `spec.selector.matchLabels` on Deployments, `spec.selector` on
Services, `spec.template.metadata.labels`. That keeps Services and
Deployments matched - and it makes the labels **immutable** in effect,
because a Deployment's selector cannot change after creation. Adding a
commonLabel to an already-deployed overlay therefore fails with
`field is immutable`.

The newer `labels` field lets you choose:

```yaml
labels:
  - pairs:
      team: payments
    includeSelectors: false      # metadata only - safe to add later
    includeTemplates: true       # also on Pod templates, so Pods carry it
  - pairs:
      app: web
    includeSelectors: true       # same as commonLabels
```

:::warning
Use `commonLabels` (or `includeSelectors: true`) only for labels that are
part of the application's identity from day one. Anything you might add
later - `team`, `cost-center`, `version` - goes in `labels` with
`includeSelectors: false`, or you will be deleting and recreating
Deployments to change a label.
:::

## The rest of the family

| Transformer | Does |
|---|---|
| `images` | change image name/tag/digest (next lesson) |
| `replicas` | set replicas on named Deployments/StatefulSets without a patch |
| `commonAnnotations` | annotations everywhere |
| `configMapGenerator` / `secretGenerator` | generate objects with a content hash suffix; references updated |
| `patches` | targeted changes (the patches lessons) |

```yaml
replicas:
  - name: web
    count: 5
```

## Order matters only in that it is fixed

Kustomize applies transformers in its own order (namespace, names, labels,
annotations, images, replicas, then patches), so you never think about it -
with one exception: a **patch** sees the object **after** the transformers,
so a patch targeting `name: web` when `namePrefix: prod-` is set must target
`web`, not `prod-web` - Kustomize matches patch targets against the
original names. The patches lesson returns to this.

## Check yourself

1. What does `namePrefix` do beyond renaming, and why is that essential?
2. What is the difference between `commonLabels` and `labels` with
   `includeSelectors: false`, and when does it bite?
3. Does `namespace: prod` create the namespace?
