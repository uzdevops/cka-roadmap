## One control plane node is one point of failure

Lose it and: existing Pods keep running (the kubelets do not need the API
server to keep things alive), but nothing new happens - no scheduling, no
scaling, no `kubectl`, no self-healing of anything that dies. HA is about
having more than one of each control plane component, and knowing how each
one shares the work.

## The API server: active-active behind a load balancer

Every API server instance is stateless and equivalent; they all talk to the
same etcd. Run three, put a **load balancer** in front, point every client
(kubectl, kubelets, the scheduler and controller manager) at the load
balancer's address instead of any one node.

```
kubectl / kubelets ──▶ lb.example.com:6443 ──▶ apiserver@cp1 :6443
                                            ──▶ apiserver@cp2 :6443
                                            ──▶ apiserver@cp3 :6443
```

kubeadm bakes that address in at init:

```bash
kubeadm init --control-plane-endpoint=lb.example.com:6443 --upload-certs ...
```

`--control-plane-endpoint` goes into every kubeconfig and into the API
server certificate's SANs. **Set it even for a single control plane** if you
ever plan to add more: changing it later means regenerating certificates and
kubeconfigs. The load balancer itself can be HAProxy + keepalived on the
control plane nodes, a cloud LB, or kube-vip running as a static Pod.

## The scheduler and controller manager: active-standby via leader election

Three schedulers all scheduling the same Pod would be chaos. So the scheduler
and the controller manager run on every control plane node but only the
**leader** acts; the others wait.

```yaml
# in their static Pod manifests
- --leader-elect=true
- --leader-elect-lease-duration=15s
- --leader-elect-renew-deadline=10s
- --leader-elect-retry-period=2s
```

The leader holds a **Lease** object in `kube-system` and renews it every 2
seconds; if it stops renewing for 15 seconds, another instance takes the
lease and becomes leader.

```bash
kubectl get leases -n kube-system
# NAME                      HOLDER                      AGE
# kube-controller-manager   cp1_5f3a...                 30d
# kube-scheduler            cp2_91c0...                 30d
kubectl describe lease kube-scheduler -n kube-system | grep -i holder
```

That is the answer to "which scheduler is actually scheduling right now".

## etcd: a cluster of its own, with quorum

etcd's HA is the RAFT story from the etcd lessons: an odd number of members,
writes need a majority. Two ways to place them:

**Stacked** (kubeadm default): etcd runs as a static Pod on each control plane
node; three control plane nodes = three etcd members.

```
cp1: apiserver + cm + sched + etcd
cp2: apiserver + cm + sched + etcd
cp3: apiserver + cm + sched + etcd
```

Fewer machines, simpler; losing a control plane node loses an etcd member
too.

**External**: etcd on its own three (or five) hosts; the API servers point
at them with `--etcd-servers=https://etcd1:2379,https://etcd2:2379,...`.

```
cp1, cp2, cp3: apiserver + cm + sched
e1, e2, e3:    etcd
```

More machines; control plane and data store fail independently; the
`kubeadm init` for this uses a config file with the external endpoints and
certificates. The next lesson is etcd in HA in detail.

## The kubeadm HA workflow, in outline

1. Load balancer in front of the future control plane nodes.
2. `kubeadm init --control-plane-endpoint=<lb>:6443 --upload-certs` on cp1
   (prints two join commands: one for control planes, one for workers).
3. `kubeadm join <lb>:6443 --control-plane --certificate-key <key> ...` on cp2
   and cp3 - they pull the shared certificates from the cluster and start
   their own control plane static Pods.
4. Install the CNI; `kubeadm join` the workers.

```bash
kubectl get nodes            # three control-plane, N workers
kubectl get pods -n kube-system | grep -E "apiserver|etcd|scheduler|controller"   # three of each
```

:::exam-tip
The exam will not make you build HA. It can ask what `--control-plane-endpoint`
is for, which component is the leader, or how many etcd members may fail.
Know: API servers are all active behind an LB; scheduler/controller manager
are leader-elected through Leases; etcd needs a majority; kubeadm's
`--upload-certs` + `--certificate-key` is how a second control plane gets the
CA.
:::

## Check yourself

1. How do three API servers share the work, and how do three schedulers?
2. Which object tells you which controller manager is currently active?
3. What is the difference between stacked and external etcd, and which does
   kubeadm do by default?
