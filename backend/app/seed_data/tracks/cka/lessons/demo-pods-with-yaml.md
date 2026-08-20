## Walkthrough: a Pod from nothing to Running to fixed

This lesson is a single worked example. Follow it on your own cluster; each
step is a command you will type dozens of times in the exam.

### 1. Generate the skeleton

```bash
kubectl run web --image=nginx:1.27 --port=80 --labels=app=web,tier=frontend \
  --dry-run=client -o yaml > web.yaml
cat web.yaml
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  creationTimestamp: null
  labels:
    app: web
    tier: frontend
  name: web
spec:
  containers:
  - image: nginx:1.27
    name: web
    ports:
    - containerPort: 80
    resources: {}
  dnsPolicy: ClusterFirst
  restartPolicy: Always
status: {}
```

Note `creationTimestamp: null`, `resources: {}` and `status: {}` - harmless
noise the generator leaves behind. You can delete them or ignore them.

### 2. Create it and watch it come up

```bash
kubectl apply -f web.yaml
kubectl get pod web -w         # Pending -> ContainerCreating -> Running
```

```bash
kubectl get pod web -o wide    # which node, which IP
kubectl describe pod web       # events at the bottom: Scheduled, Pulling, Pulled, Created, Started
```

Read the Events section once slowly. Those five lines are the happy path; every
Pod problem you ever debug is one of them failing.

### 3. Break it on purpose

```bash
kubectl set image pod/web web=nginx:1.27-doesnotexist
kubectl get pod web            # STATUS: ErrImagePull, then ImagePullBackOff
kubectl describe pod web | tail -6
#   Warning  Failed   ...  Failed to pull image "nginx:1.27-doesnotexist": ... not found
```

`ImagePullBackOff` is not an error state with a fix of its own - it means "I
tried, it failed, I am waiting longer before trying again". The message above
it is the real error: the tag does not exist.

### 4. Fix it - two ways

```bash
# a) in place: image is one of the few mutable Pod fields
kubectl set image pod/web web=nginx:1.27

# b) from the file: edit web.yaml, then
kubectl apply -f web.yaml
```

```bash
kubectl get pod web            # Running again, RESTARTS unchanged
```

### 5. Look inside

```bash
kubectl logs web                       # nginx access/error log
kubectl exec web -- nginx -v           # run a command in the container
kubectl exec -it web -- sh             # a shell, if the image has one
kubectl port-forward pod/web 8080:80   # then curl localhost:8080 from your machine
```

### 6. Change something immutable

```bash
# try to add a second container by editing the live object
kubectl edit pod web      # add another entry under containers, save
# error: Pod "web" is invalid: spec.containers: Forbidden: pod updates may not add or remove containers
```

The honest fix:

```bash
kubectl get pod web -o yaml > web-full.yaml    # or edit your web.yaml
# add the container in the file
kubectl replace --force -f web-full.yaml       # deletes and recreates in one command
```

:::exam-tip
`kubectl edit` on a Pod is a trap for anything except image, labels and a few
annotations: it will refuse, and it will have saved your edit to a temp file
whose path it prints. `kubectl replace --force -f /tmp/kubectl-edit-xxxx.yaml`
picks that edit up - faster than redoing it.
:::

### 7. Clean up

```bash
kubectl delete pod web --grace-period=0 --force   # do not wait 30 s for nginx to stop
```

:::tip
In the exam, `--force --grace-period=0` on every delete saves real minutes
over the session. Alias it.
:::

## Check yourself

1. List the five events of a healthy Pod start, in order.
2. What does `ImagePullBackOff` tell you, and where is the actual error?
3. You need to add a second container to a running Pod. What is the shortest
   correct sequence of commands?
