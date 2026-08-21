## Build the tree by hand

Follow along in an empty directory. The point is to see what each
`kustomize` command reads and what it emits at every level.

### 1. Two services, flat

```bash
mkdir -p k8s && cd k8s
kubectl create deployment api --image=myapi:1.0 --port=8080 --dry-run=client -o yaml > api-deployment.yaml
kubectl expose deployment api --port=80 --target-port=8080 --dry-run=client -o yaml > api-service.yaml
kubectl create deployment db --image=postgres:16 --port=5432 --dry-run=client -o yaml > db-deployment.yaml
kubectl expose deployment db --port=5432 --dry-run=client -o yaml > db-service.yaml
ls
# api-deployment.yaml  api-service.yaml  db-deployment.yaml  db-service.yaml
```

(`expose --dry-run` against a Deployment that does not exist needs the
Deployment file; simpler: `kubectl create service clusterip api --tcp=80:8080
--dry-run=client -o yaml`. Either way: four valid manifests.)

```bash
cat > kustomization.yaml <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - api-deployment.yaml
  - api-service.yaml
  - db-deployment.yaml
  - db-service.yaml
EOF
kubectl kustomize . | grep -E "^kind:|^  name:"
# kind: Service / name: api / kind: Service / name: db / kind: Deployment / name: api / kind: Deployment / name: db
```

Four objects in, four out, Services sorted before Deployments.

### 2. Split into directories

```bash
mkdir api db
mv api-*.yaml api/ && mv db-*.yaml db/
cd api && kustomize create --autodetect && cat kustomization.yaml && cd ..
# resources: [api-deployment.yaml, api-service.yaml]
cd db  && kustomize create --autodetect && cd ..
cat > kustomization.yaml <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - api
  - db
EOF
kubectl kustomize . | grep -c "^kind:"      # 4 - same objects, now composed from two directories
kubectl kustomize db/ | grep "^kind:"       # just the db's two
```

(No standalone `kustomize`? Write the two sub-kustomizations by hand; they
are three lines each.)

### 3. Give each directory its own rules

```bash
cat >> db/kustomization.yaml <<EOF
namespace: data
commonLabels:
  tier: data
EOF
cat >> api/kustomization.yaml <<EOF
commonLabels:
  tier: app
EOF
kubectl kustomize . | grep -E "^kind:|^  name:|namespace:|tier:"
# the db objects carry namespace: data and tier: data; the api ones tier: app and no namespace
```

### 4. And a rule for everything

```bash
cat >> kustomization.yaml <<EOF
commonLabels:
  app: shop
EOF
kubectl kustomize . | grep -c "app: shop"   # on every object (labels and selectors both)
```

### 5. Apply it

```bash
kubectl create namespace data
kubectl apply -k .
kubectl get deploy,svc -A -l app=shop
# NAMESPACE  NAME            ...
# data       deployment/db
# default    deployment/api
```

### 6. Read the tree back

```bash
find . -name kustomization.yaml -exec sh -c 'echo "== $1"; cat "$1"' _ {} \;
```

Three files, each a few lines, and the whole deployment is legible from
them. That legibility is the product.

:::tip
`kustomize create --autodetect` writes a `resources:` list from the files
present. Running it in a directory that already has a kustomization
refuses, which is a good safety habit: it never overwrites.
:::

## Check yourself

1. After step 2, how many `kustomization.yaml` files exist and what does each
   contain?
2. Which objects got `namespace: data`, and why not the api's?
3. How would you apply only the database half of the tree?
