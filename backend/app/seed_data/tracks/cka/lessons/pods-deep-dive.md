## What a Pod actually is

A Pod is one or more containers that share:

- a **network namespace** - one IP address, one port space, so containers in the
  Pod reach each other on `localhost`;
- **storage volumes** that any of them can mount;
- a **lifecycle** - they are scheduled together onto one node, and they live and
  die together.

It is the smallest unit Kubernetes schedules. You almost never create one
directly in production; you create a Deployment, which creates a ReplicaSet,
which creates Pods. But everything above is just a wrapper around this shape.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web
  labels:
    app: web
spec:
  containers:
    - name: nginx
      image: nginx:1.27
      ports:
        - containerPort: 80
      resources:
        requests:
          memory: "64Mi"
          cpu: "250m"
        limits:
          memory: "128Mi"
          cpu: "500m"
```

## Multi-container patterns

Put a second container in a Pod only when it must share the network or
filesystem with the first.

**Sidecar** - extends the main container. A log shipper reading a shared volume:

```yaml
spec:
  volumes:
    - name: logs
      emptyDir: {}
  containers:
    - name: app
      image: myapp:1.0
      volumeMounts:
        - name: logs
          mountPath: /var/log/app
    - name: log-shipper
      image: fluent-bit:3.0
      volumeMounts:
        - name: logs
          mountPath: /var/log/app
          readOnly: true
```

**Ambassador** - proxies outbound connections, so the app connects to
`localhost:6379` and the ambassador handles sharding or TLS.

**Adapter** - reshapes the app's output into a standard format, for example
exposing `/metrics` in Prometheus format from a legacy log file.

:::warning
If two containers do not need to share a network namespace or a volume, they
belong in separate Pods. Bundling them means they scale together, restart
together, and are scheduled together - almost always the wrong trade.
:::

## Init containers

Run to completion, in order, **before** any app container starts. If one fails,
the kubelet restarts the Pod according to its restart policy.

```yaml
spec:
  initContainers:
    - name: wait-for-db
      image: busybox:1.36
      command:
        - sh
        - -c
        - 'until nc -z postgres 5432; do echo waiting; sleep 2; done'
    - name: run-migrations
      image: myapp:1.0
      command: ["/app/migrate"]
  containers:
    - name: app
      image: myapp:1.0
```

A Pod stuck in `Init:0/2` means the first init container has not finished. Read
its logs specifically:

```bash
kubectl logs <pod> -c wait-for-db
```

## The Pod lifecycle

`status.phase` has five values:

| Phase | Meaning |
| --- | --- |
| `Pending` | Accepted, but not all containers are running - awaiting scheduling, image pull, or init containers |
| `Running` | Bound to a node, at least one container running |
| `Succeeded` | All containers exited 0 and will not restart |
| `Failed` | All containers terminated, at least one non-zero |
| `Unknown` | The node's kubelet cannot be reached |

`restartPolicy` controls what happens on exit:

- `Always` (default, and the only option for Deployments)
- `OnFailure` - used by Jobs
- `Never` - used for one-shot debugging Pods

## Probes: telling Kubernetes what "healthy" means

Three probes, three different jobs. Confusing them is a classic exam trap.

```yaml
spec:
  containers:
    - name: app
      image: myapp:1.0
      startupProbe:                 # "has it finished booting?"
        httpGet: {path: /healthz, port: 8080}
        failureThreshold: 30
        periodSeconds: 5            # allows up to 150s to start
      livenessProbe:                # "should I kill and restart it?"
        httpGet: {path: /healthz, port: 8080}
        initialDelaySeconds: 10
        periodSeconds: 10
        failureThreshold: 3
      readinessProbe:               # "should it receive traffic?"
        httpGet: {path: /ready, port: 8080}
        periodSeconds: 5
```

- **liveness** fails -> the container is **restarted**.
- **readiness** fails -> the Pod is **removed from Service endpoints**, but keeps
  running.
- **startup** fails -> the container is restarted; while it is running, liveness
  and readiness are disabled.

Probe handlers can be `httpGet`, `tcpSocket`, `exec`, or `grpc`.

:::exam-tip
A liveness probe that calls a dependency (the database, another service) causes
cascading restarts across your whole cluster the moment that dependency has a
blip. Liveness should test *only* the process itself. Readiness is where
dependency checks belong.
:::

## Resources: requests and limits

```yaml
resources:
  requests:                # used by the scheduler to pick a node
    cpu: "250m"            # 250 millicores = 0.25 of a core
    memory: "64Mi"
  limits:                  # enforced at runtime by the kernel
    cpu: "500m"
    memory: "128Mi"
```

- Exceeding the **CPU limit** throttles the container. It is not killed.
- Exceeding the **memory limit** gets the container **OOMKilled** and restarted.
- Requests, not limits, determine scheduling. A node with no free *requested*
  capacity will not take your Pod even if it is idle.

## Why Pods get stuck: the reference table

| Status | Cause | First command |
| --- | --- | --- |
| `Pending` | No node fits: insufficient resources, taints, node selector, unbound PVC | `kubectl describe pod` -> Events |
| `ContainerCreating` | Image pull in progress, or a volume will not mount | `kubectl describe pod` -> Events |
| `ImagePullBackOff` / `ErrImagePull` | Bad image name/tag, private registry without imagePullSecret | `kubectl describe pod` |
| `CrashLoopBackOff` | Container starts then exits repeatedly | `kubectl logs --previous` |
| `OOMKilled` | Memory limit exceeded | `kubectl describe pod` -> Last State |
| `Init:0/2` | An init container has not completed | `kubectl logs -c <init-name>` |
| `Terminating` (stuck) | Finalizer, or a process ignoring SIGTERM | `kubectl describe`, then `--force --grace-period=0` |
| `Completed` | Container exited 0 with `restartPolicy: Always` | Expected for Jobs; a bug otherwise |

```bash
# The OOMKill evidence lives in Last State, not in the logs
kubectl describe pod app | grep -A5 'Last State'
# Last State:     Terminated
#   Reason:       OOMKilled
#   Exit Code:    137
```

:::tip
Exit code 137 = 128 + 9 (SIGKILL) = almost always OOM. Exit code 143 = 128 + 15
(SIGTERM) = a normal shutdown. Recognising these two on sight saves real time.
:::

## Graceful shutdown

```yaml
spec:
  terminationGracePeriodSeconds: 30
  containers:
    - name: app
      image: myapp:1.0
      lifecycle:
        preStop:
          exec:
            command: ["sh", "-c", "sleep 5"]
```

On deletion Kubernetes: removes the Pod from Service endpoints, runs `preStop`,
sends `SIGTERM`, waits up to the grace period, then sends `SIGKILL`. That
`sleep 5` gives load balancers time to stop sending new connections before the
process starts refusing them.

## Check yourself

1. A Pod is `Running` but receives no traffic through its Service. Which probe do
   you check first?
2. What is the difference between a resource request and a resource limit for CPU?
3. Your Pod shows `CrashLoopBackOff`. Give the exact command that shows why.
