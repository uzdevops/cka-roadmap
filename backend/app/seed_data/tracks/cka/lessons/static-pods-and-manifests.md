## Pods without an API server

A kubelet can run Pods from files on its own disk, with no API server and no
scheduler involved. Drop a Pod manifest into the kubelet's **static Pod path**
and the kubelet creates it, restarts it if it dies, and removes it when the
file goes away. These are **static Pods**.

That is how a kubeadm control plane boots: the API server, controller
manager, scheduler and etcd are static Pods in `/etc/kubernetes/manifests`.
The kubelet starts them from files; *then* there is an API server for
everything else to talk to.

```bash
grep staticPodPath /var/lib/kubelet/config.yaml
# staticPodPath: /etc/kubernetes/manifests
ls /etc/kubernetes/manifests
# etcd.yaml  kube-apiserver.yaml  kube-controller-manager.yaml  kube-scheduler.yaml
```

:::exam-tip
The path is not always the default. Read it from `/var/lib/kubelet/config.yaml`
(`staticPodPath`), or from the kubelet's `--pod-manifest-path` flag on older
setups. A task can put it somewhere unusual and ask you to find it.
:::

## Mirror Pods

The kubelet reports each static Pod to the API server as a **mirror Pod** so
that `kubectl get pods` shows it. You can see it but not control it: delete
the mirror and the kubelet recreates it; edit it and nothing changes. The only
way to change or remove a static Pod is to change or remove its **file** on
the node.

The tell is the name: a mirror Pod's name is the manifest name plus `-` plus
the **node name**.

```bash
kubectl get pods -A | grep controlplane
# kube-system   etcd-controlplane                      1/1  Running
# kube-system   kube-apiserver-controlplane            1/1  Running
kubectl get pod kube-apiserver-controlplane -n kube-system -o yaml | grep -A2 ownerReferences
#   ownerReferences:
#   - kind: Node            <- owned by the node, not by a ReplicaSet
```

## Creating one

```bash
# on the node
kubectl run static-busybox --image=busybox --command -- sleep 1000 $do \
  > /etc/kubernetes/manifests/static-busybox.yaml
# ~20 s later
kubectl get pods
# static-busybox-controlplane   1/1   Running
```

The kubelet polls the directory (every 20 seconds by default), so there is a
short delay. Editing the file in place recreates the Pod; deleting the file
deletes it.

```bash
# which node? find the manifest on THAT node, not on the control plane
kubectl get pod static-greenbox-node01 -o wide       # NODE column
ssh node01
ls /etc/kubernetes/manifests                          # or wherever staticPodPath points
rm /etc/kubernetes/manifests/static-greenbox.yaml
```

:::warning
Static Pods are only ever **Pods** - no Deployments, DaemonSets or Services
from the manifest directory. A Service manifest dropped in there is ignored
(with a log line in `journalctl -u kubelet`).
:::

## Why this matters beyond the control plane

- **Troubleshooting**: a control plane component that crash-loops is a static
  Pod with a bad manifest. You fix the file, the kubelet restarts it. No
  `kubectl apply`, no `systemctl restart` - just save the file and wait.
- **Cluster upgrades**: `kubeadm upgrade apply` rewrites those manifests with
  the new image tags; the kubelet does the rolling.
- **Bootstrapping**: anything that must exist before the API server does.

## Check yourself

1. How can you tell from `kubectl get pods -A` which Pods are static?
2. You `kubectl delete` a static Pod and it comes back. How do you actually
   remove it?
3. The kube-scheduler static Pod is crash-looping. What do you edit, and what
   restarts it?
