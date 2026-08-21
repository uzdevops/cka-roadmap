## Who calls the plugin, and with what

On every node the **container runtime** - containerd - is the CNI caller.
The kubelet asks containerd for a Pod sandbox; containerd creates the
network namespace and invokes the CNI plugin for it; the plugin reports the
IP; containerd reports it to the kubelet; the kubelet writes `status.podIP`.

```
kubelet ──CRI──▶ containerd ──CNI (exec)──▶ /opt/cni/bin/<type>  ADD/DEL
                                 ▲
              /etc/cni/net.d/*.conflist   (which plugin, what config)
```

Two directories on the node, both configured on **containerd** (the
kubelet's old `--network-plugin=cni`, `--cni-conf-dir` and `--cni-bin-dir`
flags are gone since dockershim was removed):

```bash
grep -A4 '\[plugins."io.containerd.grpc.v1.cri".cni\]' /etc/containerd/config.toml
#   bin_dir = "/opt/cni/bin"
#   conf_dir = "/etc/cni/net.d"
```

```bash
ls /opt/cni/bin            # plugin binaries
ls /etc/cni/net.d          # configuration; lowest-sorted file wins
cat /etc/cni/net.d/10-flannel.conflist
```

```json
{
  "name": "cbr0",
  "cniVersion": "0.3.1",
  "plugins": [
    {"type": "flannel", "delegate": {"hairpinMode": true, "isDefaultGateway": true}},
    {"type": "portmap", "capabilities": {"portMappings": true}}
  ]
}
```

A `.conflist` is a **chain**: `flannel` sets up the interface and IP (by
delegating to the `bridge` and `host-local` reference plugins with the
node's subnet), then `portmap` adds the iptables rules that make `hostPort`
work. On `DEL` the chain runs in reverse.

## What a CNI DaemonSet does

Installing Flannel or Calico is `kubectl apply -f <manifest>`, which creates
a DaemonSet. On each node its Pod:

1. copies the plugin binary into `/opt/cni/bin` (from a hostPath mount);
2. writes the config file into `/etc/cni/net.d` (from a ConfigMap);
3. sets up the node-level part - reads `node.spec.podCIDR`, creates the
   overlay device or installs routes, runs the BGP agent;
4. keeps running as the agent that maintains routes as nodes come and go.

Which is why, until that DaemonSet's Pod is Running on a node, that node is
`NotReady` (`container runtime network not ready: cni plugin not
initialized`) - and why the DaemonSet's Pod itself must use `hostNetwork:
true` and tolerate every taint: it cannot use the Pod network it has not
built yet.

```bash
kubectl get ds -A | grep -iE "flannel|calico|weave|cilium"
kubectl get pods -n kube-flannel -o wide                # one per node, all Running?
kubectl describe node node01 | grep -i "network"       # the NotReady reason, if any
journalctl -u kubelet | grep -i cni | tail
```

## Installing one on a bare cluster

```bash
kubectl get nodes               # all NotReady after kubeadm init - expected
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
# if your pod CIDR is not 10.244.0.0/16, edit net-conf.json in the ConfigMap first
kubectl get pods -n kube-flannel -w
kubectl get nodes               # Ready once the DaemonSet Pod is up on each node
```

For Calico: `kubectl apply -f .../tigera-operator.yaml` then a `custom-resources.yaml`
with `spec.calicoNetwork.ipPools[0].cidr` equal to your Pod CIDR. For
Weave: `kubectl apply -f https://github.com/weaveworks/weave/releases/download/v2.8.1/weave-daemonset-k8s.yaml`
with `IPALLOC_RANGE` set if your CIDR differs.

:::exam-tip
The install task is graded on the nodes going Ready and Pods getting IPs.
The thing that breaks it: the CNI's configured CIDR not matching the
cluster's `--pod-network-cidr`. Check `kubectl cluster-info dump | grep
cluster-cidr` first, then make the manifest agree before applying. And if
the exam provides the manifest file locally, use that - the exam machine has
no internet.
:::

## Check yourself

1. Which component invokes the CNI plugin for a new Pod, and where does it
   find the plugin and its config?
2. Why must a CNI DaemonSet's Pod use `hostNetwork: true`?
3. A node stays NotReady with "cni plugin not initialized". Which two things
   do you check?
