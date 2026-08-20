## What the scheduler really does

Strip the scheduler down and it does one write: it fills in `spec.nodeName`
on a Pod that has none. The kubelet on the named node sees "a Pod for me" and
starts it. Everything else - filtering, scoring, affinity, taints - is the
reasoning *before* that one write.

So if there is no scheduler, you can do the write yourself.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  nodeName: node02          # <- placed by hand
  containers:
    - name: nginx
      image: nginx
```

`kubectl apply` that and the Pod runs on node02 without the scheduler ever
seeing it. No filtering happens: if node02 lacks resources or has a taint the
Pod does not tolerate, the kubelet will still try - and the Pod may fail to
start, but it will be assigned.

## When you need this

- **The scheduler is down** (a troubleshooting task) and you need a Pod
  running *now*, before you have fixed the scheduler.
- You are debugging a node and want a Pod exactly there, no argument.
- You are writing a static Pod - which are always "manually" placed because
  the kubelet runs them from a file.

:::warning
`nodeName` is set at creation. You cannot add it to an existing Pending Pod
with `kubectl edit` - the field is immutable once the Pod exists. Delete and
recreate, or use the Binding object below.
:::

## The Binding object

What the scheduler actually sends to the API server is a **Binding**: a tiny
object that says "this Pod, that node". You can send the same thing:

```yaml
apiVersion: v1
kind: Binding
metadata:
  name: nginx                 # the Pod's name
target:
  apiVersion: v1
  kind: Node
  name: node02
```

```bash
# POST it against the Pod's binding subresource
curl --header "Content-Type: application/json" --request POST \
  --data '{"apiVersion":"v1","kind":"Binding","metadata":{"name":"nginx"},"target":{"apiVersion":"v1","kind":"Node","name":"node02"}}' \
  http://localhost:8001/api/v1/namespaces/default/pods/nginx/binding/
```

(`kubectl proxy` in another terminal provides `localhost:8001`.) This binds a
Pod that already exists and is Pending. In the exam the delete-and-recreate
route is faster unless the task says the Pod must not be recreated.

## The practical sequence

```bash
kubectl get pods                         # nginx is Pending
kubectl describe pod nginx | tail -5     # no events at all -> nothing has scheduled it
kubectl get pods -n kube-system | grep scheduler   # is it even there?

kubectl get pod nginx -o yaml > nginx.yaml
# add  nodeName: node02  under spec
kubectl replace --force -f nginx.yaml
kubectl get pod nginx -o wide            # Running on node02
```

:::exam-tip
"No events" is the tell. A Pod the scheduler *saw* but could not place has a
`FailedScheduling` event explaining why. A Pod with an empty Events section
was never looked at: the scheduler is gone, or the Pod asks for a
`schedulerName` that does not exist. Manual placement fixes the symptom;
remember to go fix the scheduler too, or the next Pod will stick as well.
:::

## What you cannot do with nodeName

- Move a running Pod. There is no "reschedule"; you delete it and something
  (a controller, or you) creates it again.
- Pin a Deployment's Pods. `nodeName` in a Pod template pins *every* replica
  to one node - legal, rarely wanted. For "prefer this kind of node" you want
  nodeSelector or affinity (next lessons), which still go through the
  scheduler.

## Check yourself

1. Which single field does the scheduler write, and which component acts on
   it?
2. A Pod is Pending with an empty Events section. What does that tell you, and
   what are your two options to get it running?
3. Why is `nodeName` in a Deployment's Pod template almost always a mistake?
