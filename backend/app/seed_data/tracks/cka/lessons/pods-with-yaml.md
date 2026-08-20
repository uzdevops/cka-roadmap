## The four fields every manifest has

Every Kubernetes object you will ever write has the same skeleton:

```yaml
apiVersion:   # which API group and version this kind comes from
kind:         # what it is
metadata:     # name, namespace, labels, annotations
spec:         # what you want
```

A fifth, `status`, is written by the cluster, never by you. For a Pod:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web
  labels:
    app: web
    tier: frontend
spec:
  containers:
    - name: nginx
      image: nginx:1.27
      ports:
        - containerPort: 80
```

Read it top to bottom: this is a `Pod` from the core API (`v1`), called
`web`, carrying two labels, and its desired state is one container called
`nginx` from that image. The `containers` field is a **list** - that dash is
not decoration, it is what lets a Pod hold more than one container.

## Where the field names come from

You do not memorise them; you look them up:

```bash
kubectl explain pod.spec                       # every field of spec, with types
kubectl explain pod.spec.containers            # the container object
kubectl explain pod.spec.containers.resources --recursive
```

`apiVersion` is the one people get wrong. The rule of thumb:

| Kind | apiVersion |
|---|---|
| Pod, Service, ConfigMap, Secret, Namespace, Node, PersistentVolume(Claim), ServiceAccount | `v1` |
| Deployment, ReplicaSet, DaemonSet, StatefulSet | `apps/v1` |
| Job, CronJob | `batch/v1` |
| Ingress, NetworkPolicy | `networking.k8s.io/v1` |
| Role, RoleBinding, ClusterRole, ClusterRoleBinding | `rbac.authorization.k8s.io/v1` |
| HorizontalPodAutoscaler | `autoscaling/v2` |

`kubectl api-resources` prints the whole table for your cluster.

## YAML rules that bite

- **Indentation is the structure.** Two spaces per level, spaces only, never
  tabs. A key one space off becomes a sibling instead of a child and the error
  message will not say so.
- **Lists start with `- `.** `containers:` takes a list of maps; each `- name:`
  starts a new container.
- **Strings that look like something else.** `"80"` is a string, `80` is a
  number; `containerPort` wants the number, an env `value` wants the string.
  `yes`/`no`/`on`/`off` are booleans in YAML 1.1 - quote them.
- **`---` separates documents**, so one file can hold a Pod and its Service.

:::tip
Do not hand-type skeletons. `kubectl run web --image=nginx --dry-run=client -o
yaml > pod.yaml` gives you a valid file to edit, with `apiVersion` and the
indentation already right. This is the single most useful exam habit.
:::

## From file to cluster and back

```bash
kubectl apply -f pod.yaml          # create or update
kubectl create -f pod.yaml         # create only - fails if it exists
kubectl get pod web -o yaml        # the object as the cluster holds it, status included
kubectl get pod web -o yaml > current.yaml   # round-trip it for editing
kubectl delete -f pod.yaml
```

What comes back from `get -o yaml` has more than you wrote - defaults filled
in (`restartPolicy: Always`, `dnsPolicy: ClusterFirst`, a service account, a
`status` block). That is normal; the cluster added them.

:::exam-tip
Many Pod fields are immutable once created (the image is one of the few you
may change in place). If `kubectl apply` refuses with "field is immutable",
the move is `kubectl replace --force -f pod.yaml` - delete and recreate in one
step - and you need that file to contain everything you care about.
:::

## Check yourself

1. Which four top-level fields does every manifest have, and which fifth one
   must you never write?
2. Write from memory the `apiVersion` for a Deployment, a Job and an Ingress.
3. `kubectl apply` says a field is immutable. What is the one-line fix, and
   what does it do to the running Pod?
