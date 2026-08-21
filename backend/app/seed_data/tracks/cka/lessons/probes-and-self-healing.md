## Three layers of healing

Kubernetes does not know what "healthy" means for your application. It knows
three mechanical things, at three levels, and you tell it how to use them.

| Layer | Mechanism | Repairs |
|---|---|---|
| container | `restartPolicy` + probes | a process that exited or stopped answering |
| Pod set | ReplicaSet / Deployment | a Pod that is gone (node died, evicted, deleted) |
| node | node controller + eviction | a node that stopped reporting |

This lesson is the first layer. The second you already know; the third is the
`node.kubernetes.io/not-ready` toleration you met in the taints lesson.

## restartPolicy

```yaml
spec:
  restartPolicy: Always      # default: restart the container whenever it exits
  # OnFailure                # restart only on non-zero exit - Jobs
  # Never                    # leave it - Jobs that must not retry, one-shot debugging
```

It applies to **all** containers in the Pod and is immutable. With `Always`,
a crashing container is restarted with exponential back-off (10 s, 20 s, 40 s
... capped at 5 min) - the `CrashLoopBackOff` state is the *waiting* between
those restarts, not a separate failure.

## Probes

The kubelet can ask a container how it is doing, three different ways, for
three different purposes:

| Probe | Question | On failure |
|---|---|---|
| **liveness** | is the process alive and not wedged? | restart the container |
| **readiness** | can it take traffic *right now*? | remove the Pod from Service endpoints (no restart) |
| **startup** | has it finished starting yet? | keep waiting; liveness/readiness are held off until it passes |

```yaml
containers:
  - name: api
    image: myapi:2.0
    ports: [{containerPort: 8080}]
    startupProbe:
      httpGet: {path: /healthz, port: 8080}
      failureThreshold: 30         # 30 x 5 s = 2.5 min allowed to start
      periodSeconds: 5
    livenessProbe:
      httpGet: {path: /healthz, port: 8080}
      periodSeconds: 10
      failureThreshold: 3          # three misses in a row -> restart
    readinessProbe:
      httpGet: {path: /ready, port: 8080}
      periodSeconds: 5
```

Three ways to probe:

```yaml
httpGet: {path: /healthz, port: 8080}                # 200-399 = success
tcpSocket: {port: 5432}                               # connection accepted = success
exec: {command: ["cat", "/tmp/healthy"]}              # exit 0 = success
grpc: {port: 9090}                                    # gRPC health protocol
```

Timing knobs on every probe: `initialDelaySeconds`, `periodSeconds`,
`timeoutSeconds`, `successThreshold`, `failureThreshold`.

## The two mistakes

**A liveness probe that is too strict.** If the app is slow under load and
the probe times out, the kubelet restarts it - making the load worse -
restarts it again, and you have turned a slow service into a dead one. Make
liveness cheap and local ("is the process responsive"), never "can I reach
the database". That belongs in readiness.

**No readiness probe.** Without one, a Pod is Ready the moment its
containers start, and the Service sends traffic to an app that is still
loading - or, during a rolling update, to new Pods before they work, so the
rollout "succeeds" and users see errors. Readiness is what makes
`maxUnavailable: 0` mean something.

:::exam-tip
"Pods are Running but the Service returns errors / has no endpoints" - look
at READY: `0/1` with `Running` means the readiness probe is failing, and
`kubectl describe pod` shows `Readiness probe failed: ...` with the HTTP code
or connection error. A wrong path or port in the probe is the usual cause.
:::

## Reading probe trouble

```bash
kubectl get pods                    # READY 0/1 Running = readiness; RESTARTS climbing = liveness
kubectl describe pod api | grep -E "Liveness|Readiness|Startup" -A1
kubectl describe pod api | tail -8  # Warning  Unhealthy  Liveness probe failed: HTTP probe failed with statuscode: 500
kubectl get events --field-selector reason=Unhealthy
```

## Self-healing, put together

A Deployment with three replicas, readiness and liveness probes, running on
nodes with default tolerations:

- container wedges → liveness fails → kubelet restarts it;
- container starting up → readiness fails → no traffic until it is ready;
- Pod deleted or node dies → ReplicaSet creates a replacement; node controller
  evicts after 5 minutes NotReady;
- during a rollout, new Pods take traffic only once ready, old ones are kept
  until then.

None of it needs an operator awake. That is the promise, and probes are what
make it true.

## Check yourself

1. A liveness probe fails three times. What happens? A readiness probe fails
   three times. What happens instead?
2. Why is "can I reach the database" a bad liveness check and a reasonable
   readiness check?
3. A Pod is `Running` with `READY 0/1` and zero restarts. Which probe, and
   which command shows why?
