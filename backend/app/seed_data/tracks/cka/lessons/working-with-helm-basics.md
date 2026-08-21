## The everyday verbs

```bash
helm search hub wordpress                       # Artifact Hub
helm search repo bitnami/wordpress --versions   # a repo you added
helm show chart bitnami/wordpress               # Chart.yaml
helm show values bitnami/wordpress              # values.yaml - the knobs
helm show readme bitnami/wordpress
```

### install

```bash
helm install my-site bitnami/wordpress                           # release name, chart
helm install my-site bitnami/wordpress -n web --create-namespace
helm install my-site bitnami/wordpress --version 22.1.0          # pin the chart version
helm install my-site ./wordpress-22.1.0.tgz                      # a local package
helm install my-site ./my-chart-dir                              # a local directory
helm install my-site bitnami/wordpress --generate-name           # let Helm name it
helm install my-site bitnami/wordpress --wait --timeout 5m       # block until Pods are Ready
```

```
NAME: my-site
LAST DEPLOYED: Mon Aug 18 10:00:00 2026
NAMESPACE: web
STATUS: deployed
REVISION: 1
NOTES:
  ... (the chart's NOTES.txt: how to reach it, how to get the password)
```

### list, status, get

```bash
helm list -n web                  # releases in a namespace
helm list -A                      # everywhere
helm list -A --failed             # only broken ones
helm status my-site -n web        # the NOTES again, plus resources with --show-resources
helm get manifest my-site -n web  # exactly what was applied
helm get values my-site -n web    # what you set
helm get notes my-site -n web
helm history my-site -n web
```

### upgrade

```bash
helm upgrade my-site bitnami/wordpress -n web --set replicaCount=2       # change values (chart version stays the latest in the repo index)
helm upgrade my-site bitnami/wordpress -n web --version 22.2.0           # change chart version
helm upgrade my-site bitnami/wordpress -n web -f prod.yaml --reuse-values
helm upgrade --install my-site bitnami/wordpress -n web                   # install if absent, upgrade if present - the CI idiom
```

### rollback and uninstall

```bash
helm rollback my-site 1 -n web
helm uninstall my-site -n web
helm uninstall my-site -n web --keep-history       # keep the revisions for inspection
```

`uninstall` deletes every object the release created **except** objects
annotated `helm.sh/resource-policy: keep` - PersistentVolumeClaims in many
database charts - so data survives an accidental uninstall.

## Looking at the result the kubectl way

```bash
kubectl get all -n web -l app.kubernetes.io/instance=my-site
kubectl get all -n web -l app.kubernetes.io/managed-by=Helm
```

Charts following the conventions label everything with the release name
(`instance`) and `managed-by=Helm`, so the objects a release created are one
selector away.

## When install fails

```bash
helm install my-site bitnami/wordpress -n web --dry-run --debug | less    # see the YAML and the error before applying
helm list -n web -a                                                        # -a shows failed/pending releases too
helm status my-site -n web
helm uninstall my-site -n web        # a failed install still created a release record; remove it before retrying
```

| Message | Means |
|---|---|
| `Error: INSTALLATION FAILED: cannot re-use a name that is still in use` | the release exists (maybe failed) - `helm list -a`, uninstall or pick a name |
| `Error: failed to download "bitnami/x"` | repo not added or not updated, or the version does not exist |
| `Error: UPGRADE FAILED: another operation (install/upgrade/rollback) is in progress` | a stuck pending release - `helm rollback` to the last good revision, or `helm history` and fix the record |
| `Error: context deadline exceeded` | `--wait` timed out: Pods not Ready - `kubectl get pods` |

:::exam-tip
The exam's Helm tasks read like: "install chart X from repo Y as release Z
in namespace N with value K=V", "upgrade release Z to chart version A",
"roll back Z to revision 1", "uninstall Z". Each is one command on this
page, always with `-n`. `helm list -A` at the end proves the state.
:::

## Check yourself

1. Write the one command that installs **or** upgrades a release depending
   on whether it exists.
2. What does `helm uninstall` leave behind, and why?
3. An install failed halfway and a retry says the name is in use. What do
   you do?
