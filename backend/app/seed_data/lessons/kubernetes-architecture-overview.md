## Two kinds of machine

A Kubernetes cluster is a set of machines ("nodes") split into two roles.

- **Control plane nodes** run the components that make decisions: what should
  exist, where it should run, and whether reality matches.
- **Worker nodes** run your actual containers, plus the agents needed to be told
  what to run and to wire up networking.

A node can be both. In a single-node `kind` or `minikube` cluster, it is.

```text
+---------------------------- Control plane ----------------------------+
|                                                                       |
|  kube-apiserver  <---->  etcd                                         |
|        ^                                                              |
|        |  watch / update                                              |
|        +-------- kube-scheduler                                       |
|        +-------- kube-controller-manager                              |
|        +-------- cloud-controller-manager (optional)                  |
+-----------------------------------------------------------------------+
             ^                                   ^
             | (kubelet reports, gets work)      |
+------------+-----------+           +-----------+------------+
|      Worker node 1     |           |      Worker node 2     |
|  kubelet               |           |  kubelet               |
|  kube-proxy            |           |  kube-proxy            |
|  container runtime     |           |  container runtime     |
|  [ Pod ] [ Pod ]       |           |  [ Pod ]               |
+------------------------+           +------------------------+
```

## The API server is the only door

Nothing in Kubernetes talks to etcd directly except the API server. Nothing talks
to the kubelet to schedule work except through the API server. Every component -
`kubectl`, the scheduler, the controllers, the kubelet - is a client of the same
REST API.

That single fact explains most of the system's behaviour:

- Access control is enforced in one place (authentication, authorisation, admission).
- Components are decoupled: the scheduler does not know the kubelet exists.
- Everything is auditable, because every change is an API request.
- If the API server is down, nothing new can be *scheduled*, but Pods already
  running keep running.

:::exam-tip
"The API server is down but my application still serves traffic" is not a
contradiction, and the exam likes that distinction. The data plane (kubelet,
kube-proxy, your containers) keeps working; the control plane just cannot make
new decisions or accept changes.
:::

## What runs on a worker node

### kubelet

The agent on every node. It watches the API server for Pods assigned to *its*
node, then tells the container runtime to start them. It reports node and Pod
status back. It also runs **static Pods** from a local manifest directory, which
is how the control plane itself is usually bootstrapped.

```bash
# On a kubeadm node:
sudo systemctl status kubelet
sudo journalctl -u kubelet -f          # the first place to look on a NotReady node
ls /etc/kubernetes/manifests/          # static Pod manifests
```

### Container runtime

The thing that actually runs containers, spoken to over the Container Runtime
Interface (CRI). Today that is usually **containerd** or **CRI-O**. Docker Engine
was removed as a directly supported runtime in Kubernetes 1.24.

```bash
# containerd's CLI, namespaced to Kubernetes
sudo crictl ps
sudo crictl images
sudo crictl logs <container-id>
```

### kube-proxy

Maintains the network rules that make a Service's virtual IP reach a real Pod.
In `iptables` mode it programs iptables chains; in `ipvs` mode it programs IPVS
virtual servers. Some CNI plugins replace it entirely with eBPF.

## The journey of `kubectl apply`

Trace this end to end - it is worth memorising, because half of troubleshooting
is knowing which step to inspect.

1. **kubectl** reads your kubeconfig, builds an HTTP request, and sends it to the
   API server.
2. **Authentication** - who are you? (client certificate, bearer token, OIDC)
3. **Authorisation** - are you allowed to do this? (RBAC)
4. **Admission control** - should this be modified or rejected? (mutating, then
   validating webhooks and built-in plugins)
5. **Validation and persistence** - the object is written to **etcd**.
6. **The scheduler** notices a Pod with no `spec.nodeName`, filters and scores
   nodes, and writes a binding.
7. **The kubelet** on the chosen node sees a Pod assigned to it and calls the CRI
   runtime to pull images and start containers.
8. **kube-proxy** and the CNI plugin wire up networking so the Pod is reachable.
9. Status flows back up through the kubelet to the API server, and `kubectl get
   pods` shows `Running`.

```bash
# Watch steps 5-9 happen live
kubectl create deployment web --image=nginx:1.27
kubectl get events --sort-by=.lastTimestamp -w
```

:::tip
`kubectl get events --sort-by=.lastTimestamp` is the highest-value single command
in the whole exam. Scheduling failures, image pull failures, probe failures and
volume mount failures all announce themselves here first.
:::

## Addons that feel like core

These are not part of the control plane binary set, but a cluster without them is
not usable:

- **CNI plugin** (Calico, Cilium, Flannel, ...) - gives every Pod an IP and makes
  pod-to-pod traffic work. Without it, nodes stay `NotReady`.
- **CoreDNS** - resolves Service and Pod DNS names. Runs as a Deployment in
  `kube-system`.
- **metrics-server** - supplies `kubectl top` and the Horizontal Pod Autoscaler.

```bash
kubectl get pods -n kube-system
kubectl get nodes -o wide
```

:::warning
A fresh `kubeadm init` leaves every node `NotReady` until you install a CNI
plugin. This is expected behaviour, not a broken cluster - the kubelet reports
`NetworkReady=false` because no network plugin is configured. Read the node
conditions before you start reinstalling things:

```bash
kubectl describe node <node> | grep -A10 Conditions
```
:::

## Check yourself

1. Which component decides *which node* a Pod runs on, and which component
   actually *starts* it?
2. If etcd is unavailable, what still works and what stops working?
3. Why can a node be `Ready` but a Pod on it still be unreachable from another Pod?
