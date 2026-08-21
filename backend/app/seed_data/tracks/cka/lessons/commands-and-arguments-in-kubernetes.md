## The mapping

| Dockerfile | Pod spec field | Meaning |
|---|---|---|
| `ENTRYPOINT` | `command` | the executable |
| `CMD` | `args` | its arguments |

The naming is the trap: Kubernetes' `command` overrides Docker's
**ENTRYPOINT**, not CMD; Kubernetes' `args` overrides Docker's **CMD**. Once
that is in your head the rest is mechanical.

Given an image built with `ENTRYPOINT ["sleep"]` and `CMD ["5"]`:

```yaml
# sleep 5  - nothing overridden
spec:
  containers:
    - name: s
      image: ubuntu-sleeper

# sleep 10 - args replaces CMD, ENTRYPOINT kept
      args: ["10"]

# sleep2.0 10 - command replaces ENTRYPOINT; args still needed, because...
      command: ["sleep2.0"]
      args: ["10"]
```

:::warning
If you set `command` and **not** `args`, the image's CMD is **dropped**, not
kept. `command: ["sleep2.0"]` alone runs `sleep2.0` with no argument. The
four cases:

| `command` | `args` | runs |
|---|---|---|
| – | – | ENTRYPOINT + CMD from the image |
| – | set | ENTRYPOINT + your args |
| set | – | your command, **no** arguments |
| set | set | your command + your args |
:::

## Writing it without mistakes

Both fields are lists of strings. Two styles that are equivalent:

```yaml
command: ["sleep", "5000"]
# or
command:
  - sleep
  - "5000"
```

The quotes around `"5000"` matter: YAML would otherwise read `5000` as a
number, and the field requires strings. Same for `"--color=green"` style
flags only when they start with a dash inside a flow list - quote them anyway
and stop thinking about it.

```bash
# generate it - the fastest correct way
kubectl run ubuntu-sleeper-2 --image=ubuntu --command -- sleep 5000 $do
#   -> command: [sleep, "5000"]   (everything after -- is the command)
kubectl run webapp-green --image=kodekloud/webapp-color -- --color=green $do
#   -> args: [--color=green]       (without --command, it is args)
```

That `--command` flag is the whole difference: with it, what follows `--`
becomes `command`; without it, `args`.

## Reading what a running Pod was given

```bash
kubectl get pod ubuntu-sleeper -o jsonpath='{.spec.containers[0].command}'
kubectl get pod ubuntu-sleeper -o jsonpath='{.spec.containers[0].args}'
kubectl describe pod ubuntu-sleeper | grep -A4 "Command:\|Args:"
```

If neither field is set, `kubectl` shows nothing - the process comes from the
image, and `crictl inspecti <image>` on a node (or `docker inspect`
elsewhere) is where you read it.

:::exam-tip
A task that says "the Pod should run the command `sleep 5000`" wants
`command: ["sleep", "5000"]` (replace the whole thing). A task that says "pass
the argument `--color=green` to the image" wants `args: ["--color=green"]`
(keep the ENTRYPOINT). Two verbs, two fields. And remember these are
immutable on a running Pod - it is delete-and-recreate.
:::

## A shell when you need one

Sometimes the command is genuinely a shell one-liner:

```yaml
command: ["/bin/sh", "-c"]
args: ["echo starting; exec myapp --port 8080"]
```

The `exec` at the end makes `myapp` replace the shell as PID 1, so signals
reach it. Without `exec`, SIGTERM goes to `sh`, which does not forward it,
and the container waits for the kill.

## Check yourself

1. Which Pod field overrides a Dockerfile's `ENTRYPOINT`, and which overrides
   `CMD`?
2. An image runs `sleep 5` by default. You set `command: ["sleep"]` and
   nothing else. What runs?
3. Write the `kubectl run` one-liner that creates a Pod from image `busybox`
   running `sleep 3600`, and the one that passes `--verbose` as an argument
   to an image's own entrypoint.
