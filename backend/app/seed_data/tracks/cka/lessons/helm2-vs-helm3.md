## Why old tutorials mention Tiller

Helm 2 had a server half: **Tiller**, a Deployment in `kube-system` that
the Helm client talked to and that actually applied manifests. Tiller ran
with whatever permissions you gave it - usually cluster-admin, because it
installed everything for everyone - and that one service account was a
security hole the size of the cluster. Helm 3 (November 2019) removed it.
Everything you read that says `helm init`, `tiller`, `--tiller-namespace`
is Helm 2 and is gone.

| | Helm 2 | Helm 3 |
|---|---|---|
| server component | Tiller in the cluster | none - the CLI talks to the API server |
| permissions | Tiller's service account | **yours** - your kubeconfig and RBAC |
| release storage | ConfigMaps in `kube-system` | Secrets in the **release's namespace** |
| release names | cluster-wide unique | unique **per namespace** |
| `helm init` | required | does not exist |
| upgrades | 2-way merge | **3-way strategic merge** |
| chart dependencies | `requirements.yaml` | in `Chart.yaml` |
| `helm delete` | kept history by default | `helm uninstall` removes it (`--keep-history` to keep) |
| libraries, JSON schema for values, OCI | no | yes |

## The three-way merge

This is the one that changes behaviour you will see. Helm 2 compared the old
chart output with the new chart output and applied the difference. If
someone had `kubectl edit`ed a release's Deployment in the meantime - say,
bumped replicas by hand - Helm 2 did not know and `helm rollback` would not
restore it.

Helm 3 compares **three** things: the previous chart output, the new chart
output, and the **live object**. A manual change outside Helm is noticed
and, on upgrade, preserved if the chart did not touch that field, or
overwritten if it did; on rollback, the live state is considered too.
Exactly the reasoning behind `kubectl apply`'s three-way merge from the
core-concepts phase.

```bash
kubectl scale deployment my-site-wordpress --replicas=3     # outside Helm
helm upgrade my-site bitnami/wordpress --set someOtherValue=x
kubectl get deployment my-site-wordpress                      # replicas still 3 - Helm 3 left the field it did not own
```

(Helm 2 would have put it back to the chart's value.)

## Revisions and rollback, Helm 3 style

```bash
helm history my-site
# REVISION  UPDATED                   STATUS      CHART             DESCRIPTION
# 1         Mon Aug 18 10:00:00 2026  superseded  wordpress-22.1.0  Install complete
# 2         Mon Aug 18 11:00:00 2026  superseded  wordpress-22.2.0  Upgrade complete
# 3         Mon Aug 18 11:30:00 2026  deployed    wordpress-22.1.0  Rollback to 1
helm rollback my-site 1
```

A rollback is a **new revision** (3) whose content is revision 1's - the same
pattern as `kubectl rollout undo`. History is capped (`--history-max`,
default 10).

:::warning
A rollback restores the Kubernetes **objects** - not the data in a volume,
not a database's rows. Rolling back a database chart's upgrade brings back
the old Deployment and the old image; if the new version migrated the
schema, the old image may not start. Helm rolls back manifests; backups roll
back data.
:::

## Migrating from Helm 2

The `helm-2to3` plugin converted Helm 2 releases in place (config, repos,
release storage). Nobody should be doing this any more; if you meet a
cluster with Tiller, it is a sign the cluster needs more than a Helm
upgrade.

:::exam-tip
Nothing on the exam is Helm 2. If a task's wording or a reference manifest
mentions Tiller or `helm init`, it is a distractor or a very old README -
Helm 3 has neither, and `helm` with no server component is the only Helm
you will use.
:::

## Check yourself

1. What was Tiller, and why was removing it a security improvement?
2. What does Helm 3's three-way merge look at that Helm 2's did not, and
   what behaviour changes?
3. Does `helm rollback` restore the data in a PersistentVolume? What does it
   restore?
