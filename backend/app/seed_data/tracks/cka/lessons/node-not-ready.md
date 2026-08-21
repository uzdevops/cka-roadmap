## A node goes NotReady

```bash
kubectl get nodes
# NAME       STATUS     ROLES           AGE   VERSION
# node01     NotReady   <none>          10d   v1.31.0
kubectl describe node node01
```

`describe node` tells you two things before you ssh anywhere.

**Conditions**:

```
Conditions:
  Type             Status    LastHeartbeatTime   Reason              Message
  MemoryPressure   Unknown   ...                 NodeStatusUnknown   Kubelet stopped posting node status.
  DiskPressure     Unknown
  PIDPressure      Unknown
  Ready            Unknown   ...                 NodeStatusUnknown   Kubelet stopped posting node status.
```

- `Ready False` with a Reason: the kubelet is running and reporting a
  problem (container runtime down, network plugin not ready, disk full).
- `Ready Unknown` and every condition `Unknown`: the kubelet has **stopped
  talking** to the API server - stopped, crashed, certificates, network,
  the node is off.
- `MemoryPressure`/`DiskPressure`/`PIDPressure` `True`: the node is alive
  but starved; the kubelet evicts Pods and refuses new ones.

**Events and capacity**: `Allocatable` vs requests, and Events like
`NodeHasDiskPressure`, `ContainerGCFailed`, `Rebooted`.

## On the node

```bash
ssh node01
top; free -h; df -h /; df -h /var/lib/kubelet /var/lib/containerd     # alive? starved?
systemctl status kubelet
journalctl -u kubelet -n 100 --no-pager                                 # the explanation is almost always here
systemctl status containerd                                             # the kubelet cannot run Pods without it
```

If the node itself is down (no ssh), it is infrastructure: start it. When
it comes back, the kubelet starts and the node turns Ready; if it does not,
continue below.

## The kubelet will not start or keeps failing

```bash
systemctl status kubelet
# ● kubelet.service - kubelet: The Kubernetes Node Agent
#    Active: activating (auto-restart) (Result: exit-code)
journalctl -u kubelet -f
```

The log names the cause. The four usual ones:

| Log line | Cause | Fix |
|---|---|---|
| `failed to load Kubelet config file /var/lib/kubelet/config.yaml` / `open /etc/kubernetes/pki/CA.crt: no such file` | a wrong path in **`/var/lib/kubelet/config.yaml`** (`clientCAFile`, `staticPodPath`) | correct the path (`ls /etc/kubernetes/pki/` to see the real name); `systemctl restart kubelet` |
| `dial tcp 10.0.0.10:6553: connect: connection refused` / `Unable to register node` | wrong API server **address or port** in **`/etc/kubernetes/kubelet.conf`** (`server: https://...:6443`) | fix the server line; restart kubelet |
| `part of the existing bootstrap client certificate is expired` / `x509: certificate has expired` | kubelet **client cert** expired (`/var/lib/kubelet/pki/kubelet-client-current.pem`) | `kubeadm certs renew` on control plane does not cover kubelet certs; re-bootstrap with a new token or fix rotation; check clock |
| `x509: certificate signed by unknown authority` | kubelet trusts a CA that did not sign the API server | the `certificate-authority-data` in `kubelet.conf` is wrong - compare with `/etc/kubernetes/pki/ca.crt` |
| `Failed to start ContainerManager` / `failed to run Kubelet: ... cgroup` | cgroup driver mismatch (kubelet `systemd` vs containerd `cgroupfs`) | align `cgroupDriver` in config.yaml with containerd's config |
| `Unit kubelet.service is masked` / `not found` | the service itself | `systemctl unmask kubelet`; `systemctl enable --now kubelet`; is `kubelet` binary on PATH? |

```bash
cat /var/lib/kubelet/config.yaml | grep -E "clientCAFile|staticPodPath|cgroupDriver|address|port"
cat /etc/kubernetes/kubelet.conf | grep server
ls /etc/kubernetes/pki/ /var/lib/kubelet/pki/
openssl x509 -in /var/lib/kubelet/pki/kubelet-client-current.pem -noout -dates -issuer
cat /etc/systemd/system/kubelet.service.d/10-kubeadm.conf                  # how the kubelet is launched: flags, env files
```

The **three files** of the kubelet, in the order to check them:

1. `/var/lib/kubelet/config.yaml` - the KubeletConfiguration: CA path,
   static Pod path, cgroup driver, cluster DNS, eviction thresholds.
2. `/etc/kubernetes/kubelet.conf` - the kubeconfig it uses to reach the
   API server: server URL, CA data, client cert path.
3. `/etc/systemd/system/kubelet.service.d/10-kubeadm.conf` (+
   `/var/lib/kubelet/kubeadm-flags.env`) - the systemd drop-in with the
   flags that point at 1 and 2.

After any edit: `systemctl daemon-reload` if you touched the unit,
`systemctl restart kubelet`, then `journalctl -u kubelet -f` until it says
`Successfully registered node`, and `kubectl get nodes` from the control
plane until `Ready`.

## The kubelet is fine but the node is still NotReady

```bash
journalctl -u kubelet | grep -iE "network|cni"
# "Container runtime network not ready: NetworkReady=false reason:NetworkPluginNotReady message:Network plugin returns error: cni plugin not initialized"
ls /etc/cni/net.d/ /opt/cni/bin/
kubectl get pods -n kube-system -o wide | grep node01            # is the CNI DaemonSet Pod running on this node?
```

No CNI config → the node reports NotReady by design. Fix the network
plugin (its DaemonSet Pod on that node, the config file), not the kubelet.

```bash
systemctl status containerd; crictl ps                            # runtime down → kubelet cannot run anything
```

## Pods on a NotReady node

After `--node-monitor-grace-period` (40s) the node is marked NotReady;
after the Pod's toleration for `node.kubernetes.io/not-ready` (default
300s) the controller evicts its Pods and Deployments recreate them
elsewhere. Pods stuck `Terminating` on a dead node stay until the node
returns or you force-delete them.

:::exam-tip
The exam's worker-node question is: a node is NotReady; `ssh` in; `systemctl
status kubelet`; `journalctl -u kubelet`; the log names a wrong path, port
or certificate in one of the three files; fix; `systemctl restart kubelet`;
`exit`; `kubectl get nodes` until Ready. Two traps: the API server port
typed as `6553` in kubelet.conf, and a CA file name that differs by case
(`CA.crt` vs `ca.crt`) in config.yaml.
:::

## Check yourself

1. What is the difference between `Ready False` and `Ready Unknown` on a
   node?
2. Name the three kubelet files and what each one configures.
3. The kubelet is running and registered but the node is NotReady with
   `NetworkPluginNotReady`. What do you fix, and what do you not touch?
