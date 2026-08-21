## A release over time

Install, upgrade, something breaks, roll back, upgrade again, uninstall:
that is the life of a release, and Helm numbers every step.

```bash
helm install nginx-release bitnami/nginx --version 15.9.0
helm list
# NAME            REVISION  STATUS    CHART         APP VERSION
# nginx-release   1         deployed  nginx-15.9.0  1.25.3
```

## upgrade

```bash
helm upgrade nginx-release bitnami/nginx --version 18.1.0
helm list
# nginx-release   2         deployed  nginx-18.1.0  1.27.0
helm history nginx-release
# REVISION  STATUS      CHART         APP VERSION  DESCRIPTION
# 1         superseded  nginx-15.9.0  1.25.3       Install complete
# 2         deployed    nginx-18.1.0  1.27.0       Upgrade complete
kubectl get pods                         # new Pods with the new image, via the Deployment's rollout
```

Helm computes the difference between the two rendered manifests (and the
live objects - the three-way merge) and applies only what changed. A
Deployment with a new image rolls; a ConfigMap with new data is updated;
an object that disappeared from the chart is deleted.

## rollback

```bash
helm rollback nginx-release 1
helm history nginx-release
# 1   superseded   nginx-15.9.0   Install complete
# 2   superseded   nginx-18.1.0   Upgrade complete
# 3   deployed     nginx-15.9.0   Rollback to 1
```

Revision 3 is a new revision with revision 1's manifests. The Deployment
rolls back to the old image; ConfigMaps and Services return to their old
content.

**What rollback does not restore**: anything that is not a Kubernetes
object Helm created. A database chart upgraded from 15.x to 16.x may have
migrated the data on its PersistentVolume; rolling the chart back brings the
old image, which cannot read the new data format. For stateful charts:
backup before upgrade, and read the chart's upgrade notes.

## The revision record

```bash
helm get manifest nginx-release --revision 2        # what revision 2 applied
helm get values nginx-release --revision 1
helm diff revision nginx-release 1 2                 # helm-diff plugin: the change between two revisions
kubectl get secrets -l owner=helm,name=nginx-release
# sh.helm.release.v1.nginx-release.v1
# sh.helm.release.v1.nginx-release.v2
# sh.helm.release.v1.nginx-release.v3
```

`--history-max 10` (the default) keeps the last ten revisions; older Secrets
are pruned.

## hooks and tests

Charts can run Jobs at lifecycle points - `pre-upgrade` (a schema migration),
`post-install` (register with something), `pre-delete` (a backup). They are
ordinary manifests in `templates/` with an annotation:

```yaml
metadata:
  annotations:
    "helm.sh/hook": pre-upgrade
    "helm.sh/hook-weight": "0"
    "helm.sh/hook-delete-policy": hook-succeeded
```

A failed hook fails the upgrade (`helm history` shows `failed`; the release
stays on the previous revision's objects). And `helm test <release>` runs the
chart's `templates/tests/` Pods - a smoke test you can run after any
upgrade.

```bash
helm test nginx-release
helm upgrade nginx-release bitnami/nginx --atomic        # roll back automatically if the upgrade fails
helm upgrade nginx-release bitnami/nginx --wait --timeout 3m
```

`--atomic` is the production habit: a failed upgrade (hook failure, Pods
never Ready within `--timeout`) is rolled back in the same command.

## uninstall

```bash
helm uninstall nginx-release
helm uninstall nginx-release --keep-history     # keep the revision Secrets; `helm history` still works; `helm rollback` can resurrect
helm list -a                                    # uninstalled releases with kept history show as `uninstalled`
```

:::exam-tip
The sequence the exam tends to want: `helm upgrade` to a named chart
version, confirm with `helm list` / `helm history`, then `helm rollback
<release> <revision>` and confirm again. Two details that lose marks:
forgetting `-n` and rolling back to the **wrong revision number** - read
`helm history` first, then roll back to the revision whose CHART column is
the one the task names.
:::

## Check yourself

1. After install, upgrade and rollback, how many revisions exist and which
   is deployed?
2. What does a rollback restore, and what does it not?
3. What does `--atomic` do on an upgrade, and when would you not want it?
