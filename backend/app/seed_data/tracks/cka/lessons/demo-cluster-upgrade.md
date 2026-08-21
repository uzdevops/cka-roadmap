## A full minor upgrade, command by command

Two nodes - `controlplane` and `node01` - on 1.29.4, going to 1.30.2 with
apt. Follow along on your own cluster; every line is one you will type in the
exam in the same order.

### 0. Before touching anything

```bash
kubectl get nodes
# controlplane   Ready   control-plane   v1.29.4
# node01         Ready   <none>          v1.29.4
kubectl get pods -n kube-system           # everything Running?
```

### 1. Point the package repository at the new minor

On **both** nodes:

```bash
# Debian/Ubuntu
sed -i 's#/v1.29/#/v1.30/#' /etc/apt/sources.list.d/kubernetes.list
apt-get update
apt-cache madison kubeadm | head -3       # 1.30.2-1.1 should appear
```

(On RHEL-family systems it is the `baseurl` in `/etc/yum.repos.d/kubernetes.repo`.)

### 2. Control plane: kubeadm first

```bash
apt-mark unhold kubeadm
apt-get install -y kubeadm=1.30.2-1.1
apt-mark hold kubeadm
kubeadm version                           # v1.30.2
kubeadm upgrade plan                      # read it - target v1.30.2, the kubelets listed as manual
```

### 3. Control plane: drain and apply

```bash
kubectl drain controlplane --ignore-daemonsets
kubeadm upgrade apply v1.30.2
# ... [upgrade/successful] SUCCESS! Your cluster was upgraded to "v1.30.2". Enjoy!
# ... [upgrade/kubelet] Now that your control plane is upgraded, please proceed with upgrading your kubelets
```

During `apply` the API server restarts; `kubectl` pauses for ~30 s. Normal.

### 4. Control plane: kubelet and kubectl

```bash
apt-mark unhold kubelet kubectl
apt-get install -y kubelet=1.30.2-1.1 kubectl=1.30.2-1.1
apt-mark hold kubelet kubectl
systemctl daemon-reload
systemctl restart kubelet
kubectl uncordon controlplane
kubectl get nodes
# controlplane   Ready   control-plane   v1.30.2    <- the control plane is done
# node01         Ready   <none>          v1.29.4
```

### 5. Worker: drain from the control plane, upgrade on the node

```bash
kubectl drain node01 --ignore-daemonsets
```

```bash
# on node01
apt-mark unhold kubeadm
apt-get install -y kubeadm=1.30.2-1.1
apt-mark hold kubeadm
kubeadm upgrade node                       # updates the local kubelet configuration from the cluster
apt-mark unhold kubelet kubectl
apt-get install -y kubelet=1.30.2-1.1 kubectl=1.30.2-1.1
apt-mark hold kubelet kubectl
systemctl daemon-reload
systemctl restart kubelet
```

```bash
# back on the control plane
kubectl uncordon node01
kubectl get nodes
# controlplane   Ready   control-plane   v1.30.2
# node01         Ready   <none>          v1.30.2
```

### 6. Verify

```bash
kubectl get pods -n kube-system -o wide     # all Running, kube-proxy/CoreDNS on new images
kubectl get all -A | grep -v Running | head  # anything not happy?
kubeadm upgrade plan                        # "You're up to date"
```

:::exam-tip
Six things candidates skip, in order of frequency: the repo change (then
`apt` cannot find the version), `apt-mark unhold` (then `apt` refuses), the
kubelet restart (then the node shows the old version), uncordon (then the
next task's Pods never schedule), doing the worker before the control plane
(then `kubeadm upgrade node` complains), and `--ignore-daemonsets` on drain.
Read this list once more the night before.
:::

:::tip
`apt-mark hold` is why the packages do not get upgraded accidentally by an
unrelated `apt-get upgrade`. Unhold, install the exact version, hold again -
three lines that belong together.
:::

## Check yourself

1. Which two commands run **only** on the control plane node and nowhere
   else?
2. Why does `kubeadm upgrade node` take no version argument?
3. `apt-get install kubeadm=1.30.2-1.1` says "version not found". What did you
   skip?
