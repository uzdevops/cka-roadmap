## One kustomization per directory, directories that include directories

A real project is not four files in one folder. It is an API, a database, a
cache, a monitoring sidecar - each with its own manifests - and you want to
apply the whole thing with one command, or any part alone.

```
k8s/
  kustomization.yaml          # resources: [api/, db/, cache/]
  api/
    kustomization.yaml        # resources: [deployment.yaml, service.yaml]
    deployment.yaml
    service.yaml
  db/
    kustomization.yaml        # resources: [statefulset.yaml, service.yaml, secret.yaml]
    statefulset.yaml
    service.yaml
    secret.yaml
  cache/
    kustomization.yaml
    deployment.yaml
    service.yaml
```

```yaml
# k8s/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - api
  - db
  - cache
```

```bash
kubectl apply -k k8s/            # everything
kubectl apply -k k8s/api/        # just the API
```

A `resources` entry that is a **directory** must contain its own
`kustomization.yaml`; Kustomize renders it recursively and includes the
result. Each sub-directory is a complete, applyable unit on its own, and the
root composes them. Three levels deep is fine; the rule is the same at every
level.

## Why not one big kustomization listing every file

```yaml
# this works, and it is what you have before you learn directories
resources:
  - api/deployment.yaml
  - api/service.yaml
  - db/statefulset.yaml
  - db/service.yaml
  - db/secret.yaml
  - cache/deployment.yaml
  - cache/service.yaml
```

It works until: you want to apply only the database; you want a
`namespace: data` on the db objects but not the api; you want to add a
fourth service and forget one of its three files. Per-directory
kustomizations give each part its own transformers and its own
`kubectl apply -k`, and the root just lists directories.

## Transformers at each level

```yaml
# k8s/db/kustomization.yaml
resources: [statefulset.yaml, service.yaml, secret.yaml]
namespace: data              # only the db objects
commonLabels: {tier: data}
```

```yaml
# k8s/kustomization.yaml
resources: [api, db, cache]
commonLabels: {app: shop}    # everything, on top of what the children set
```

Children apply theirs first, then the parent applies its own to the
combined result. Labels accumulate; a parent `namespace` overrides a child's.

## Remote directories

```yaml
resources:
  - https://github.com/kubernetes-sigs/kustomize//examples/helloWorld?ref=v5.4.0
  - github.com/org/platform-base//k8s/base?ref=main
```

A Git URL with `//` separating repo from path and `?ref=` pinning a tag or
commit. That is how a base can be shared across repositories - with a pinned
ref, or your builds change under you.

:::exam-tip
When a task's directory tree has kustomizations in sub-directories, apply
from the **root** that lists them (`kubectl apply -k k8s/`) unless told to
apply one part. And if `kubectl kustomize` says a directory "must have a
kustomization file", the sub-directory you listed has none - create it with
`resources:` naming its files (or `kustomize create --autodetect` inside it).
:::

## Check yourself

1. What must a directory contain to be listed under `resources`?
2. A parent kustomization sets `namespace: prod` and a child sets
   `namespace: data`. Which wins for the child's objects?
3. Why split into per-directory kustomizations rather than one list of all
   files?
