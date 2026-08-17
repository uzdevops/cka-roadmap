## You cannot pass the CKA by reading

The exam is a terminal. Every hour you spend in a real cluster is worth three
spent reading. This lesson gets you a cluster you can break and rebuild in
minutes.

## Choosing a local cluster

| Tool | Multi-node | Speed | Best for |
| --- | --- | --- | --- |
| **kind** | Yes, trivially | Fastest | Everyday practice, multi-node scenarios |
| **minikube** | Yes (`--nodes`) | Fast | Addons: ingress, metrics-server, dashboard |
| **kubeadm on VMs** | Yes | Slowest | Phase 4: upgrades, etcd, certificates |

Start with **kind**. Move to real VMs in Phase 4, because cluster installation
and upgrade tasks cannot be practised on kind.

## Install the tools

```bash
# kubectl - always match your cluster's minor version
curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version --client

# kind
[ $(uname -m) = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind
```

## A three-node kind cluster

```yaml
# kind-cluster.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: cka
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 8080
        protocol: TCP
  - role: worker
  - role: worker
```

```bash
kind create cluster --config kind-cluster.yaml
kubectl get nodes
# NAME                STATUS   ROLES           AGE   VERSION
# cka-control-plane   Ready    control-plane   45s   v1.31.x
# cka-worker          Ready    <none>          30s   v1.31.x
# cka-worker2         Ready    <none>          30s   v1.31.x
```

Tearing it down and starting fresh takes under a minute, which is exactly what
you want when practising destructive tasks:

```bash
kind delete cluster --name cka
```

## Understanding kubeconfig

Every `kubectl` command resolves three things from `~/.kube/config`: a
**cluster** (where), a **user** (who), and a **namespace** - bundled into a
**context**.

```bash
kubectl config view --minify              # the context you are actually using
kubectl config get-contexts
kubectl config use-context kind-cka
kubectl config set-context --current --namespace=dev   # stop typing -n dev
```

```yaml
# ~/.kube/config, simplified
clusters:
  - name: kind-cka
    cluster:
      server: https://127.0.0.1:39443
      certificate-authority-data: LS0tLS1C...
users:
  - name: kind-cka
    user:
      client-certificate-data: LS0tLS1C...
      client-key-data: LS0tLS1C...
contexts:
  - name: kind-cka
    context:
      cluster: kind-cka
      user: kind-cka
      namespace: default
current-context: kind-cka
```

:::warning
Exam tasks frequently start with "on cluster `xyz`" or "in namespace `abc`".
Running the right command against the wrong context scores zero. Make
`kubectl config use-context` the first thing you type for every question.
:::

## The shell setup that buys you time

Two hours is not much. Set this up in the first minute of the exam and in every
practice session, so it is muscle memory.

```bash
# aliases
alias k=kubectl
complete -o default -F __start_kubectl k

# dry-run + yaml output, used constantly to scaffold manifests
export do="--dry-run=client -o yaml"
export now="--force --grace-period=0"

# usage
k run nginx --image=nginx $do > pod.yaml
k delete pod nginx $now
```

Add them to `~/.bashrc` so a new terminal keeps them:

```bash
cat <<'EOF' >> ~/.bashrc
alias k=kubectl
complete -o default -F __start_kubectl k
export do="--dry-run=client -o yaml"
export now="--force --grace-period=0"
EOF
source ~/.bashrc
```

## Vim settings for YAML

YAML is whitespace-sensitive and the exam gives you `vim`. Without this, you will
lose time to indentation errors:

```bash
cat <<'EOF' >> ~/.vimrc
set expandtab
set tabstop=2
set shiftwidth=2
set number
EOF
```

:::exam-tip
In `vim`, `:set paste` before pasting a block from the documentation prevents
cascading auto-indent. `Ctrl-v` for block select then `Shift-i` to insert on
multiple lines is the fastest way to indent a pasted snippet.
:::

## Verify your environment

Run all of this before you consider the setup finished:

```bash
kubectl get nodes                       # all Ready
kubectl get pods -A                     # kube-system all Running
kubectl run test --image=nginx --restart=Never
kubectl get pod test -o wide            # scheduled on a worker
kubectl exec test -- nginx -v
kubectl delete pod test
```

If every one of those works, you have a functioning cluster and a working CLI.

:::tip
Install `metrics-server` early so `kubectl top` works - you will want it for the
autoscaling and troubleshooting phases. On kind it needs one extra flag because
the kubelet serving certificates are self-signed:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch -n kube-system deployment metrics-server --type=json \
  -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```
:::

## Check yourself

1. What three things does a kubeconfig *context* bind together?
2. How do you generate a Pod manifest without creating the Pod?
3. Why is `kind` unsuitable for practising a cluster upgrade?
