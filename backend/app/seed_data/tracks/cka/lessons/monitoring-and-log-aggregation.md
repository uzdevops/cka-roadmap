## Where container logs come from

A container's stdout and stderr are captured by the container runtime and
written to a file on the node - `/var/log/pods/<namespace>_<pod>_<uid>/<container>/0.log`
with containerd. The kubelet reads that file when the API server asks, and
`kubectl logs` is the API server asking. Nothing is aggregated, shipped or
kept beyond what the node holds; log rotation on the node decides how far
back you can see.

```
container stdout/stderr ──▶ containerd ──▶ /var/log/pods/.../0.log ──▶ kubelet ──▶ API server ──▶ kubectl logs
```

Two consequences to internalise:

- An application that writes to a **file** inside the container produces no
  `kubectl logs` output at all. The fix is to log to stdout, or to add a
  sidecar that tails the file (multi-container lesson).
- When the Pod is **deleted**, its logs are gone from Kubernetes' point of
  view. Anything you need later has to be shipped somewhere - that is what
  Fluentd/Fluent Bit DaemonSets with Elasticsearch or Loki are for, and it is
  outside the exam.

## The command and its flags

```bash
kubectl logs web                          # one container Pod: the whole log
kubectl logs web -c sidecar               # a specific container
kubectl logs web --all-containers         # every container, prefixed
kubectl logs web -f                       # follow
kubectl logs web --tail=50
kubectl logs web --since=10m              # or --since-time=2026-08-20T10:00:00Z
kubectl logs web --timestamps
kubectl logs web --previous               # the PREVIOUS instance, after a crash/restart
kubectl logs -l app=web                   # every Pod with the label (one at a time unless --prefix)
kubectl logs -l app=web --prefix --tail=20
kubectl logs deployment/web               # a Pod of the Deployment (picks one)
kubectl logs job/backup
```

:::exam-tip
`--previous` is the flag that answers "why did it crash". A container in
`CrashLoopBackOff` restarts every few seconds; its *current* log is the
first lines of a fresh start, and the error that killed it is in the
*previous* instance's log. `kubectl logs <pod> --previous` first, always.
:::

```bash
kubectl logs webapp-2 -c simple-webapp | grep -i "warning\|error"
kubectl logs webapp-1 | grep -i "login failed"
```

Most exam tasks here are grep problems: find the user, the error, the line.
Combine with `--tail` and `--since` when a log is large.

## When kubectl logs gives nothing

| Symptom | Cause | Move |
|---|---|---|
| empty output, app is running | app logs to a file, not stdout | `kubectl exec <pod> -- cat /var/log/app.log`, add a sidecar |
| `Error from server: ... container "x" in pod is waiting to start` | container never started (image pull, init container) | `kubectl describe pod` - Events |
| `a container name must be specified` | multi-container Pod | `-c <name>`, or `--all-containers` |
| `error dialing backend` / timeout | API server cannot reach the kubelet on 10250 | kubelet down, firewall, wrong `--kubelet-client-*` certs |

On the node itself, bypassing the API server:

```bash
crictl ps -a                      # find the container id
crictl logs <id> --tail 50
ls /var/log/pods/                 # the raw files
journalctl -u kubelet             # the kubelet's own log - not a container
```

Control plane components are static Pods, so `kubectl logs
kube-apiserver-controlplane -n kube-system` works while the API server is up -
and `crictl logs` on the node when it is not.

## Events are logs too

```bash
kubectl get events -n payroll --sort-by=.lastTimestamp
kubectl get events --field-selector type=Warning -A
kubectl describe pod web | tail -15
```

Events are the *cluster's* log about an object - scheduled, pulled, started,
probe failed, OOMKilled, evicted. They expire after an hour by default, so
read them while they are there.

:::tip
`kubectl logs` accepts `--since` and `--tail` together; `--since=1h
--tail=100` means "the last hundred lines from the last hour", which is
almost always the view you want on a chatty container.
:::

## Check yourself

1. A container is in `CrashLoopBackOff`. Which exact command shows the error
   that is killing it?
2. An application writes its log to `/var/log/app.log` inside the container.
   What does `kubectl logs` show, and what are your two options?
3. The API server is down. How do you read the API server's own log?
