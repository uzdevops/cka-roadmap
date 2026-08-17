## The four components you must know cold

On a `kubeadm` cluster all of these run as **static Pods** on the control plane
node, defined by manifests in `/etc/kubernetes/manifests/`. The kubelet watches
that directory and keeps them running - which is a neat bootstrap trick: the
control plane is run by the same agent it manages.

```bash
ls /etc/kubernetes/manifests/
# etcd.yaml  kube-apiserver.yaml  kube-controller-manager.yaml  kube-scheduler.yaml

kubectl get pods -n kube-system -l tier=control-plane
```

## kube-apiserver

The front door. Stateless, horizontally scalable, and the only component that
speaks to etcd.

Its request pipeline is worth knowing by name because exam failures map onto it:

```text
request -> authentication -> authorisation (RBAC) -> admission -> validation -> etcd
             401                403                  4xx/mutation
```

Key flags you will actually touch:

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml (excerpt)
spec:
  containers:
    - command:
        - kube-apiserver
        - --advertise-address=10.0.0.10
        - --secure-port=6443
        - --etcd-servers=https://127.0.0.1:2379
        - --authorization-mode=Node,RBAC
        - --enable-admission-plugins=NodeRestriction
        - --client-ca-file=/etc/kubernetes/pki/ca.crt
```

:::warning
Editing this file restarts the API server within seconds. A typo means the API
server never comes back and `kubectl` stops working entirely. Always keep a copy:

```bash
sudo cp /etc/kubernetes/manifests/kube-apiserver.yaml /root/apiserver.yaml.bak
```

If you break it, the container logs are still on disk even though `kubectl` is
dead:

```bash
sudo crictl ps -a | grep apiserver
sudo crictl logs <container-id>
```
:::

## etcd

A distributed, consistent key-value store. It holds **all** cluster state - every
object you have ever created. It is the only stateful component, which makes it
the only thing you genuinely have to back up.

- Uses the Raft consensus algorithm; needs a quorum of `(n/2)+1` members.
- Therefore always run an **odd** number of members: 3 or 5. A 2-member cluster
  is strictly worse than a 1-member cluster.
- Watches are what make the whole reconciliation model efficient - controllers
  subscribe to changes rather than polling.

```bash
# Cluster health, using the control plane's own certificates
sudo ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health
```

:::exam-tip
etcd backup and restore appears on the CKA with high probability. The command
shape is always the same - endpoints, cacert, cert, key - and you can read every
one of those paths straight out of `/etc/kubernetes/manifests/etcd.yaml`. You
will practise the full snapshot save/restore cycle in Phase 4.
:::

## kube-scheduler

Watches for Pods with no `spec.nodeName` and picks a node in two stages:

1. **Filtering** ("predicates") - eliminate nodes that *cannot* work: not enough
   allocatable CPU/memory, taints the Pod does not tolerate, unsatisfied node
   selectors or affinity, no matching volume topology, node not `Ready`.
2. **Scoring** ("priorities") - rank the survivors: spread across nodes, image
   locality, least requested resources, affinity preferences.

The highest-scoring node wins, and the scheduler writes a **Binding** object.
It never contacts the kubelet.

```bash
# Why is this Pod Pending? The scheduler tells you in the events.
kubectl describe pod <name> | tail -20
# Events:
#   Warning  FailedScheduling  0/3 nodes are available:
#   1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: },
#   2 Insufficient cpu.
```

That message is a filtering explanation. Read it literally: it tells you exactly
which predicate rejected which nodes.

## kube-controller-manager

A single binary running dozens of independent control loops. The ones you meet
most:

| Controller | Responsibility |
| --- | --- |
| Deployment | Creates and scales ReplicaSets for rollouts |
| ReplicaSet | Keeps the right number of Pods alive |
| Node | Marks nodes unhealthy and evicts Pods after a grace period |
| Job / CronJob | Runs Pods to completion, on a schedule |
| Endpoints / EndpointSlice | Keeps Service backends in sync with Pod readiness |
| ServiceAccount + Token | Creates default ServiceAccounts in new namespaces |
| PersistentVolume | Binds claims to volumes, handles reclaim policy |

```bash
kubectl get deployment web -o yaml | grep -A5 'status:'
# observedGeneration tells you whether the controller has seen your latest change
```

## cloud-controller-manager

Optional, and absent on bare-metal or local clusters. It isolates cloud-specific
logic: creating load balancers for `type: LoadBalancer` Services, attaching cloud
disks, and labelling nodes with region/zone.

:::tip
On `kind` or `minikube` there is no cloud controller, which is why a
`type: LoadBalancer` Service stays `<pending>` forever for its external IP. That
is correct behaviour, not a bug. Use `NodePort`, `kubectl port-forward`, or
`minikube tunnel` locally.
:::

## Failure modes, component by component

This table is the fastest revision aid in the lesson.

| Component down | Symptom |
| --- | --- |
| kube-apiserver | `kubectl` fails entirely; running Pods unaffected |
| etcd | API server unhealthy; no reads or writes of cluster state |
| kube-scheduler | New Pods stay `Pending` forever; existing Pods fine |
| kube-controller-manager | Deleted Pods are not recreated; rollouts stall; nodes never marked NotReady |
| kubelet (one node) | That node goes `NotReady`; its Pods eventually evicted |
| kube-proxy (one node) | Service VIPs stop working *from* that node |
| CoreDNS | DNS resolution fails; apps error on hostname lookup |

:::exam-tip
Given a symptom, name the component. "New Pods are Pending but existing ones are
healthy" is the scheduler. "I deleted a Pod from a Deployment and it was never
replaced" is the controller manager. Practise this mapping in both directions -
troubleshooting is 30% of the exam.
:::

## Check yourself

1. Where are the control plane manifests on a kubeadm node, and what restarts
   them when you edit one?
2. Why must an etcd cluster have an odd number of members?
3. A Pod is `Pending` with `FailedScheduling: Insufficient cpu`. Which stage of
   scheduling rejected it, and what are two ways to fix it?
