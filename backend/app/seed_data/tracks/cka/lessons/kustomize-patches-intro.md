## Changing one thing in one object

Transformers change every resource. A **patch** changes specific fields of
specific resources: this Deployment's replicas, that container's memory
limit, an extra env var, a new volume. Two patch languages, one `patches:`
field.

```yaml
patches:
  - target:                          # WHICH resource(s)
      kind: Deployment
      name: api
    patch: |-                        # WHAT to do - JSON 6902 form
      - op: replace
        path: /spec/replicas
        value: 3
  - path: memory-patch.yaml          # WHAT to do - strategic merge form, in a file
```

## JSON 6902 patches: operations on paths

```yaml
- op: replace                        # add | remove | replace | move | copy | test
  path: /spec/template/spec/containers/0/resources/limits/memory
  value: 512Mi
- op: add
  path: /spec/template/spec/containers/0/env/-          # `-` = append to the list
  value: {name: MODE, value: prod}
- op: remove
  path: /spec/template/spec/containers/1                # by index
```

`path` is a JSON pointer: `/` separated, lists by index, `-` for "end of
list". Precise, a bit terse, and the only form that can **remove** a field or
an element cleanly.

## Strategic merge patches: a partial object

```yaml
# memory-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api                          # identifies the target
spec:
  template:
    spec:
      containers:
        - name: api                  # merge key: matches the container by NAME, not index
          resources:
            limits:
              memory: 512Mi
```

You write the part of the object you want changed; Kustomize merges it into
the real one, using each field's **merge key** (`name` for containers, ports,
env vars, volumes) to match list items. Readable, and the form that looks
like what you already know - but it cannot delete a list element without a
`$patch: delete` directive.

## Targeting

```yaml
patches:
  - path: patch.yaml                         # strategic merge: the file's apiVersion/kind/name ARE the target
  - patch: |- ...
    target:                                  # JSON 6902, or a strategic merge patch without its own name:
      group: apps
      version: v1
      kind: Deployment
      name: api                              # exact name, or
      labelSelector: "tier=web"              # every Deployment with this label
      namespace: shop
      annotationSelector: ...
```

A target with a `labelSelector` and no `name` patches **every** matching
resource - one patch adding a `nodeSelector` to all Deployments labelled
`tier=web`. `name` supports a regex (`name: "api-.*"`).

## Both in one file

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources: [../../base]
patches:
  - path: replicas-patch.yaml                      # strategic merge file
  - path: env-patch.yaml
  - target: {kind: Deployment, name: api}          # inline JSON 6902
    patch: |-
      - op: add
        path: /spec/template/spec/nodeSelector
        value: {disktype: ssd}
```

:::exam-tip
Choose by verb. **Set or add a field** → either form; the strategic merge
file is less error-prone. **Remove** a field or list item → JSON 6902. **Add
to a list** (a container, an env var) → strategic merge with the merge key
is clearest; JSON 6902 `add` to `/.../-` also works. Then `kubectl
kustomize | grep` the field. A patch whose target matches nothing is an
error - read it; it names the kind and name it looked for.
:::

## Check yourself

1. What are the two patch forms, and which one can remove a list element
   without a special directive?
2. In a strategic merge patch, how does Kustomize know which container in
   the list you mean?
3. How do you apply one patch to every Deployment with label `tier=web`?
