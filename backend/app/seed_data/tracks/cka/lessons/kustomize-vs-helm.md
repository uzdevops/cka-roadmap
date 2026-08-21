## Templating versus patching

Both solve "one set of manifests, many environments". They do it from
opposite ends.

**Helm** turns the manifests into templates with holes, and fills the holes
from values:

```yaml
replicas: {{ .Values.replicaCount }}
image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
```

**Kustomize** keeps the manifests whole and describes changes to them:

```yaml
# overlays/prod/kustomization.yaml
resources: [../../base]
images: [{name: myapp, newTag: "2.1.0"}]
patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
    target: {kind: Deployment, name: myapp}
```

| | Helm | Kustomize |
|---|---|---|
| the base YAML is | not valid on its own (has `{{ }}`) | valid, applyable as-is |
| expressiveness | anything Go templates can do: loops, conditionals, functions | only what overlays/patches can express - deliberately |
| packaging and sharing | charts, repos, versions | directories in Git |
| release tracking, rollback | yes | no - `kubectl apply` and `kubectl rollout` |
| third-party software | the ecosystem: thousands of charts | you patch what you vendor |
| mistakes look like | a template renders invalid YAML; a mistyped value is silently defaulted | a patch targets nothing (error) or the wrong thing (visible in `kubectl kustomize` output) |
| install | separate CLI | in kubectl |

## The honest trade

Helm's templates can do *anything*, and that is also the problem: a big
chart is a program written in a templating language, and reading it to find
out what it will produce means running it. Kustomize can do *less*, and that
is also the point: the base is readable, the overlay is a diff, and
`kubectl kustomize` shows you the whole result with no logic to follow.

For **software you did not write**, Helm's ecosystem wins - the chart author
has already exposed the knobs. For **manifests you own**, Kustomize keeps
them plain.

## Both, together

```yaml
# kustomization.yaml
helmCharts:
  - name: ingress-nginx
    repo: https://kubernetes.github.io/ingress-nginx
    version: 4.11.1
    releaseName: ingress
    namespace: ingress-nginx
    valuesInline:
      controller:
        replicaCount: 2
patches:
  - patch: |-
      - op: add
        path: /spec/template/spec/nodeSelector
        value: {role: edge}
    target: {kind: Deployment, name: ingress-ingress-nginx-controller}
```

```bash
kubectl kustomize --enable-helm . | kubectl apply -f -
```

Render the chart, then patch the rendered output with things the chart's
values cannot express. GitOps tools (Argo CD, Flux) support this shape
natively.

:::tip
A good rule for a team: Helm for installing platform components, Kustomize
for your applications, and the two never fight because they own different
directories.
:::

## Check yourself

1. Why is a Kustomize base applyable as-is while a Helm chart's templates
   are not?
2. Which tool would you pick to install Prometheus, and which to deploy
   your own API to three clusters?
3. How do you patch a Helm chart's output with Kustomize?
