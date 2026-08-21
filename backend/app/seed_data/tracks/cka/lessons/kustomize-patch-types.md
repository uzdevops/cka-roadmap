## Inline or in a file

Either patch language can be written **inline** in `kustomization.yaml` or
in a **separate file**; the choice is about readability, not capability.

### Inline

```yaml
patches:
  - target: {kind: Deployment, name: api}
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 3
  - target: {kind: Deployment, name: api}
    patch: |-
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: api
      spec:
        template:
          spec:
            containers:
              - name: api
                image: myapi:2.1.0
```

`|-` starts a literal block; the patch body is indented under it. Kustomize
detects which language it is: a YAML **list** of `op:` entries is JSON 6902;
a YAML **map** with `kind:` is strategic merge.

Inline is right for one-liners - a replica count, a single env var - where
a separate file would be more overhead than content.

### File

```yaml
patches:
  - path: patches/api-resources.yaml                         # strategic merge; target read from the file
  - path: patches/api-nodeselector.json                      # JSON 6902; needs an explicit target
    target: {kind: Deployment, name: api}
```

```yaml
# patches/api-resources.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  template:
    spec:
      containers:
        - name: api
          resources:
            requests: {cpu: 250m, memory: 256Mi}
            limits:   {cpu: "1",  memory: 512Mi}
```

```json
[
  {"op": "add", "path": "/spec/template/spec/nodeSelector", "value": {"disktype": "ssd"}}
]
```

A file is right when the patch is more than a few lines, when several
overlays share it (`- path: ../../patches/common.yaml`), or when you want it
reviewed as its own diff.

## Mixing the axes

| | JSON 6902 | Strategic merge |
|---|---|---|
| inline | `patch: \|-` with a list of `op:` + `target:` | `patch: \|-` with a partial object (target optional if the object names itself) |
| file | `path: x.json` or `x.yaml` + `target:` | `path: x.yaml` (target from the file) |

The one rule: a **JSON 6902 patch always needs `target:`**, because a list of
operations says nothing about which object it applies to. A strategic merge
patch carries its own `apiVersion`/`kind`/`metadata.name` and needs `target`
only to override or widen that (`labelSelector`).

## Legacy fields you will still see

```yaml
patchesStrategicMerge:        # deprecated: a list of strategic merge patch files
  - memory-patch.yaml
patchesJson6902:              # deprecated: target + path to a JSON 6902 file
  - target: {group: apps, version: v1, kind: Deployment, name: api}
    path: replicas.json
```

Both still work with a warning; `patches:` replaced them and handles every
case. Write `patches:`.

:::exam-tip
If a task hands you a patch **file**, wire it with `- path:` (plus `target:`
if it is JSON 6902). If it describes the change in a sentence, an inline
`patch: |-` is fastest. Either way, indentation under `patch: |-` is the
usual typo - the patch body must be indented more than `patch:` itself, and
a strategic merge body must start at `apiVersion:`.
:::

## Check yourself

1. How does Kustomize tell an inline JSON 6902 patch from an inline
   strategic merge patch?
2. Which patch form always requires `target:`, and why?
3. When would you put a patch in a file rather than inline?
