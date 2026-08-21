## Bringing up a two-node cluster

Nodes `controlplane` (192.168.56.11) and `node01` (192.168.56.21), both
prepped as in the previous lesson. Every command here is one you will type
in the install lab and in the exam.

### 1. On the control plane: init

```bash
kubeadm init \
  --pod-network-cidr=10.244.0.0/16 \
  --apiserver-advertise-address=192.168.56.11
```

Watch it go through the phases. It ends with three things to copy:

```
Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:
  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

You should now deploy a pod network to the cluster. ...

Then you can join any number of worker nodes by running the following on each as root:
kubeadm join 192.168.56.11:6443 --token x1y2z3.abcdefghij123456 \
        --discovery-token-ca-cert-hash sha256:9f2d...
```

Do the first block immediately; save the join command somewhere.

```bash
mkdir -p $HOME/.kube && sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config && sudo chown $(id -u):$(id -g) $HOME/.kube/config
kubectl get nodes
# controlplane   NotReady   control-plane   40s   v1.30.2      <- NotReady is expected: no CNI yet
kubectl get pods -n kube-system
# coredns-...    Pending                                        <- also expected
# etcd-controlplane, kube-apiserver-controlplane, ... Running
```

### 2. The CNI

```bash
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
# (its default Network is 10.244.0.0/16 - matching --pod-network-cidr; edit the ConfigMap if yours differs)
kubectl get pods -n kube-flannel -w
kubectl get nodes
# controlplane   Ready   control-plane   3m   v1.30.2
kubectl get pods -n kube-system | grep coredns       # Running now
```

### 3. On the worker: join

```bash
kubeadm join 192.168.56.11:6443 --token x1y2z3.abcdefghij123456 \
  --discovery-token-ca-cert-hash sha256:9f2d...
# [preflight] Running pre-flight checks
# ...
# This node has joined the cluster
```

Lost the command? On the control plane:

```bash
kubeadm token create --print-join-command
```

### 4. Verify

```bash
kubectl get nodes -o wide
# controlplane   Ready   control-plane   5m   v1.30.2   192.168.56.11
# node01         Ready   <none>          1m   v1.30.2   192.168.56.21
kubectl get pods -A -o wide            # flannel and kube-proxy on both nodes, CoreDNS Running
kubectl run test --image=nginx
kubectl get pod test -o wide           # scheduled to node01, has a 10.244.x.x IP
kubectl exec test -- curl -s kubernetes.default.svc   # DNS + Service + API: a 403 JSON answer means the network works end to end
```

The control plane is tainted, so `test` went to node01. On a one-node lab,
remove the taint to schedule there:

```bash
kubectl taint nodes controlplane node-role.kubernetes.io/control-plane:NoSchedule-
```

### 5. When it goes wrong

| Symptom | Fix |
|---|---|
| `init` fails preflight | read the `[ERROR ...]` line: swap, CPUs, ports in use (a previous attempt - `kubeadm reset -f`), runtime down |
| `init` hangs at "waiting for the kubelet to boot up the control plane" | `journalctl -u kubelet -f` on the node: cgroup driver mismatch with containerd, or the kubelet cannot pull images (no internet / wrong `sandbox_image`) |
| nodes stay NotReady after the CNI | `kubectl get pods -n kube-flannel -o wide` - the DaemonSet Pod on that node; CIDR mismatch in its logs |
| `join` fails: token invalid | expired (24 h) - `kubeadm token create --print-join-command` |
| `join` fails: `/etc/kubernetes/kubelet.conf already exists` | stale previous attempt - `kubeadm reset -f` on the worker, then join |
| `kubectl` on the control plane: `connection refused localhost:8080` | you skipped copying `admin.conf` |
| `kubectl get nodes -o wide` shows the NAT IP 10.0.2.15 | set `KUBELET_EXTRA_ARGS=--node-ip=<private ip>` in `/etc/default/kubelet`, restart the kubelet |

:::exam-tip
The install task's scoring is `kubectl get nodes` showing every node Ready
on the requested version, and usually a Pod running on the worker. Do the
four steps in order, copy `admin.conf` before touching kubectl, make the CNI
CIDR match, and keep the join command. If the exam gives you a `kubeadm`
config file or a specific version, `kubeadm init --config` / `--kubernetes-version`
- read the task twice.
:::

## Check yourself

1. Why is the control plane node NotReady right after a successful init, and
   what makes it Ready?
2. You lost the join command. How do you get a new one?
3. `init` sits for minutes at "waiting for the kubelet". What do you look at?
