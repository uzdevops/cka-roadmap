## Every object has the same four top-level fields

Whether it is a Pod, a NetworkPolicy or a CustomResource, the shape is identical:

```yaml
apiVersion: apps/v1        # which API group and version
kind: Deployment           # which type within that group
metadata:                  # identity: name, namespace, labels, annotations
  name: web
  namespace: default
  labels:
    app: web
spec:                      # desired state - you write this
  replicas: 3
status:                    # observed state - the system writes this
  readyReplicas: 3
```

You never write `status`. If you include it in a manifest, it is ignored.

## apiVersion: reading the group and version

```text
apiVersion: v1              -> core group (no name), version v1
apiVersion: apps/v1         -> group "apps", version v1
apiVersion: batch/v1        -> group "batch", version v1
apiVersion: networking.k8s.io/v1
apiVersion: rbac.authorization.k8s.io/v1
```

The ones that matter most:

| Kind | apiVersion |
| --- | --- |
| Pod, Service, ConfigMap, Secret, Namespace, PersistentVolume(Claim), ServiceAccount | `v1` |
| Deployment, ReplicaSet, StatefulSet, DaemonSet | `apps/v1` |
| Job, CronJob | `batch/v1` |
| Ingress, NetworkPolicy | `networking.k8s.io/v1` |
| Role, RoleBinding, ClusterRole, ClusterRoleBinding | `rbac.authorization.k8s.io/v1` |
| HorizontalPodAutoscaler | `autoscaling/v2` |

:::tip
Never memorise this table. `kubectl api-resources` prints it for your exact
cluster, including the short names and whether the type is namespaced:

```bash
kubectl api-resources | grep -i ingress
# ingresses  ing  networking.k8s.io/v1  true  Ingress
```
:::

## metadata: more than a name

```yaml
metadata:
  name: web                       # unique within (namespace, kind)
  namespace: production
  labels:                         # identifying, selectable
    app: web
    tier: frontend
    environment: production
  annotations:                    # descriptive, not selectable
    kubernetes.io/change-cause: "upgrade to 1.28"
    owner: platform-team@example.com
```

The distinction is one the exam tests: **labels are for selection, annotations
are for information.** You can select Pods by label; you cannot select by
annotation.

## Namespaced versus cluster-scoped

```bash
kubectl api-resources --namespaced=true    | head
kubectl api-resources --namespaced=false   | head
```

Cluster-scoped objects (no namespace): Node, PersistentVolume, Namespace,
ClusterRole, ClusterRoleBinding, StorageClass, CustomResourceDefinition.

:::warning
Setting `metadata.namespace` on a cluster-scoped object is an error, and omitting
it on a namespaced object silently uses your current context's namespace - which
may not be the one the question asked for. Always pass `-n` explicitly in the
exam rather than relying on context.
:::

## Writing YAML you can trust

YAML is indentation-sensitive and unforgiving. Three rules prevent most errors:

1. **Spaces only, never tabs.** A tab is a parse error.
2. **Two spaces per level**, consistently.
3. **`-` starts a list item**, indented under its key.

```yaml
spec:
  containers:           # a list
    - name: web         # first item
      image: nginx:1.27
      ports:
        - containerPort: 80
      env:
        - name: LOG_LEVEL
          value: "debug"
    - name: sidecar     # second item
      image: busybox
```

A frequent mistake - `containerPort` as a map instead of a list:

```yaml
# WRONG
ports:
  containerPort: 80

# RIGHT
ports:
  - containerPort: 80
```

## Multiple documents in one file

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: demo
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: settings
  namespace: demo
data:
  LOG_LEVEL: debug
```

`kubectl apply -f file.yaml` creates both, in order.

## Discovering fields with explain

This is the skill that replaces memorisation.

```bash
kubectl explain pod
kubectl explain pod.spec.containers
kubectl explain pod.spec.containers.livenessProbe
kubectl explain pod.spec.securityContext --recursive
kubectl explain deployment.spec.strategy.rollingUpdate
```

Output tells you the type and whether the field is required:

```text
FIELD: containerPort <integer> -required-

DESCRIPTION:
    Number of port to expose on the pod's IP address.
```

## Validate before you apply

```bash
kubectl apply -f manifest.yaml --dry-run=server    # full server-side validation
kubectl apply -f manifest.yaml --dry-run=client    # local, faster, less thorough
kubectl diff -f manifest.yaml                      # what would change
```

:::exam-tip
`--dry-run=server` catches admission-webhook rejections and schema errors that
client-side validation misses. When a manifest "looks right" but the exam task
still fails, run it server-side before you start rewriting the file.
:::

## Labels applied to a real selector

The relationship between a Deployment's selector and its Pod template labels is
the most common YAML error people make:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  selector:
    matchLabels:
      app: web        # must match ...
  template:
    metadata:
      labels:
        app: web      # ... this, exactly
    spec:
      containers:
        - name: web
          image: nginx:1.27
```

If they do not match, the API server rejects the Deployment with
`selector does not match template labels`. The selector is also **immutable**
after creation - to change it you must delete and recreate the Deployment.

## Check yourself

1. What is the difference between a label and an annotation?
2. Which command tells you whether `Ingress` is namespaced, and in which API group?
3. Why does a Deployment fail to create when `spec.selector.matchLabels` does not
   match `spec.template.metadata.labels`?
