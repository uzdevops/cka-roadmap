## When two containers belong together

One container per Pod is the rule. The exception is when two processes need
to share a **lifecycle**, a **network namespace** and **storage** so closely
that running them apart would mean reinventing all three: a log shipper that
tails the app's file, a proxy that sits in front of the app on localhost, an
agent that refreshes a certificate the app reads.

A multi-container Pod gives them exactly that:

- **same network namespace** - they share one IP and one port space; they
  talk over `localhost`; they cannot both bind port 8080;
- **shared volumes** - any volume in the Pod can be mounted in both;
- **one lifecycle** - scheduled together, onto one node; started together;
  the Pod is Ready when *all* are; deleted together.

They do **not** share a filesystem (only explicitly mounted volumes), a
process namespace by default, or resource limits (each container has its
own).

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
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
      image: fluent/fluent-bit:2.2
      volumeMounts:
        - name: logs
          mountPath: /var/log/app
          readOnly: true
```

The app writes to `/var/log/app/app.log`; the shipper reads the same file
through the shared `emptyDir`. Neither knows the other exists.

## Working with them

```bash
kubectl get pod app                      # READY 2/2
kubectl describe pod app | grep -A2 "Containers:"
kubectl logs app -c log-shipper          # -c is required once there are two
kubectl logs app --all-containers --prefix
kubectl exec app -c app -- ls /var/log/app
kubectl get pod app -o jsonpath='{.spec.containers[*].name}'
```

`READY 1/2` means one container is not ready - `describe` says which and
why. A crash in either container restarts that container, not the Pod, and
`RESTARTS` counts per container.

:::exam-tip
Two exam shapes: "add a sidecar container `X` with image `Y` to Pod `Z`" -
the Pod's container list is immutable, so it is `kubectl get pod Z -o yaml`,
add the container, `kubectl replace --force`. And "this multi-container Pod
is not Ready" - `kubectl describe` shows one container failing, usually a
wrong image or a command that exits.
:::

## Where `emptyDir` fits

`emptyDir` is the volume type built for this: an empty directory created when
the Pod starts, living as long as the Pod, shared between its containers.
Scratch space, log hand-off, a build artefact passed from an init container to
the app. `emptyDir: {medium: Memory}` puts it on tmpfs.

## Sharing more than volumes

```yaml
spec:
  shareProcessNamespace: true
```

With this, containers see each other's processes (`ps` in one shows the
other's), which makes debugging sidecars and signal-based coordination
possible. Off by default.

## When not to do it

If the two things scale independently, restart independently, or are owned
by different teams, they are two Deployments with a Service between them -
not two containers in one Pod. The test is the lifecycle: if you would ever
want to restart or scale one without the other, split them.

## Check yourself

1. Name three things containers in one Pod share and two things they do not.
2. Which command reads the logs of a specific container in a multi-container
   Pod?
3. A Pod shows `READY 1/2`. What does that mean, and what is the first
   command?
