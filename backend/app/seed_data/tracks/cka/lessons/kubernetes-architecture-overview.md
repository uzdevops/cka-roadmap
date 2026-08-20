## Two kinds of machine

A Kubernetes cluster is a set of machines ("nodes") split into two roles.

- **Control plane nodes** run the components that make decisions: what should
  exist, where it should run, and whether reality matches.
- **Worker nodes** run your actual containers, plus the agents needed to be told
  what to run and to wire up networking.

A node can be both. In a single-node `kind` or `minikube` cluster, it is.

## The cluster at a glance

Everything below is a box in the diagram - the two headers included. Select any
of them and you will land on its description, which is where the detail lives:
what it does, what breaks when it stops, and the command you would actually
type.

::cluster-architecture

:::component{key=control-plane}
Not a process - the **role** a node plays. A control plane node runs the four
components below, and together they answer one question over and over: does the
cluster match what was asked for? None of them run your application containers.

Production clusters run three or five control plane nodes behind a load
balancer, so the API server stays reachable and etcd keeps its quorum when one
dies. A `kind` or `minikube` cluster collapses all of this onto a single node
that is both control plane and worker.

On a `kubeadm` cluster all four run as **static Pods**, defined by manifests the
kubelet watches:

```bash
ls /etc/kubernetes/manifests/
# etcd.yaml  kube-apiserver.yaml  kube-controller-manager.yaml  kube-scheduler.yaml

kubectl get pods -n kube-system -l tier=control-plane
```

Control plane nodes normally carry a taint that keeps ordinary workloads off
them - which is why a Pod can sit `Pending` on a two-node cluster that looks
half empty:

```bash
kubectl describe node <control-plane-node> | grep -i taint
# Taints: node-role.kubernetes.io/control-plane:NoSchedule
```
:::

:::component{key=kube-apiserver}
The front door, and the only component that talks to etcd. Everything else -
`kubectl`, the scheduler, the controllers, every kubelet - is a client of this
one REST API, which is why access control, auditing and validation all happen
in exactly one place.

It is stateless and horizontally scalable: all the state it serves lives in
etcd. Its request pipeline is worth knowing by name, because failures map onto
its stages:

```text
request -> authentication -> authorisation (RBAC) -> admission -> validation -> etcd
             401                403                  4xx/mutation
```

**When it is down:** `kubectl` stops working entirely and no new decisions can
be made - but Pods that are already running keep running and keep serving
traffic. The data plane does not depend on it.

```bash
kubectl get --raw='/readyz?verbose'
sudo crictl ps -a | grep apiserver     # still works when kubectl does not
```
:::

:::component{key=etcd}
A distributed, consistent key-value store holding **all** cluster state - every
object you have ever created. It is the only stateful component in the control
plane, which makes it the only thing you genuinely have to back up.

- It uses the Raft consensus algorithm and needs a quorum of `(n/2)+1` members.
- So always run an **odd** number of members, 3 or 5. A 2-member cluster is
  strictly worse than a 1-member cluster: it tolerates zero failures and has
  two things that can break.
- Its **watch** mechanism is what makes reconciliation efficient - controllers
  subscribe to changes instead of polling.

**When it is down:** the API server reports itself unhealthy and no cluster
state can be read or written.

```bash
sudo ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health
```
:::

:::component{key=kube-controller-manager}
One binary running dozens of independent control loops. Each loop watches the
desired state through the API server, compares it with the observed state, and
acts to close the gap. This is the reconciliation model made concrete.

| Controller | Responsibility |
| --- | --- |
| Deployment | Creates and scales ReplicaSets for rollouts |
| ReplicaSet | Keeps the right number of Pods alive |
| Node | Marks nodes unhealthy and evicts Pods after a grace period |
| Job / CronJob | Runs Pods to completion, on a schedule |
| EndpointSlice | Keeps Service backends in sync with Pod readiness |
| PersistentVolume | Binds claims to volumes, handles reclaim policy |

**When it is down:** deleted Pods are never recreated, rollouts stall halfway,
and failed nodes are never marked `NotReady`. Nothing errors loudly - the
cluster just stops healing itself.
:::

:::component{key=kube-scheduler}
Watches for Pods that have no `spec.nodeName` yet and picks a node for each, in
two stages:

1. **Filtering** ("predicates") - eliminate nodes that *cannot* work: not enough
   allocatable CPU or memory, taints the Pod does not tolerate, unsatisfied node
   selectors or affinity, no matching volume topology, node not `Ready`.
2. **Scoring** ("priorities") - rank the survivors: spread across nodes, image
   locality, least requested resources, affinity preferences.

The highest-scoring node wins and the scheduler writes a **Binding** object. It
never contacts the kubelet - it only writes to the API server, and the kubelet
finds out by watching.

**When it is down:** new Pods stay `Pending` forever; everything already running
is unaffected.

```bash
kubectl describe pod <name> | tail -20
# Events:
#   Warning  FailedScheduling  0/3 nodes are available:
#   1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: },
#   2 Insufficient cpu.
```

That message is a filtering explanation. Read it literally - it names which
predicate rejected which nodes.
:::

:::component{key=worker}
The other role: the nodes that actually run your containers. A worker holds the
three components below plus the Pods themselves, and it makes **no decisions** -
it is told what to run and reports back on how that went.

This is the half of the cluster people mean by the **data plane**, and it is why
a broken control plane is survivable: the workers already know what they are
running and keep doing it. Traffic keeps flowing; you just cannot change
anything.

Add as many as you like - workers are the axis a cluster scales along. Each one
needs a kubelet, a container runtime, kube-proxy (or a CNI that replaces it),
and a CNI plugin to give its Pods addresses.

```bash
kubectl get nodes -o wide
kubectl describe node <node> | grep -A10 Conditions   # why a node is NotReady
kubectl get pods -A -o wide --field-selector spec.nodeName=<node>
```

:::exam-tip
`kubectl drain <node> --ignore-daemonsets` then `kubectl uncordon <node>` is the
worker-node lifecycle the exam asks about most. Drain evicts the Pods and marks
the node unschedulable; `--ignore-daemonsets` is needed because DaemonSet Pods
are deliberately not evictable.
:::
:::

:::component{key=kubelet}
The agent on **every** node, control plane included. It watches the API server
for Pods assigned to *its* node, then tells the container runtime to start them,
and reports node and Pod status back up.

It also runs **static Pods** straight from a local manifest directory, with no
scheduler involved. That is how the control plane bootstraps itself: on a
`kubeadm` cluster the API server, etcd, scheduler and controller manager are all
static Pods run by the very kubelet they manage.

**When it is down on one node:** that node goes `NotReady` and, after the
eviction timeout, its Pods are rescheduled elsewhere. Containers already running
on it are not killed by the kubelet's absence - nothing is left to report on
them or restart them.

```bash
sudo systemctl status kubelet
sudo journalctl -u kubelet -f          # first place to look on a NotReady node
ls /etc/kubernetes/manifests/          # static Pod manifests
```
:::

:::component{key=kube-proxy}
Maintains the network rules that make a Service's virtual IP actually reach a
real Pod. It watches Services and EndpointSlices, and programs the node's
packet-forwarding layer to match.

- In `iptables` mode it writes iptables chains - the common default.
- In `ipvs` mode it programs IPVS virtual servers, which scales better on
  clusters with very many Services.
- Some CNI plugins (Cilium, for example) replace it entirely with eBPF.

**When it is down on one node:** Service VIPs stop working *from* that node.
Pods on it can still be reached directly by Pod IP, which is exactly the clue
that points at kube-proxy rather than at the CNI plugin.

```bash
kubectl -n kube-system get pods -l k8s-app=kube-proxy -o wide
sudo iptables -t nat -L KUBE-SERVICES -n | head
```
:::

:::component{key=container-runtime}
The thing that actually runs containers - pulls images, creates namespaces and
cgroups, starts and stops processes. The kubelet speaks to it over the
**Container Runtime Interface (CRI)**, so the two are swappable.

Today that is usually **containerd** or **CRI-O**. Docker Engine was removed as
a directly supported runtime in Kubernetes 1.24; the images it built are
unaffected, because image format and runtime are separate concerns.

**When it is down on one node:** the kubelet cannot start anything there and the
node goes `NotReady` - the same symptom as a dead kubelet, which is why you
check both.

```bash
sudo crictl ps                 # containerd's CLI, namespaced to Kubernetes
sudo crictl images
sudo crictl logs <container-id>
```
:::

:::note
There is an eighth box on some clusters: the **cloud-controller-manager**. It is
optional and absent on bare metal, `kind` and `minikube`. It isolates
cloud-specific logic - creating load balancers for `type: LoadBalancer`
Services, attaching cloud disks, labelling nodes with region and zone. Its
absence locally is why a `type: LoadBalancer` Service keeps `<pending>` as its
external IP forever, which is correct behaviour rather than a bug.
:::

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
