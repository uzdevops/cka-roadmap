## A package manager for Kubernetes

Installing WordPress on a cluster by hand means a Deployment, a Service, a
PersistentVolumeClaim, a Secret for the database password, a second
Deployment and Service for MariaDB, its own PVC and Secret, maybe an
Ingress - eight or nine manifests that have to agree with each other on
names, labels, ports and passwords. Upgrading means editing all of them;
removing means remembering all of them.

Helm treats that whole set as **one thing**, the way `apt` treats a
program's files as one package:

```bash
helm install my-site bitnami/wordpress --set wordpressPassword=secret
helm upgrade my-site bitnami/wordpress --set replicaCount=2
helm rollback my-site 1
helm uninstall my-site
```

One command installs all nine objects with consistent names; one removes
them all; one upgrades and one undoes the upgrade.

## The vocabulary

| Term | Meaning |
|---|---|
| **Chart** | the package: templates for the objects + default values + metadata (`Chart.yaml`) |
| **Release** | a chart installed into a cluster under a name; install the same chart twice and you have two releases |
| **Revision** | each `install`/`upgrade`/`rollback` of a release is a numbered revision; history is kept |
| **Values** | the knobs: `values.yaml` in the chart has defaults; you override with `--set` or `-f` |
| **Repository** | an HTTP index of charts (`helm repo add`), or an OCI registry (`oci://`) |
| **Artifact Hub** | artifacthub.io - the search engine across public repositories |

```
chart (templates + values.yaml) ──render with your values──▶ YAML ──apply──▶ objects in the cluster = a release
```

## Why charts, not scripts

A shell script of `kubectl apply` commands would install WordPress too. What
the chart adds:

- **Parameterisation** - every difference between your install and mine is a
  value, not an edit.
- **Versioning** - the chart has a version, the app it installs has a
  version, and `helm upgrade` moves between them.
- **State** - Helm records what it installed (as a Secret in the namespace),
  so `upgrade` knows what to change and `uninstall` knows what to remove.
- **Hooks and tests** - run a Job before upgrade, a test after install.
- **Distribution** - `helm repo add` and you have a thousand charts.

## Helm's place in the ecosystem

Most cluster add-ons ship as charts: ingress-nginx, cert-manager,
metrics-server, Prometheus (kube-prometheus-stack), Argo CD, the CSI
drivers, the cloud controllers. "Install X" in a README is, more often than
not, three Helm lines. That is why the CKA put it on the curriculum - not to
write charts, but to install and manage components with them.

```bash
helm search hub wordpress                  # Artifact Hub, from the CLI
helm search repo bitnami/nginx             # a repository you added
helm show values bitnami/wordpress | less  # every knob a chart exposes
```

:::tip
`helm show values <chart>` is the command that turns "how do I configure
this" into "which of these keys do I set". Pipe it to a file, keep the three
lines you changed as your `values.yaml`, and commit that.
:::

## Check yourself

1. What is the difference between a chart and a release?
2. Name three things Helm gives you that a script of `kubectl apply`
   commands does not.
3. Which command shows every configurable value of a chart?
