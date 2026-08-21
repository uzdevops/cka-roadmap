## The transformers on a real tree

Continuing the `k8s/` tree from the directories demo - `api/` and `db/`,
each with a Deployment and a Service, composed by a root kustomization.

### 1. Prefix and namespace from the root

```bash
cat k8s/kustomization.yaml
# resources: [api, db]
# commonLabels: {app: shop}
cat >> k8s/kustomization.yaml <<EOF
namePrefix: shop-
namespace: shop
EOF
kubectl kustomize k8s | grep -E "^  name:|namespace:"
#   name: shop-api       namespace: shop
#   name: shop-db        namespace: shop   (the db's own `namespace: data` is overridden by the parent)
```

Check the reference fixing: the api Deployment's Service selector and names
still line up.

```bash
kubectl kustomize k8s | grep -B2 -A6 "kind: Service" | grep -E "name:|app:"
```

### 2. Images from an overlay

```bash
mkdir -p k8s/overlays/prod
cat > k8s/overlays/prod/kustomization.yaml <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../..                          # the root k8s/ as the base
images:
  - name: myapi
    newTag: "2.1.0"
  - name: postgres
    newName: harbor.corp/postgres
    newTag: "16.3"
EOF
kubectl kustomize k8s/overlays/prod | grep image:
#   image: myapi:2.1.0
#   image: harbor.corp/postgres:16.3
```

### 3. Replicas and labels per environment

```bash
cat >> k8s/overlays/prod/kustomization.yaml <<EOF
replicas:
  - name: api                      # the ORIGINAL name, before the root's namePrefix
    count: 4
labels:
  - pairs: {env: prod}
    includeSelectors: false
commonAnnotations:
  owner: platform
EOF
kubectl kustomize k8s/overlays/prod | grep -E "replicas:|env:|owner:"
```

Note `name: api`, not `shop-api`: Kustomize matches the name as it is in the
resource **before** its own transformers run at that level. This is the rule
that trips everyone once.

### 4. A dev overlay, three lines different

```bash
mkdir -p k8s/overlays/dev
cat > k8s/overlays/dev/kustomization.yaml <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources: [../..]
nameSuffix: -dev
images:
  - name: myapi
    newTag: main
replicas:
  - name: api
    count: 1
EOF
diff <(kubectl kustomize k8s/overlays/dev) <(kubectl kustomize k8s/overlays/prod)
```

The `diff` is the whole point of the exercise: the two environments differ
in exactly the lines the overlays say, and nothing else.

### 5. Apply both

```bash
kubectl create ns shop
kubectl apply -k k8s/overlays/prod
kubectl apply -k k8s/overlays/dev
kubectl get deploy -n shop
# shop-api-dev    1/1
# shop-api        4/4
# shop-db-dev     1/1
# shop-db         1/1
```

Both overlays share a namespace here only because the root set it; a real
setup would give each overlay its own `namespace:`.

:::tip
After any change to a transformer, `kubectl kustomize | grep` for the field
you touched. It is faster than reading the whole output and it catches the
"matched nothing" silence of `images` and `replicas`.
:::

## Check yourself

1. The root sets `namePrefix: shop-`. In an overlay's `replicas`, do you
   write `api` or `shop-api`? Why?
2. Which transformer would you use to point every `postgres` image at an
   internal registry, and what is the one-line entry?
3. What does `diff <(kubectl kustomize dev) <(kubectl kustomize prod)` prove?
