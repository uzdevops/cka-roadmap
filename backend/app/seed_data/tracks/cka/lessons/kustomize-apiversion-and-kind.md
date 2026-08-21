## The header

Every `kustomization.yaml` starts with two lines that look like a Kubernetes
object's and are not one:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
```

They tell Kustomize which schema the rest of the file follows. Omit them and
current versions assume these values and print a warning; write them and
the file is explicit and lints cleanly. Write them.

| Field | Value |
|---|---|
| `apiVersion` | `kustomize.config.k8s.io/v1beta1` - the only version in use, despite the "beta" |
| `kind` | `Kustomization` for a base or overlay; `Component` for a reusable optional piece (`kustomize.config.k8s.io/v1alpha1`) |

```yaml
# a component, for the components lesson
apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component
```

## Not a Kubernetes object

`kubectl apply -f kustomization.yaml` fails:

```
error: unable to recognize "kustomization.yaml": no matches for kind "Kustomization" in version "kustomize.config.k8s.io/v1beta1"
```

- because the API server has no such resource. The file is read by
Kustomize, on the client, with `-k`. If that error appears, you used `-f`
where you meant `-k`.

## Other non-object YAML you will see in a kustomize tree

Inline and file patches in JSON 6902 form are also not objects - they are
lists of operations:

```yaml
- op: replace
  path: /spec/replicas
  value: 3
```

Strategic merge patch files, by contrast, **are** partial objects, with
`apiVersion`, `kind` and `metadata.name` so Kustomize knows which resource
they modify:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
```

Both are covered in the patches lessons; the point here is only that a tree
of kustomize files contains three kinds of YAML - real objects, the
kustomization itself, and patches - and the header tells you which is which.

:::tip
Older tutorials omit the header entirely and show `bases:` instead of
`resources:`, `patchesStrategicMerge:` instead of `patches:`, `commonLabels`
instead of `labels`. They still work (with deprecation warnings) but write
the current forms - they are what `kustomize edit` generates and what the
exam's reference files will use.
:::

## Check yourself

1. What is the `apiVersion`/`kind` pair of a kustomization, and what is it
   for?
2. What happens if you `kubectl apply -f` a kustomization.yaml, and why?
3. Which `kind` does a reusable optional piece use?
