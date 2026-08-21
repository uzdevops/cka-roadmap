## The env field

The simplest configuration there is: a name and a value, visible to the
process as an environment variable.

```yaml
spec:
  containers:
    - name: app
      image: myapp:2.0
      env:
        - name: APP_COLOR
          value: blue
        - name: APP_MODE
          value: "prod"
```

```bash
kubectl run app --image=myapp:2.0 --env=APP_COLOR=blue --env=APP_MODE=prod
kubectl exec app -- env | grep APP_
kubectl set env deployment/app APP_COLOR=green          # on a Deployment: triggers a rollout
kubectl set env deployment/app APP_COLOR-               # remove
```

Values are **strings**. `value: 8080` is a YAML integer and is rejected; write
`value: "8080"`.

## Three sources for a value

```yaml
env:
  - name: APP_COLOR
    value: blue                          # 1. literal

  - name: DB_HOST
    valueFrom:
      configMapKeyRef:                   # 2. one key from a ConfigMap
        name: app-config
        key: db_host

  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:                      # 3. one key from a Secret
        name: db-secret
        key: password
```

And a fourth that is not configuration at all but is invaluable:

```yaml
  - name: POD_NAME
    valueFrom:
      fieldRef:
        fieldPath: metadata.name         # the Pod's own name, namespace, IP, node...
  - name: CPU_LIMIT
    valueFrom:
      resourceFieldRef:
        containerName: app
        resource: limits.cpu
```

The **downward API** - a Pod learning about itself. `metadata.name`,
`metadata.namespace`, `metadata.labels['app']`, `status.podIP`,
`spec.nodeName` are the common ones.

## All keys at once: envFrom

```yaml
envFrom:
  - configMapRef:
      name: app-config           # every key in the ConfigMap becomes a variable
  - secretRef:
      name: db-secret
  - configMapRef:
      name: feature-flags
      prefix: FF_                # optional: FF_<key>
```

`envFrom` is the shortcut for "inject the whole ConfigMap". Keys that are not
valid environment variable names are skipped (with an event). If the same
name appears in `env` and `envFrom`, **`env` wins**.

:::exam-tip
"Make the Pod read `APP_COLOR` from ConfigMap `webapp-config-map`" is
`valueFrom.configMapKeyRef`. "Inject all the keys of the ConfigMap" is
`envFrom.configMapRef`. The second is shorter; use it unless the task names a
specific key or wants a different variable name than the key.
:::

## What goes wrong

| Symptom | Cause |
|---|---|
| `CreateContainerConfigError` | the ConfigMap/Secret or the **key** named in `valueFrom` does not exist - `describe pod` says which |
| the variable is set but stale | ConfigMap changed after the Pod started; env is read once at start - recreate the Pod (rollout) |
| the value is `8080` in the file but the API rejects it | must be a string: `"8080"` |
| `envFrom` silently skipped a key | the key is not a valid variable name (contains `-` or `.`) |

`optional: true` on a `configMapKeyRef`/`secretKeyRef` lets the Pod start even
if the source is missing - useful, and a trap when you wonder why a variable
is simply absent.

## Seeing the result

```bash
kubectl exec app -- env                                   # what the process sees
kubectl exec app -- printenv APP_COLOR
kubectl describe pod app | grep -A10 "Environment:"       # what was configured, with sources
kubectl get pod app -o jsonpath='{.spec.containers[0].env}'
```

:::tip
`kubectl describe` shows `<set to the key 'password' in secret 'db-secret'>`
rather than the value for Secret-sourced variables; `kubectl exec -- env`
shows the real value. Know which one a task is asking you to read.
:::

## Check yourself

1. Write the `env` entry that sets `DB_PASSWORD` from key `password` of Secret
   `db-secret`.
2. You update a ConfigMap. The Pod that reads it via `env` still shows the old
   value an hour later. Why, and how do you fix it for a Deployment?
3. Both `env` and `envFrom` define `APP_MODE` with different values. Which one
   does the container see?
