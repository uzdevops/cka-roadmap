## Loose coupling by key/value

Kubernetes objects do not reference each other by ID. A Service does not contain
a list of Pods; it contains a **selector**, and the endpoint controller
continuously finds whatever matches. That indirection is why you can replace
every Pod behind a Service without touching the Service.

```yaml
metadata:
  labels:
    app: web
    tier: frontend
    environment: production
    version: v1.2.3
```

## Label rules

- Key: optional DNS-subdomain prefix + `/` + name, e.g. `example.com/team`.
  The name part is at most 63 characters.
- Value: at most 63 characters, alphanumerics plus `-`, `_`, `.`; may be empty.
- Prefixes `kubernetes.io/` and `k8s.io/` are reserved for core components.

The recommended common labels, which you will see on anything installed by Helm:

```yaml
labels:
  app.kubernetes.io/name: web
  app.kubernetes.io/instance: web-prod
  app.kubernetes.io/version: "1.2.3"
  app.kubernetes.io/component: frontend
  app.kubernetes.io/part-of: shop
  app.kubernetes.io/managed-by: helm
```

## Equality-based selectors

The simple form, used by Services and by `kubectl -l`:

```bash
kubectl get pods -l app=web
kubectl get pods -l app=web,tier=frontend        # AND
kubectl get pods -l app!=web
kubectl get pods -l 'app'                        # key exists, any value
kubectl get pods -l '!app'                       # key does not exist
```

```yaml
# Service - only supports equality-based selectors
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  selector:
    app: web
    tier: frontend
  ports:
    - port: 80
      targetPort: 8080
```

## Set-based selectors

Richer, and required by Deployments, ReplicaSets and NetworkPolicies:

```bash
kubectl get pods -l 'environment in (production, staging)'
kubectl get pods -l 'tier notin (cache)'
kubectl get pods -l 'app in (web),environment notin (dev)'
```

```yaml
selector:
  matchLabels:
    app: web
  matchExpressions:
    - key: environment
      operator: In
      values: [production, staging]
    - key: tier
      operator: NotIn
      values: [cache]
    - key: track
      operator: Exists
```

Operators: `In`, `NotIn`, `Exists`, `DoesNotExist`. Every condition in
`matchLabels` and `matchExpressions` is ANDed together.

:::warning
A Service's `spec.selector` is a plain map - it cannot use `matchExpressions`.
If a question asks for set-based matching on a Service, the answer is to select
by a label you add for that purpose, not to write expressions.
:::

## Managing labels from the CLI

```bash
kubectl label pod web environment=production
kubectl label pod web environment=staging --overwrite
kubectl label pod web environment-                 # remove (trailing dash)
kubectl label pods --all monitored=true
kubectl label nodes cka-worker disktype=ssd

kubectl get pods --show-labels
kubectl get pods -L environment,tier               # labels as columns
```

## Labels drive scheduling too

A node label plus a Pod `nodeSelector` is the simplest placement rule there is:

```bash
kubectl label nodes cka-worker disktype=ssd
```

```yaml
spec:
  nodeSelector:
    disktype: ssd
```

The Pod will stay `Pending` until a node carries that label - which is a very
common cause of unschedulable Pods.

```bash
kubectl get nodes --show-labels
kubectl describe pod <name> | grep -A5 Events
# 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.
```

## Annotations

Same key/value shape, opposite purpose: arbitrary metadata for tools and humans,
**not** selectable, and not size-limited to 63 characters.

```yaml
metadata:
  annotations:
    kubernetes.io/change-cause: "upgrade nginx to 1.28"
    nginx.ingress.kubernetes.io/rewrite-target: /
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
    description: |
      Owned by the platform team.
      Escalate via #platform-oncall.
```

```bash
kubectl annotate deployment web kubernetes.io/change-cause="bump to 1.28"
kubectl annotate deployment web description-       # remove
```

The `kubernetes.io/change-cause` annotation is what populates the CHANGE-CAUSE
column of a rollout history - useful when a question asks you to identify or roll
back to a specific revision:

```bash
kubectl rollout history deployment/web
# REVISION  CHANGE-CAUSE
# 1         initial deployment
# 2         bump to 1.28
```

:::exam-tip
Ingress behaviour is configured almost entirely through annotations
(`nginx.ingress.kubernetes.io/...`). If an Ingress question mentions rewriting,
SSL redirect, or backend protocol, the answer is an annotation, not a spec field.
:::

## Labels versus annotations

| | Labels | Annotations |
| --- | --- | --- |
| Purpose | Identify and select | Describe and configure tools |
| Selectable | Yes | No |
| Value size | 63 characters | Effectively unlimited |
| Indexed by the API | Yes | No |
| Typical use | `app`, `tier`, `environment` | change-cause, ingress config, checksums |

## Check yourself

1. Write a selector matching Pods where `environment` is `production` or
   `staging`, but `tier` is not `cache`.
2. Why can a Service not use `matchExpressions`?
3. Your Pod is `Pending` with "didn't match Pod's node affinity/selector". Give
   two commands that will confirm the cause.
