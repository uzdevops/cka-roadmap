## The file at the centre

Every directory Kustomize can process has one `kustomization.yaml` (or
`kustomization.yml`, or `Kustomization`). It lists what to include and what
to do to it.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

# WHAT - the inputs
resources:
  - deployment.yaml
  - service.yaml
  - ../../base                 # another directory with its own kustomization.yaml
  - https://github.com/org/repo//path?ref=v1.2.0    # a remote directory

# HOW - transformers applied to everything above
namespace: prod
namePrefix: prod-
nameSuffix: -v2
commonLabels:                   # deprecated in favour of `labels`, still works
  app: web
labels:
  - pairs: {team: payments}
    includeSelectors: false     # label the objects, do not touch selectors
commonAnnotations:
  owner: platform
images:
  - name: myapp
    newName: registry.example.com/myapp
    newTag: "2.1.0"
replicas:
  - name: web
    count: 5

# targeted changes
patches:
  - path: resources-patch.yaml                     # strategic merge patch file
  - patch: |-                                       # inline JSON 6902
      - op: replace
        path: /spec/replicas
        value: 3
    target: {kind: Deployment, name: web}

# generated objects
configMapGenerator:
  - name: app-config
    literals: [MODE=prod]
    files: [config.properties]
secretGenerator:
  - name: db-secret
    literals: [password=hunter2]
generatorOptions:
  disableNameSuffixHash: false  # keep the content hash in generated names (the default)

# optional pieces
components:
  - ../../components/caching
```

You never use all of it at once. A base is usually just `resources:`. An
overlay is `resources: [../../base]` plus two or three of the rest.

## resources

The files and directories to include, in order. A file is a plain manifest
(possibly multi-document with `---`). A directory must contain its own
`kustomization.yaml` and is rendered recursively. Paths are relative to this
file.

```bash
kubectl kustomize .          # errors name the exact file and field when something is wrong
```

Forgetting to list a new file in `resources` is the classic "I added
hpa.yaml and nothing changed" - Kustomize only sees what is listed.

## Order of operations

Kustomize loads `resources` (recursively), applies **generators** (adding the
generated ConfigMaps/Secrets), then **transformers** (namespace, prefixes,
labels, images, replicas), then **patches**, then the **name-reference
fixing** that updates every reference - a Deployment's `configMapRef`, a
Service's selector - to the new names. That last step is why `namePrefix` is
safe: references follow.

## Seeing what it does

```bash
kubectl kustomize overlays/prod | less
kubectl kustomize overlays/prod | grep -E "^  name:|namespace:|image:|replicas:"
kubectl kustomize overlays/prod > /tmp/rendered.yaml && kubectl apply --dry-run=client -f /tmp/rendered.yaml
```

:::exam-tip
Read an unfamiliar `kustomization.yaml` top to bottom in this order: what
does it include (`resources`), what does it do to all of it (namespace,
prefix, labels, images), what does it change specifically (`patches`). Then
`kubectl kustomize` to confirm before `apply -k`. Fifteen seconds, and you
will not be surprised by the result.
:::

## Check yourself

1. What is the one field every kustomization has, and what may it contain?
2. In what order are generators, transformers and patches applied?
3. You add `hpa.yaml` to the directory and `kubectl apply -k` ignores it.
   Why?
