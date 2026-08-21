## Patching a map

Most of a manifest is maps - `metadata.labels`, `spec.template.spec`,
`resources.limits`. Three operations cover them: replace a value, add a key,
remove a key.

Starting point:

```yaml
# base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  labels:
    component: api
spec:
  replicas: 1
  template:
    metadata:
      labels:
        component: api
    spec:
      containers:
        - name: api
          image: myapi:1.0
```

## Replace

```yaml
# JSON 6902
patches:
  - target: {kind: Deployment, name: api}
    patch: |-
      - op: replace
        path: /spec/template/metadata/labels/component
        value: web
```

```yaml
# strategic merge - the same change
patches:
  - patch: |-
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: api
      spec:
        template:
          metadata:
            labels:
              component: web
```

In a strategic merge, a key you write **replaces** the existing value for
that key and leaves sibling keys alone - so `component: web` changes one
label and keeps any others.

## Add

```yaml
# JSON 6902
- op: add
  path: /spec/template/metadata/labels/org
  value: KodeKloud
```

```yaml
# strategic merge: adding is just writing a key that was not there
spec:
  template:
    metadata:
      labels:
        org: KodeKloud
```

`add` on a path that already exists behaves like replace. `add` to a path
whose parent does not exist fails - add the parent first (or use strategic
merge, which creates intermediate maps).

## Remove

```yaml
# JSON 6902
- op: remove
  path: /spec/template/metadata/labels/org
```

```yaml
# strategic merge: set the key to null
spec:
  template:
    metadata:
      labels:
        org: null
```

Both work; JSON 6902's `remove` is explicit, `null` in a merge patch is the
idiom people forget exists.

## Paths into maps

A JSON pointer path is the keys separated by `/`:

```
/metadata/labels/component
/spec/template/spec/containers/0/resources/limits/memory     <- through a LIST by index
/spec/template/metadata/annotations/prometheus.io~1scrape    <- a key containing "/" is escaped as ~1
```

That last one matters for annotations with slashes (`prometheus.io/scrape`,
`nginx.ingress.kubernetes.io/rewrite-target`): `/` becomes `~1`, `~` becomes
`~0`. In a strategic merge patch you just write the key in quotes.

```yaml
# strategic merge, no escaping
metadata:
  annotations:
    prometheus.io/scrape: "true"
```

## Checking

```bash
kubectl kustomize . | grep -A3 "labels:"
kubectl kustomize . | grep -c "org: KodeKloud"
```

:::exam-tip
For map fields, reach for the strategic merge form unless you need to
**remove** a key - it reads as YAML, it creates missing parents, and the
annotation-slash escaping never comes up. Save JSON 6902 for removals and
for lists, the next lesson.
:::

## Check yourself

1. Write both forms of a patch that changes label `component` on the Pod
   template to `web`.
2. How do you remove a key with a strategic merge patch?
3. Write the JSON pointer path for the annotation `prometheus.io/scrape` on
   a Pod template.
