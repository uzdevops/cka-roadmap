## Twelve files that drift

One application: `deployment.yaml`, `service.yaml`, `configmap.yaml`,
`ingress.yaml`. Three environments. The naive answer:

```
k8s/
  dev/    deployment.yaml service.yaml configmap.yaml ingress.yaml
  stg/    deployment.yaml service.yaml configmap.yaml ingress.yaml
  prod/   deployment.yaml service.yaml configmap.yaml ingress.yaml
```

Twelve files, nine of them near-identical copies. Add a readiness probe:
edit three files. Fix a label: three files. Within a month `dev` has a
probe `prod` does not, and nobody knows which differences are intentional.

## The idea: a base and overlays

Write the common manifests **once** - the base - and, per environment, only
**what differs**:

```
k8s/
  base/
    deployment.yaml  service.yaml  configmap.yaml  ingress.yaml
    kustomization.yaml          # lists the four
  overlays/
    dev/
      kustomization.yaml        # resources: [../../base] ; replicas: 1 ; namePrefix: dev-
    stg/
      kustomization.yaml        # replicas: 2
    prod/
      kustomization.yaml        # replicas: 5 ; image tag 2.1.0 ; an extra HPA
```

```bash
kubectl apply -k overlays/prod
```

Kustomize reads the overlay, pulls in the base, applies the overlay's
changes, and emits complete YAML. The base is plain, valid Kubernetes YAML -
no placeholders - and every overlay is a short list of differences that is
readable as a diff.

## What "customize" means

The changes an overlay can express:

- **transformers** that touch every resource: add a name prefix or suffix,
  a namespace, common labels or annotations, change image tags;
- **patches** that change specific fields of specific resources: replicas,
  a resource limit, an env var, a whole new container;
- **generators** that create ConfigMaps and Secrets from literals or files,
  with a content hash in the name so a change rolls the Pods;
- **composition** that pulls in other directories, other overlays, or
  optional components.

No template language. No `{{ }}`. The base stays applyable as-is, which
means it stays readable and lintable by any YAML tool.

## Ideology, in three lines

1. **Declarative all the way down**: the kustomization is YAML describing
   YAML.
2. **Template-free**: you never edit a file to make it valid.
3. **Built into kubectl**: `kubectl apply -k` and `kubectl kustomize` need
   nothing installed.

:::exam-tip
The exam task shape is "a base directory and an overlay are given; fix or
complete the overlay so that `kubectl apply -k` produces X". You will
read a `kustomization.yaml`, add a transformer or a patch, and apply. Know
the file's sections and the `-k` flag.
:::

## Check yourself

1. What is the problem with one directory of manifests per environment?
2. What is a base, and what does an overlay contain?
3. Name the four kinds of change a kustomization can express.
