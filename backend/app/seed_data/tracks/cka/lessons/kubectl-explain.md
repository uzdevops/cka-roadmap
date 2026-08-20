## The documentation that is already in your terminal

You do not remember every field of every kind, and you do not need to. The
API server publishes its full schema, and `kubectl explain` reads it back to
you - with types, descriptions and which fields are required.

```bash
kubectl explain pod
kubectl explain pod.spec
kubectl explain pod.spec.containers
kubectl explain pod.spec.containers.livenessProbe
kubectl explain deployment.spec.strategy.rollingUpdate
```

```
KIND:       Pod
VERSION:    v1

FIELD: livenessProbe <Probe>

DESCRIPTION:
    Periodic probe of container liveness. Container will be restarted if the
    probe fails. ...

FIELDS:
  exec          <ExecAction>
  failureThreshold      <integer>
  httpGet       <HTTPGetAction>
  initialDelaySeconds   <integer>
  periodSeconds <integer>
  ...
```

Each line is a field name, its type, and - when you scroll - a paragraph on
what it does. Nested types are explained by going one level deeper.

## The two flags that matter

```bash
kubectl explain pod.spec.affinity --recursive      # the whole subtree, names only, indented
kubectl explain pod.spec.affinity --recursive | less
```

`--recursive` prints every field below the path as a tree without the prose.
That is the view you want when you know *roughly* what you need (a node
affinity, a volume mount) and just need the spelling and nesting right.

```bash
kubectl explain deployment --api-version=apps/v1
kubectl explain ingress --api-version=networking.k8s.io/v1
kubectl explain cronjob.spec.jobTemplate.spec.template.spec.containers.resources
```

`--api-version` picks a specific group version when a kind exists in more than
one (HorizontalPodAutoscaler in `autoscaling/v1` and `autoscaling/v2`, for
example).

## Short names work too

```bash
kubectl explain deploy.spec.template.spec
kubectl explain svc.spec.ports
kubectl explain netpol.spec.ingress
kubectl explain pvc.spec
```

`kubectl api-resources` is the companion: it lists every kind with its short
name, API group and whether it is namespaced. Between the two you can write a
manifest for an object you have never seen.

:::exam-tip
Typing the field path wrong is the most common YAML error in the exam - an
indentation level too deep, `matchExpression` for `matchExpressions`,
`volumeMount` for `volumeMounts`. `kubectl explain <kind>.<path> --recursive`
answers both the name and the nesting in two seconds, and it works offline in
the exam terminal. Use it before the docs.
:::

## explain vs the documentation site

| Question | Faster with |
|---|---|
| what is this field called / where does it go | `kubectl explain` |
| a complete example manifest to copy | kubernetes.io/docs (search the kind, copy the example) |
| what values a field accepts | `explain` (it lists enums in the description) |
| a conceptual explanation | the docs |

:::tip
`kubectl explain` needs an API server - it reads the schema from the cluster.
It therefore also tells you about CRDs installed on *this* cluster, which the
public docs cannot.
:::

## Check yourself

1. You need to add a `nodeAffinity` block and cannot remember the nesting.
   What is the exact command that shows it?
2. Which flag lets you choose between two API versions of the same kind?
3. Why does `kubectl explain` know about a CRD the documentation site has
   never heard of?
