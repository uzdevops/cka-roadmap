## Make it so

`kubectl apply -f` is the declarative verb: hand it a file and the cluster
ends up matching the file. If the object does not exist it is created; if it
exists it is updated; if it already matches, nothing happens.

```bash
kubectl apply -f deployment.yaml
kubectl apply -f ./manifests/            # every file in a directory
kubectl apply -f https://.../install.yaml
kubectl apply -k ./overlays/prod          # a kustomization
kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: dev
EOF
```

## The three-way merge

What makes `apply` safe to repeat is that it compares three documents:

```
   your file          last-applied (annotation)         live object
 (what you want)   (what you wanted last time)   (what the cluster has now)
```

| Field is ... | apply does |
|---|---|
| in your file, not in live | add it |
| in your file and live, different | set it to your file's value |
| in last-applied, **not** in your file | **remove** it - you deleted it on purpose |
| in live, not in your file or last-applied | leave it - the cluster or another tool owns it (defaults, status, a scaler) |

That last row is the clever one. Defaults the API server filled in, fields a
controller manages, the `status` block - none of them are in your file, none
were ever in your file, so apply leaves them alone.

The "last-applied" document is stored on the object itself:

```bash
kubectl get deploy web -o jsonpath='{.metadata.annotations.kubectl\.kubernetes\.io/last-applied-configuration}'
```

## Server-side apply

Newer kubectl can do the merge **on the API server** with `--server-side`,
tracking field ownership per *manager* (`managedFields` in the metadata)
instead of through the annotation. Several tools can then co-own one object
without stomping on each other. Useful to know it exists; the default
client-side apply is what the exam expects.

```bash
kubectl apply --server-side -f deployment.yaml
kubectl apply --server-side --force-conflicts -f deployment.yaml   # take ownership of conflicting fields
```

## The things apply will not do

- **Change an immutable field.** A Pod's container list, a Service's
  `clusterIP`, a Job's template, a PVC's storage class:
  `kubectl apply` reports "field is immutable". The answer is
  `kubectl replace --force -f file.yaml`, which deletes and recreates.
- **Delete objects you removed from a directory.** `apply -f dir/` only sees
  the files that are there. `--prune` exists and is dangerous; in practice you
  `kubectl delete -f old.yaml`.
- **Undo a `kubectl scale` or `edit` by itself.** It will - but only because
  your file says 3 and the live object says 5, so it sets 3. That is the
  mixed-style trap from the previous lesson.

```bash
kubectl diff -f deployment.yaml      # what WOULD apply change? - the safest habit before any apply
```

:::exam-tip
`kubectl apply` over an object created imperatively prints a warning about the
missing last-applied annotation and then just works, adding the annotation.
Do not stop to "fix" that warning. Likewise `kubectl create -f` over an
existing object fails - reach for `apply` when you are unsure whether it
exists.
:::

:::tip
`kubectl apply -f x.yaml && kubectl get -f x.yaml` - `get -f` reads the file
to know what to show, so you see exactly the objects you just applied, whatever
their kinds.
:::

## Check yourself

1. A field was in the file last time and you removed it this time. What does
   apply do to the live object, and how does it know?
2. apply says `spec.clusterIP: Invalid value ... field is immutable`. What now?
3. What does `kubectl diff -f` show, and why run it before apply?
