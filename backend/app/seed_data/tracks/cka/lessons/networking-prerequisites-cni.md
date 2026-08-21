## Everyone was writing the same script

Docker, rkt, Mesos, Kubernetes - every container system had to do the same
steps per container: create a namespace, make a veth pair, attach it to a
bridge, assign an IP, add routes, and undo it all on delete. Each wrote its
own code. The **Container Network Interface** is the agreement to stop: one
interface that a runtime calls and a plugin implements.

```
runtime (kubelet via containerd) ──▶ plugin binary: ADD <container-id> <netns>  ──▶ plugin configures the network, returns the IP
                                  ──▶ plugin binary: DEL <container-id> <netns>  ──▶ plugin cleans up
```

The contract, in full:

- The runtime creates the network namespace.
- It identifies the network the container should join (from a config file).
- It calls the plugin **executable** with `ADD` (or `DEL`, `CHECK`,
  `VERSION`), passing the container ID and the namespace path, plus the
  config on stdin.
- The plugin does whatever it does and prints a JSON result with the
  interfaces and IPs it created.

A plugin is **any program** that handles those verbs. Most are written in Go;
you could write one in bash.

## Where the pieces live on a node

```bash
ls /opt/cni/bin/
# bridge  dhcp  flannel  host-local  loopback  macvlan  portmap  ptp  tuning  vlan  ...  (plus calico, weave-net, cilium-cni when installed)
ls /etc/cni/net.d/
# 10-flannel.conflist      (or 10-calico.conflist, 05-cilium.conflist, ...)
```

| Path | Holds |
|---|---|
| `/opt/cni/bin` | the plugin binaries (`--cni-bin-dir`) |
| `/etc/cni/net.d` | the network configuration; the **first file alphabetically** is used (`--cni-conf-dir`) |

```bash
cat /etc/cni/net.d/10-bridge.conf
```

```json
{
  "cniVersion": "1.0.0",
  "name": "mynet",
  "type": "bridge",                 # which binary in /opt/cni/bin to run
  "bridge": "cni0",
  "isGateway": true,
  "ipMasq": true,
  "ipam": {
    "type": "host-local",           # a second plugin, for address management
    "subnet": "10.244.1.0/24",
    "routes": [{"dst": "0.0.0.0/0"}]
  }
}
```

Read that config against the namespace lesson: `type: bridge` is the script
you ran by hand; `isGateway` gives the bridge an IP; `ipMasq` adds the
MASQUERADE rule; `ipam` picks the IP from the subnet.

A `.conflist` chains several plugins: `flannel` then `portmap` (hostPort
support) then `bandwidth`. Each runs in order for ADD, reverse for DEL.

## Reference plugins vs real CNIs

The CNI project ships a set of **reference plugins** - `bridge`, `ptp`,
`macvlan`, `host-local`, `dhcp`, `portmap`, ... - the building blocks. A
**cluster CNI** like Flannel, Calico, Cilium or Weave uses or replaces them
and adds the part the reference plugins lack: making Pod subnets on
*different nodes* reachable from each other (routes, VXLAN, BGP, eBPF).
Kubernetes itself ships **no** CNI: after `kubeadm init` the nodes are
`NotReady` until you install one, and that is by design.

## What Kubernetes is not responsible for

- Creating the namespace: the runtime.
- Which IP: the IPAM plugin.
- Cross-node reachability: the cluster CNI.
- **Services**: not CNI at all - that is kube-proxy (or a CNI like Cilium
  that chooses to replace kube-proxy).
- **NetworkPolicy**: the CNI, if it supports it. Flannel does not.

:::exam-tip
Two node-level facts to find fast: `ls /etc/cni/net.d` tells you **which**
CNI is configured (the file name says it); `ls /opt/cni/bin` tells you which
plugin binaries exist. A node where the first is empty has no CNI - Pods
stuck `ContainerCreating` with `failed to find plugin` or `no networks found`
in `describe pod`. The fix is installing one, usually `kubectl apply -f` of
the CNI's manifest.
:::

## Check yourself

1. What does the runtime do, and what does the CNI plugin do, when a Pod
   starts?
2. Which directory holds CNI configuration, and which file in it is used?
3. Name two things people think are CNI's job that are not.
