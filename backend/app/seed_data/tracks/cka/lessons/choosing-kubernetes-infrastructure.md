## Three ways to end up with a cluster

| Category | You get | You do | Examples |
|---|---|---|---|
| **Local / learning** | a cluster on your machine in minutes | nothing operational | minikube, kind, k3d, Docker Desktop |
| **Turnkey / self-managed** | tools that build and upgrade a cluster on VMs you control | provision VMs, run the tool, run the cluster | kubeadm, kops, Kubespray, Cluster API, RKE2, OpenShift, Talos |
| **Hosted / managed** | a control plane the provider runs | nodes (sometimes), workloads | GKE, EKS, AKS, DigitalOcean, Linode, OpenShift Dedicated |

The line that matters: in the first two **you** own the control plane -
upgrades, certificates, etcd backups, HA. In the third the provider does;
you get a kubeconfig and a node pool.

## Local

```bash
minikube start --nodes 2 --cni calico
kind create cluster --config kind-3node.yaml       # control plane + 2 workers, as Docker containers
k3d cluster create lab --servers 1 --agents 2
```

- **minikube** - a VM or container per node, lots of addons, the longest
  history.
- **kind** - Kubernetes in Docker; fast, multi-node, the one this track's
  labs use; no LoadBalancer without an add-on, and nodes are containers so
  `systemctl` on a "node" is `docker exec`.
- **k3s/k3d** - a single-binary Kubernetes; tiny, good for edge and CI.

None of them teaches you kubeadm's failure modes, which is why the install
lessons use real VMs.

## Turnkey

- **kubeadm** - the upstream tool: `init` on the first control plane,
  `join` on the rest. It installs the control plane as static Pods and
  leaves the OS, runtime, CNI and load balancer to you. It is **the** CKA
  tool.
- **kops** - kubeadm-style clusters on AWS/GCP with the cloud resources
  (VPC, ASGs) created for you.
- **Kubespray** - Ansible playbooks around kubeadm for bare metal and any
  cloud.
- **Cluster API** - Kubernetes managing Kubernetes: clusters as custom
  resources, a management cluster that creates workload clusters.
- **Distributions** - RKE2/Rancher, OpenShift, Talos, Charmed Kubernetes:
  opinionated bundles with their own installers and support.

```bash
kubeadm init --pod-network-cidr=10.244.0.0/16 --control-plane-endpoint=lb.example.com:6443
kubeadm join lb.example.com:6443 --token ... --discovery-token-ca-cert-hash sha256:...
```

## Hosted

```bash
gcloud container clusters create prod --num-nodes 3 --region europe-west1
aws eks create-cluster ... / eksctl create cluster
az aks create ...
```

You never see the control plane nodes. Upgrades are a button (or a flag);
etcd backups are the provider's; HA is included. In exchange: no custom
admission flags on the API server, no encryption-at-rest config of your own
(they offer their KMS), version choices limited to what the provider
supports, and a bill per cluster-hour.

## Choosing

| If | Then |
|---|---|
| you are learning the CKA | kubeadm on 2-3 VMs; kind for quick experiments |
| a small team, no ops staff, on a cloud | managed |
| compliance says the data stays in your building | turnkey on-prem: kubeadm/Kubespray/RKE2, plus MetalLB and a storage CSI |
| dozens of clusters | Cluster API or a distribution with fleet tooling |
| edge / IoT | k3s / Talos |

:::exam-tip
"Which infrastructure" is not a CKA question. What is: the kubeadm workflow
from the next lessons, and knowing that a `kind` or `minikube` cluster
differs from a kubeadm one in where things live (kind nodes are containers:
`docker exec kind-control-plane cat /etc/kubernetes/manifests/...`).
:::

## Check yourself

1. In which of the three categories do you own the control plane, and what
   does "own" include?
2. Why does this track use kubeadm on VMs for the install lessons rather
   than kind?
3. Name two things a managed provider will not let you do to the API server.
