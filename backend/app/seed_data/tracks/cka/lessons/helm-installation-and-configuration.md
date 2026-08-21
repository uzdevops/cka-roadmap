## One binary, no server

Helm 3 is a single client binary. There is nothing to install *in* the
cluster - it talks to the API server with your kubeconfig and stores its
state as Secrets in the release's namespace. So "installing Helm" is putting
one file on your PATH.

```bash
# the project's installer script
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# or a package manager
sudo snap install helm --classic          # Ubuntu
brew install helm                         # macOS
# apt: add the Helm repo from helm.sh/docs/intro/install, then apt-get install helm

# or the tarball
wget https://get.helm.sh/helm-v3.15.2-linux-amd64.tar.gz
tar -zxvf helm-v3.15.2-linux-amd64.tar.gz && sudo mv linux-amd64/helm /usr/local/bin/helm

helm version
# version.BuildInfo{Version:"v3.15.2", ...}
```

## Pointing it at a cluster

Helm uses the same kubeconfig and context rules as kubectl:

```bash
helm list                                  # current context, current namespace
helm list -A                               # all namespaces
helm --kube-context prod list
helm --kubeconfig /path/config -n payroll list
KUBECONFIG=/path/config helm list
```

Whatever `kubectl get pods` is pointed at, `helm` is pointed at too. A
release is always **in a namespace** (`-n`, default `default`), and Helm's
record of it (`sh.helm.release.v1.<name>.v<revision>` Secrets) lives there.

```bash
kubectl get secrets -n default -l owner=helm
# sh.helm.release.v1.my-site.v1   helm.sh/release.v1   ...
```

## Adding repositories

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo list
helm repo update                           # refresh the indexes - do this before install/upgrade
helm search repo nginx
helm repo remove bitnami
```

Charts can also live in **OCI registries** with no repo step:

```bash
helm install my-app oci://registry.example.com/charts/my-app --version 1.2.0
```

## Shell completion and environment

```bash
source <(helm completion bash)
helm env                                   # where Helm keeps its cache, config, plugins
# HELM_CACHE_HOME=~/.cache/helm  HELM_CONFIG_HOME=~/.config/helm  HELM_REPOSITORY_CONFIG=.../repositories.yaml
```

:::exam-tip
On the exam cluster Helm is usually pre-installed; check `helm version`
first. If a task says install it, the `get-helm-3` script is the shortest
route and needs only curl and bash. Then `helm repo add` whatever the task
names and `helm repo update` - forgetting the update is why "chart not
found" or "version not found" appears.
:::

## Check yourself

1. What does Helm 3 install in the cluster, and where does it keep the
   record of a release?
2. Helm and kubectl disagree about which cluster they are talking to. Is
   that possible? Why or why not?
3. You add a repo and `helm install` cannot find the chart version the task
   wants. What did you skip?
