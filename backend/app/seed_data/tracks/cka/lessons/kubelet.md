## The agent on every node

Every node - worker and control plane alike - runs one kubelet. It is the only
Kubernetes component that is **not** a Pod: it is a systemd service on the
host, because something has to be running before any Pod can exist, and the
kubelet is that something. Its job:

1. **Register** the node with the API server and keep sending heartbeats
   (node status every ten seconds by default).
2. **Watch** the API server for Pods assigned to this node (`spec.nodeName`
   equals its name).
3. For each one: pull the images through the CRI, create the sandbox and the
   containers, mount the volumes, inject the environment and Secrets.
4. **Probe** the containers and restart them according to the restart policy.
5. **Report** Pod status and resource usage back.
6. Run **static Pods** from a manifest directory - the mechanism the whole
   control plane boots from on kubeadm clusters.

```
API server ◀──▶ kubelet ──CRI──▶ containerd ──▶ containers
                   │
                   └── /etc/kubernetes/manifests  (static Pods)
```

## How it runs and where it is configured

```bash
systemctl status kubelet
journalctl -u kubelet -f                              # its logs - no kubectl logs for the kubelet
ps -ef | grep kubelet | tr ' ' '\n' | grep -- --       # the flags it started with
```

On a kubeadm node the interesting configuration is split across three files:

| File | Holds |
|---|---|
| `/var/lib/kubelet/config.yaml` | the KubeletConfiguration: `staticPodPath`, `clusterDNS`, `authentication.x509.clientCAFile`, eviction thresholds, cgroup driver |
| `/etc/kubernetes/kubelet.conf` | the kubeconfig it uses to talk to the API server - server URL, its own client certificate |
| `/var/lib/kubelet/kubeadm-flags.env` | the few flags kubeadm still passes: runtime endpoint, pod-infra image |

```bash
grep -E "staticPodPath|clusterDNS|clientCAFile" /var/lib/kubelet/config.yaml
grep server /etc/kubernetes/kubelet.conf
```

:::exam-tip
Worker-node troubleshooting tasks almost always end in one of those files. A
wrong `server:` port in `kubelet.conf`, a wrong CA path in `config.yaml`, or a
kubelet that is simply stopped - the symptom in all three cases is the same
`NotReady` node, and `journalctl -u kubelet` tells them apart in one screen.
:::

## NotReady, and how to read it

```bash
kubectl get nodes
kubectl describe node node01 | grep -A6 Conditions
```

`Ready False` with `KubeletNotReady` or `Unknown` means the API server has
stopped hearing from the kubelet. On the node:

```bash
systemctl status kubelet       # inactive? -> systemctl start kubelet
journalctl -u kubelet | tail -30
```

The messages you learn to recognise:

| Log says | Means |
|---|---|
| `failed to load Kubelet config file ... no such file` | path in the systemd drop-in or a missing config.yaml |
| `x509: certificate signed by unknown authority` / `unable to load client CA file` | wrong `clientCAFile` in config.yaml |
| `dial tcp 127.0.0.1:6553: connect: connection refused` | wrong API server port/address in kubelet.conf |
| `failed to run Kubelet: ... cgroup driver` | kubelet and containerd disagree on cgroupfs vs systemd |
| `Error getting node ... node "node01" not found` | the node name does not match what the kubelet registered as |

After a fix: `systemctl daemon-reload && systemctl restart kubelet`.

## The kubelet's own API

The kubelet listens on port **10250**. That is what the API server calls for
`kubectl logs`, `kubectl exec` and `kubectl top` - which is why those commands
can break while `kubectl get` still works (wrong `--kubelet-client-*`
certificates on the API server, or a firewall between control plane and node).

:::warning
The kubelet's port 10250 is authenticated and authorised in a kubeadm cluster
- but the read-only port 10255, if enabled, is not. It is disabled by
default; keep it that way.
:::

## Check yourself

1. Why is the kubelet a systemd service rather than a Pod?
2. A node is `NotReady`. Give the three commands you run on it, in order.
3. `kubectl get pods` works but `kubectl logs` times out for Pods on one node.
   Which port and which component are involved?
