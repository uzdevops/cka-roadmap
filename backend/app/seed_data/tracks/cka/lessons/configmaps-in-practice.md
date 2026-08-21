## Configuration as an object

A ConfigMap is a namespaced bag of key/value strings. Its only job is to
hold non-secret configuration *outside* the image and outside the Pod spec,
so that the same Deployment can read different values in dev and prod, and so
that a change to configuration is a change to one object rather than an edit
of every Pod template.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_COLOR: blue
  APP_MODE: prod
  nginx.conf: |                     # a whole file is just a multi-line value
    server {
      listen 80;
      location / { return 200 'ok'; }
    }
```

## Creating one

```bash
# literals
kubectl create configmap app-config --from-literal=APP_COLOR=blue --from-literal=APP_MODE=prod

# a file: key = file name, value = contents
kubectl create configmap nginx-conf --from-file=nginx.conf
kubectl create configmap nginx-conf --from-file=site.conf=nginx.conf     # rename the key

# every file in a directory
kubectl create configmap all-conf --from-file=./conf/

# key=value lines from an env-style file
kubectl create configmap app-env --from-env-file=app.env

kubectl create configmap app-config --from-literal=A=1 $do > cm.yaml   # generate, then apply
kubectl get configmap app-config -o yaml
kubectl describe configmap app-config
```

## Consuming one - three shapes

**1. One key, one environment variable**

```yaml
env:
  - name: APP_COLOR
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: APP_COLOR
```

**2. Every key as environment variables**

```yaml
envFrom:
  - configMapRef:
      name: app-config
```

**3. Keys as files in a directory**

```yaml
volumes:
  - name: config
    configMap:
      name: app-config
      # items:                       # optional: only some keys, renamed
      #   - key: nginx.conf
      #     path: default.conf
containers:
  - name: web
    volumeMounts:
      - name: config
        mountPath: /etc/nginx/conf.d
        readOnly: true
```

Each key becomes a file named after the key, containing the value. This is
the shape for configuration *files*.

```bash
kubectl exec web -- ls /etc/nginx/conf.d
kubectl exec web -- cat /etc/nginx/conf.d/nginx.conf
```

:::exam-tip
A mounted ConfigMap **replaces the directory** it is mounted on - everything
that was in the image at `/etc/nginx/conf.d` disappears, you see only the
ConfigMap's keys. If you need to add one file without hiding the others,
mount with `subPath`:

```yaml
volumeMounts:
  - name: config
    mountPath: /etc/nginx/conf.d/default.conf
    subPath: nginx.conf
```

- and know that `subPath` mounts do **not** update when the ConfigMap changes.
:::

## Updating, and what notices

| Consumed as | After you edit the ConfigMap |
|---|---|
| env var | nothing changes until the Pod is recreated |
| volume (directory) | files update in place within a minute or so; the app must re-read them |
| volume with `subPath` | nothing changes until the Pod is recreated |

For a Deployment the reliable way to propagate a change is `kubectl rollout
restart deployment/web`. Some teams put a hash of the ConfigMap in a Pod
template annotation so that `apply` rolls automatically; Kustomize does that
for you with `configMapGenerator`.

```yaml
immutable: true        # on the ConfigMap: no edits allowed; delete and recreate instead
```

Immutable ConfigMaps are cheaper for the kubelet (it stops watching them) and
protect against accidental live edits; the trade-off is exactly that you
cannot edit them.

## Limits and gotchas

- A ConfigMap is capped at **1 MiB**. Bigger configuration belongs in a
  volume of another kind.
- It is **namespaced**: a Pod can only reference ConfigMaps in its own
  namespace.
- A missing ConfigMap named in `env`/`volumes` blocks the container:
  `CreateContainerConfigError` / `ContainerCreating` forever, with the name in
  `describe pod` events. `optional: true` changes that to "start without it".
- Binary data goes in `binaryData` (base64), not `data`.

## Check yourself

1. Give the `kubectl create configmap` command that turns a file `app.properties`
   into a ConfigMap key of the same name.
2. You mount a ConfigMap at `/etc/app` and the image's own files under
   `/etc/app` vanish. Why, and what mounts a single file instead?
3. Which of the three consumption shapes picks up a ConfigMap edit without a
   Pod restart?
