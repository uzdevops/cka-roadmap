## Run this first, to completion

An **init container** runs before the app containers, must exit successfully,
and is then done. Several run **one after another, in order**; the app
containers do not start until the last init container has exited 0. Use them
for what the app needs to be true before it starts: a schema migration, a
config file rendered from a template, a wait-for-dependency loop, a file
downloaded into a shared volume.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  initContainers:
    - name: wait-for-db
      image: busybox:1.36
      command: ["sh", "-c", "until nslookup db.payroll.svc.cluster.local; do echo waiting; sleep 2; done"]
    - name: fetch-config
      image: busybox:1.36
      command: ["sh", "-c", "wget -O /work/app.conf http://config-svc/app.conf"]
      volumeMounts: [{name: work, mountPath: /work}]
  containers:
    - name: app
      image: myapp:1.0
      volumeMounts: [{name: work, mountPath: /etc/app}]
  volumes:
    - name: work
      emptyDir: {}
```

Init containers are ordinary containers in every other way: their own image,
command, resources, volume mounts. They can have tools the app image lacks
(curl, nslookup, a migration CLI) - that is one of the best reasons to use
them.

## What you see while they run

```bash
kubectl get pod app
# NAME   READY   STATUS     RESTARTS   AGE
# app    0/1     Init:0/2   0          5s      <- 0 of 2 init containers done
# app    0/1     Init:1/2   0          12s
# app    0/1     PodInitializing
# app    1/1     Running
```

| STATUS | Meaning |
|---|---|
| `Init:0/2` | the first of two init containers is running |
| `Init:Error` | an init container exited non-zero |
| `Init:CrashLoopBackOff` | it keeps failing; the kubelet is backing off between retries |
| `PodInitializing` | init done, app containers being created |

```bash
kubectl describe pod app | grep -A12 "Init Containers:"
kubectl logs app -c wait-for-db             # init container logs, by name
kubectl logs app -c wait-for-db --previous  # the failed attempt
```

:::exam-tip
A Pod stuck in `Init:...` is an init-container problem, nothing to do with
the app container - and `kubectl logs <pod>` without `-c` will *not* show you
the init container (it shows the app, which has not started, and errors). The
fix is always `kubectl logs <pod> -c <init-name>` and, nine times out of ten,
a typo in the init command. `sleeeep`, a wrong Service name, a missing scheme
in a URL.
:::

## Restart semantics

If an init container fails, the kubelet restarts **it** (subject to the
Pod's `restartPolicy`; with `Never` the whole Pod fails). When it eventually
succeeds, the next init container runs. If the *Pod* restarts - node reboot,
eviction and recreate - **all** init containers run again from the first,
so they should be idempotent: "create the table if it does not exist", not
"create the table".

## What init containers are not

- They are not for things that must keep running. A helper that should stay
  up alongside the app is a sidecar - or a native sidecar (init container
  with `restartPolicy: Always`, previous lesson), which is the modern way to
  get "start first" *and* "keep running".
- They do not have readiness probes (they are done when they exit) - but they
  can have resource requests, and the Pod's effective request is the **max**
  of (largest init container, sum of app containers), because they never run
  at the same time as the app.

## Adding one to an existing Pod

`initContainers` is immutable on a running Pod:

```bash
kubectl get pod red -o yaml > red.yaml
# add spec.initContainers: [{name: warm-up, image: busybox, command: [sleep, "20"]}]
kubectl replace --force -f red.yaml
kubectl get pod red -w                    # Init:0/1 for 20 s, then Running
```

## Check yourself

1. In what order do two init containers and two app containers start, and
   what does each wait for?
2. A Pod shows `Init:CrashLoopBackOff`. Which exact command shows you the
   reason?
3. Why should an init container's work be idempotent?
