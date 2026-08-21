## Three names for the same mechanism

Every multi-container Pod uses the same three things - shared network,
shared volumes, shared lifecycle. The *patterns* are just which direction
the helper faces.

```
          ┌──────────── Pod ─────────────┐
Sidecar   │  app ──volume──▶ helper      │  helper works alongside (logs, sync, certs)
Adapter   │  app ──▶ helper ──▶ outside  │  helper reshapes what the app emits
Ambassador│  outside ◀── helper ◀── app  │  helper reshapes what the app consumes
          └──────────────────────────────┘
```

## Sidecar

A helper that extends the app without the app knowing: tail its log file and
ship it, watch a Git repo and sync files into a shared volume, renew a TLS
certificate into a volume the app reads, or run a service-mesh proxy.

```yaml
containers:
  - name: web
    image: nginx
    volumeMounts: [{name: html, mountPath: /usr/share/nginx/html}]
  - name: git-sync
    image: registry.k8s.io/git-sync/git-sync:v4
    args: ["--repo=https://github.com/example/site", "--root=/tmp/git"]
    volumeMounts: [{name: html, mountPath: /tmp/git}]
volumes:
  - name: html
    emptyDir: {}
```

## Adapter

The app produces output in *its* format; the adapter converts it to what the
outside expects. The classic: an application exposes metrics in a custom
format, the adapter (a Prometheus exporter) reads them over `localhost` and
re-exposes them in Prometheus format on another port. The platform scrapes
the adapter; the app is untouched.

## Ambassador

The mirror image: the app talks to `localhost:port` and the ambassador
forwards to the real destination - a database proxy that handles TLS and
failover, a connection pooler, a cloud SQL proxy. The app is configured once
("database is at localhost:5432") and the ambassador carries the environment
differences.

:::exam-tip
The exam does not grade pattern names. It grades YAML: a second entry under
`containers`, a shared `emptyDir`, the right `volumeMounts` in both, `-c` on
`logs`/`exec`. Recognising "this is a sidecar task" just tells you that shape
is what is wanted.
:::

## Native sidecars: init containers that keep running

Since Kubernetes 1.29 there is a first-class way to express "a helper that
must start before the app and may outlive it": an **init container with
`restartPolicy: Always`**.

```yaml
spec:
  initContainers:
    - name: log-shipper
      image: fluent/fluent-bit:2.2
      restartPolicy: Always          # <- makes it a sidecar, not a one-shot init
      volumeMounts: [{name: logs, mountPath: /var/log/app}]
  containers:
    - name: app
      image: myapp:1.0
      volumeMounts: [{name: logs, mountPath: /var/log/app}]
  volumes:
    - name: logs
      emptyDir: {}
```

What it fixes compared to a plain second container:

| | second `containers` entry | native sidecar (init + `restartPolicy: Always`) |
|---|---|---|
| start order | no guarantee | starts **before** the app containers, and must be started (not complete) before they begin |
| stop order | no guarantee | stopped **after** the app containers |
| Jobs | a sidecar keeps the Job Pod alive forever | the Job completes when the app container exits |
| restarts | per restartPolicy | always restarted |

Use it whenever the helper has to be up before the app talks to it (a proxy,
a secrets agent) - which is most of the time.

## Check yourself

1. A metrics exporter that reads the app over localhost and re-exposes
   Prometheus metrics - which pattern, and why?
2. What makes an init container a "native sidecar", and what ordering
   guarantee does that buy?
3. Why does a traditional sidecar break a Job, and how does the native form
   fix it?
