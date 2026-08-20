## Why one Pod is never enough

A Pod is mortal. Its node can die, it can be evicted, its container can
crash past the restart policy's patience. If you want "always three copies of
nginx", you do not create three Pods - you create one object that *wants*
three Pods and a controller that keeps it true. That object is a
**ReplicaSet**.

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
```

Three parts:

- **replicas** - how many.
- **selector** - which Pods count. The ReplicaSet owns every Pod whose labels
  match, whether it created them or not.
- **template** - the Pod to create when there are too few. Its labels **must**
  satisfy the selector, or the API server rejects the ReplicaSet.

The older `ReplicationController` did the same job with an equality-only
selector and no `matchExpressions`. You will still see it in old manifests;
write ReplicaSets.

## The selector is the whole point

```bash
kubectl get rs
kubectl get pods -l app=web
kubectl describe rs web | grep -E "Selector|Replicas"
```

Because ownership is by label, two things follow:

1. **Adopting**: create a Pod by hand with `app: web` and the ReplicaSet
   counts it - and if it now has four, it deletes one (not necessarily yours).
2. **Orphaning**: `kubectl label pod web-abc12 app-` removes the label, the
   Pod is no longer counted, and the ReplicaSet creates a replacement. The old
   Pod keeps running, unmanaged. This is the trick for pulling one Pod out of
   a set to debug it.

:::exam-tip
"The ReplicaSet will not create" is nearly always
`spec.selector.matchLabels` not matching `spec.template.metadata.labels`. The
error says exactly that - read it. Second favourite: a wrong `apiVersion`
(`apps/v1`, not `v1`).
:::

## Scaling

```bash
kubectl scale rs web --replicas=5
kubectl scale --replicas=2 -f rs.yaml        # from the file
kubectl edit rs web                          # change spec.replicas
```

Scaling down deletes Pods; scaling up creates them from the template. Note
what `scale` does **not** do: it does not change the file on your disk. The
next `kubectl apply -f rs.yaml` puts replicas back to whatever the file says.

## Changing the template does nothing to running Pods

Edit the image in a ReplicaSet's template and ... nothing happens. The
ReplicaSet only creates Pods when it is short of them, so existing Pods keep
the old image until they die. To roll the change you would delete Pods one by
one and let them be recreated. That is tedious and risky - which is exactly
why you almost never create ReplicaSets directly: a **Deployment** manages
ReplicaSets for you and does the rolling for you. The next lesson.

## Generating one quickly

There is no `kubectl create replicaset`. Fastest path:

```bash
kubectl create deployment web --image=nginx:1.27 --replicas=3 --dry-run=client -o yaml \
  | sed 's/kind: Deployment/kind: ReplicaSet/' | grep -v strategy > rs.yaml
```

Or write the twelve lines by hand - it is good practice, and the exam's
`kubectl explain rs.spec` is open to you.

## Check yourself

1. Write a ReplicaSet's three required spec sections from memory.
2. How do you take one Pod out of a ReplicaSet to debug it without the
   ReplicaSet noticing - and what *does* it do in response?
3. You change the image in a ReplicaSet's template. What happens to the three
   running Pods?
