## Four ways to tell a container how to behave

An image is fixed; an application is not. The same nginx image serves a
thousand different sites because configuration is injected at run time.
Kubernetes gives you four levers, and this week's lessons take them one at a
time. This page is the map.

| Lever | What it changes | Where it lives in the Pod spec |
|---|---|---|
| **command / args** | what process starts, with which arguments | `containers[].command`, `containers[].args` |
| **environment variables** | key=value visible to the process | `containers[].env`, `containers[].envFrom` |
| **ConfigMaps** | non-secret configuration: values, or whole files | referenced from `env`/`envFrom`, or mounted as a volume |
| **Secrets** | the same, for credentials and keys | same shapes as ConfigMaps, different kind and handling |

```yaml
spec:
  containers:
    - name: app
      image: myapp:2.0
      command: ["python", "server.py"]          # ENTRYPOINT equivalent
      args: ["--port", "8080"]                  # CMD equivalent
      env:
        - name: MODE
          value: production                     # literal
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:                    # one key from a ConfigMap
              name: app-config
              key: db_host
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:                       # one key from a Secret
              name: db-secret
              key: password
      envFrom:
        - configMapRef:
            name: app-config                    # every key as an env var
      volumeMounts:
        - name: config
          mountPath: /etc/app                   # every key as a file
  volumes:
    - name: config
      configMap:
        name: app-config
```

Read that once as a whole, then the next lessons fill in each block.

## Which lever for which job

- The process or its flags differ per environment → **command/args**.
- A handful of scalar settings → **env** (literals, or from a ConfigMap).
- A configuration *file* the application reads (`nginx.conf`, `application.properties`) → **ConfigMap mounted as a volume**.
- Anything sensitive → the **Secret** variants of the same two shapes.

Two rules that save you from the common mistakes:

1. **Environment variables are read once, at process start.** Change the
   ConfigMap and a running Pod's env does not change; the Pod has to be
   recreated (a Deployment rollout does that). Mounted files *do* update in
   place, after a short delay - unless mounted with `subPath`.
2. **Secrets are not encryption.** They are base64 in the API and plain on
   the etcd disk unless you configure encryption at rest. Treat RBAC on
   Secrets and the etcd disk as the real controls.

:::exam-tip
Nearly every task in this area says either "inject X as an environment
variable" or "mount X at /path". Decide which shape it is before you open
the editor; the YAML for the two is different enough that starting with the
wrong one costs a rewrite.
:::

## What happens at container start, in order

1. Volumes (including ConfigMap and Secret volumes) are mounted.
2. The environment is assembled: `env` and `envFrom` are resolved; a missing
   ConfigMap or Secret key makes the container fail with
   `CreateContainerConfigError` - `kubectl describe pod` names the key.
3. `command` and `args` are combined and executed.

That third step is the subject of the next two lessons: how Docker's
`ENTRYPOINT` and `CMD` map onto `command` and `args`, and what overrides what.

## Check yourself

1. You change a value in a ConfigMap that a Pod consumes as an environment
   variable. What does the running Pod see, and what do you do about it?
2. Which Pod field corresponds to a Dockerfile's `CMD`?
3. A Pod is stuck in `CreateContainerConfigError`. What is the most likely
   cause, and where is the exact name of the problem printed?
