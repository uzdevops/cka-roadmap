## Two ways to talk to the cluster

**Imperative**: tell the cluster what to *do*.

```bash
kubectl run web --image=nginx
kubectl create deployment api --image=myapi:1.2 --replicas=3
kubectl expose deployment api --port=80
kubectl scale deployment api --replicas=5
kubectl set image deployment/api myapi=myapi:1.3
kubectl edit deployment api
kubectl delete pod web
```

**Declarative**: tell the cluster what you *want*, in a file, and let it work
out the steps.

```bash
kubectl apply -f api.yaml          # creates it if absent, updates it if present, no-op if identical
kubectl apply -f ./manifests/      # a whole directory
```

Both end up as the same objects in etcd. The difference is who keeps track of
the desired state: with imperative commands it is in your head and your shell
history; with `apply` it is in files you can review, version and re-run.

## Imperative object configuration - the middle ground

```bash
kubectl create -f pod.yaml        # error if it exists
kubectl replace -f pod.yaml       # error if it does not exist; replaces the whole object
kubectl delete -f pod.yaml
```

You still write files, but each command is one operation and you have to
choose the right one. `apply` removes that choice.

## What `apply` actually does

`apply` is a three-way merge between:

1. the **file** you give it,
2. the **live object** in the cluster,
3. the **last applied configuration** - the file as it was the previous time
   you applied it, stored by kubectl in an annotation on the object:

```bash
kubectl get deployment api -o jsonpath='{.metadata.annotations.kubectl\.kubernetes\.io/last-applied-configuration}' | jq .
```

With all three, apply can tell the difference between "you removed this field
from your file, so delete it from the object" and "this field was never in
your file, the cluster added it, leave it alone". That is what makes repeated
applies safe and what `create`/`replace` cannot do.

:::warning
Mixing the two styles on one object is where surprises live. `kubectl scale`
changes replicas in the cluster but not in your file; the next `apply`
silently scales it back. `kubectl edit` likewise. Pick one owner per object:
either the file owns it (and you edit the file) or the CLI does.
:::

## Which to use when

| Situation | Use |
|---|---|
| the exam, one-off objects, speed | imperative - `run`, `create`, `expose` |
| anything that needs a field the flags cannot set | imperative **generate**, then edit, then `apply` |
| real environments, anything you want to keep | declarative - files in Git, `apply` |
| inspecting or nudging a live object | `describe`, `get -o yaml`, `edit`, `scale`, `set image` |

The exam habit that covers everything:

```bash
kubectl create deployment api --image=myapi:1.2 --replicas=3 --dry-run=client -o yaml > api.yaml
# edit api.yaml: add resources, a volume, a probe, whatever the task asks
kubectl apply -f api.yaml
```

`--dry-run=client` means "do not send it, just print what you would send".
`--dry-run=server` sends it for validation and admission without persisting
- useful to catch a webhook rejection before the real apply.

:::exam-tip
`kubectl apply` on an object that was created with `kubectl create` or `run`
works - it just warns once that the last-applied annotation is missing and
creates it. Do not waste time "converting" objects; apply is forgiving.
:::

## Reading the verbs

- `create` / `run` / `expose` - make a new object; fail if it exists.
- `apply` - make it so; create or update.
- `replace` - swap the whole object; `--force` deletes and recreates.
- `edit` - open the live object in `$EDITOR`; saves on exit.
- `patch` - change one path: `kubectl patch deployment api -p
  '{"spec":{"replicas":2}}'`.
- `set` - shortcuts for common patches: `set image`, `set env`, `set
  resources`, `set serviceaccount`.

## Check yourself

1. What three things does `kubectl apply` compare, and where is the third one
   stored?
2. You `kubectl scale` a Deployment to 5 and later `kubectl apply` its file,
   which says 3. What happens, and why?
3. When is `--dry-run=server` better than `--dry-run=client`?
