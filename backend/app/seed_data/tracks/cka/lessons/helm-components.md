## The parts and how they connect

```
 helm CLI ──reads──▶ chart (from a repo, an OCI registry, or a local dir)
          ──reads──▶ values (chart defaults + your overrides)
          ──renders─▶ manifests
          ──applies─▶ API server ──▶ objects in a namespace
          ──records─▶ release Secret (sh.helm.release.v1.<name>.v<N>) in that namespace
```

| Component | What it is |
|---|---|
| **helm** | the CLI; everything happens here |
| **chart** | the package (next lesson) |
| **repository** | an `index.yaml` plus `.tgz` charts behind HTTP - or an OCI registry |
| **values** | parameters: `values.yaml` defaults inside the chart, plus `-f` files and `--set` flags from you |
| **release** | a named, versioned installation of a chart |
| **release secret** | Helm's own record: the rendered manifests and the values, base64+gzip, one per revision |
| **hooks** | manifests annotated to run at a lifecycle point (`pre-install`, `post-upgrade`, `test`) |

## Repositories

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
cat ~/.config/helm/repositories.yaml          # what `repo add` wrote
helm repo update
helm search repo bitnami/nginx --versions     # every chart version in the index
helm pull bitnami/nginx --untar               # download a chart to look inside
```

A repository is static files: `index.yaml` listing chart names, versions and
`.tgz` URLs. GitHub Pages, an S3 bucket, a Nexus/Harbor instance - anything
that serves files is a Helm repo. `helm repo update` fetches the index;
without it, you search a stale copy.

## Releases and revisions

```bash
helm install web bitnami/nginx -n apps --create-namespace
helm install web2 bitnami/nginx -n apps           # same chart, second release
helm list -n apps
# NAME  NAMESPACE  REVISION  STATUS    CHART         APP VERSION
# web   apps       1         deployed  nginx-18.1.0  1.27.0
# web2  apps       1         deployed  nginx-18.1.0  1.27.0
helm status web -n apps
helm get values web -n apps                       # the values you supplied
helm get values web -n apps --all                 # including chart defaults
helm get manifest web -n apps                     # the YAML Helm applied
helm history web -n apps
```

Two columns people confuse: **CHART** version (`nginx-18.1.0`, the package)
and **APP VERSION** (`1.27.0`, the nginx inside). A chart upgrade may or may
not change the app version.

Where it is all kept:

```bash
kubectl get secret -n apps -l name=web,owner=helm
# sh.helm.release.v1.web.v1   helm.sh/release.v1
kubectl get secret sh.helm.release.v1.web.v1 -n apps -o jsonpath='{.data.release}' | base64 -d | base64 -d | gunzip | head -c 500
```

Delete those Secrets and Helm forgets the release exists - the objects stay,
unmanaged. That is occasionally useful ("adopt" a release) and usually an
accident.

## Values, layered

Precedence, lowest to highest:

1. `values.yaml` inside the chart
2. `-f first.yaml`
3. `-f second.yaml` (later files win)
4. `--set key=value` (wins over everything)

```bash
helm install web bitnami/nginx -f base.yaml -f prod.yaml --set replicaCount=5
helm upgrade web bitnami/nginx --reuse-values --set image.tag=1.27.1   # keep previous values, change one
helm upgrade web bitnami/nginx -f prod.yaml                             # WITHOUT --reuse-values: previous --set values are dropped
```

That last line is the everyday trap: `helm upgrade` starts from the chart
defaults plus what you pass **this time**, not from what you passed last
time. Keep your values in a file and always pass it, or use `--reuse-values`
deliberately.

:::exam-tip
Four verbs and one flag cover the exam: `install`, `upgrade`, `rollback`,
`uninstall`, and `-n <namespace>`. Every `helm list`/`upgrade`/`rollback`
must name the release's namespace or it silently looks in `default` and says
"release not found".
:::

## Check yourself

1. Where does Helm 3 store the record of a release, and what happens if you
   delete it?
2. What is the difference between CHART version and APP VERSION?
3. You ran `helm install web chart --set replicaCount=3` yesterday and
   `helm upgrade web chart --set image.tag=2` today. How many replicas now,
   and why?
