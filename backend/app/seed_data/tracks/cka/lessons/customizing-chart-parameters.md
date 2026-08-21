## Three ways to change a value

A chart's `values.yaml` is its defaults. You override them at install or
upgrade, and the overrides are what make your release yours.

```bash
helm show values bitnami/wordpress > wp-defaults.yaml      # read the knobs first
grep -n "wordpressBlogName\|replicaCount" wp-defaults.yaml
```

### 1. --set, for one or two values

```bash
helm install my-site bitnami/wordpress \
  --set wordpressBlogName="Helm Tutorials" \
  --set wordpressEmail=john@example.com \
  --set replicaCount=2
```

Nested keys use dots; list items use brackets; commas separate pairs; a
literal comma or dot needs a backslash; `--set-string` forces a string when
Helm would read a number; `--set-file key=path` reads a file's contents into
a value:

```bash
--set image.tag=1.27.1
--set ingress.hosts[0].host=shop.example.com
--set "annotations.nginx\.ingress\.kubernetes\.io/rewrite-target=/"
--set-string podAnnotations.version=123
--set-file tls.crt=./tls.crt
```

`--set` is for the exam and the terminal; it does not scale past three
values and it leaves no record in Git.

### 2. -f values.yaml, for everything else

```yaml
# my-values.yaml
wordpressBlogName: Helm Tutorials
wordpressEmail: john@example.com
replicaCount: 2
resources:
  requests: {cpu: 250m, memory: 256Mi}
ingress:
  enabled: true
  hostname: shop.example.com
```

```bash
helm install my-site bitnami/wordpress -f my-values.yaml
helm install my-site bitnami/wordpress -f base.yaml -f prod.yaml    # later files override earlier
helm upgrade my-site bitnami/wordpress -f my-values.yaml            # the same file, every time
```

Only the keys you set are overridden; everything else keeps the chart's
default. Commit this file next to your other manifests - it **is** the
configuration of the release.

### 3. Pull the chart and edit it

```bash
helm pull bitnami/wordpress --untar
cd wordpress
vim values.yaml                     # change the defaults themselves
helm install my-site ./             # install from the local, modified chart
```

Useful for a one-off or when a template needs a change the values do not
allow. The cost: you now own a fork, and `helm upgrade` to the next upstream
chart version means re-applying your edits. Prefer `-f` whenever the value
exists.

## Precedence, once more

```
chart values.yaml  <  -f file1  <  -f file2  <  --set
```

Later wins. And an `upgrade` starts from the **chart defaults** again plus
what you pass this time - pass the same `-f` file, or `--reuse-values`.

## Checking what you set

```bash
helm get values my-site                  # user-supplied values only
helm get values my-site --all            # merged with defaults
helm get values my-site --revision 1     # what revision 1 had
helm diff upgrade my-site bitnami/wordpress -f my-values.yaml    # the helm-diff plugin: what WOULD change
```

:::exam-tip
Tasks phrase it as "set the value X to Y": that is `--set X=Y` on install or
upgrade. If the task gives you a values file, `-f`. When unsure whether a
key is right, `helm show values <chart> | grep <key>` - a mistyped key is
silently ignored by most charts and the release comes up with the default,
which is the failure mode to fear.
:::

## Check yourself

1. Write a `--set` for `ingress.hosts[0].host=shop.example.com`.
2. Two `-f` files and a `--set` all define `replicaCount`. Which wins?
3. Why is editing a pulled chart's `values.yaml` usually worse than
   passing `-f`?
