## Render first, apply second

Kustomize's only product is YAML on stdout. Everything else is what you do
with that YAML.

```bash
kubectl kustomize overlays/prod
# or: kustomize build overlays/prod
```

```yaml
apiVersion: v1
kind: Service
metadata:
  labels:
    app: web
  name: prod-web
  namespace: prod
spec:
  ...
---
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: web
  name: prod-web
  namespace: prod
spec:
  replicas: 5
  ...
```

A multi-document stream, sorted (Namespaces and CRDs first, then the rest)
so that applying top to bottom works. Read it: this is **exactly** what will
reach the API server. If the output is wrong, the kustomization is wrong;
nothing between the two can change it.

## Applying it

```bash
kubectl kustomize overlays/prod | kubectl apply -f -      # the two-step form: render, pipe
kubectl apply -k overlays/prod                             # the one-step form: identical result
kubectl apply -k overlays/prod --dry-run=server           # validate against the cluster, apply nothing
kubectl diff -k overlays/prod                              # what would change versus what is live
kubectl delete -k overlays/prod                            # delete everything the overlay produces
```

The two-step form has a use beyond habit: save the rendered file and commit
it, or hand it to a tool that does not speak `-k`, or `grep` it in CI.

```bash
kubectl kustomize overlays/prod > rendered/prod.yaml
```

## Checking the output quickly

```bash
kubectl kustomize overlays/prod | grep -c "^kind:"                     # how many objects
kubectl kustomize overlays/prod | grep -E "^kind:|^  name:"            # kinds and names
kubectl kustomize overlays/prod | yq '.metadata.namespace' -            # with yq installed
kubectl kustomize overlays/prod | kubectl apply --dry-run=client -f -   # does it even parse as objects
```

## Errors come from the render, not the apply

```
error: accumulating resources: ... 'deployment.yml' must be a file (got 'deployment.yaml')
error: no matches for Id Deployment.v1.apps/api.[noNs]; failed to find unique target for patch
error: evalsymlink failure on '../../base' : lstat ...: no such file or directory
```

They name the field and the path. `kubectl kustomize` is therefore the
debugging tool: run it until it is clean, and only then `apply -k`.

:::exam-tip
Always run `kubectl kustomize <dir>` before `kubectl apply -k <dir>` in a
task - it is one command, it costs three seconds, and it turns "why did the
apply do that" into "oh, the patch targets nothing". After the apply,
`kubectl get all -n <ns>` confirms the names the output promised.
:::

## Check yourself

1. What does `kubectl kustomize` produce, and what is the relationship
   between it and `kubectl apply -k`?
2. How do you see what an apply **would** change without applying?
3. A patch error appears. Is it a render-time or apply-time error, and what
   does that tell you about where to fix it?
