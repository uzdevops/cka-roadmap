## The order of an upgrade

```
1. kubeadm (the tool)          on the control plane node
2. control plane                kubeadm upgrade apply  -> API server, controller manager, scheduler, etcd, CoreDNS, kube-proxy
3. kubelet + kubectl            on the control plane node
4. each worker, one at a time:  drain -> kubeadm upgrade node -> kubelet -> uncordon
```

The order is dictated by the version-skew rules: the API server must be the
newest thing; kubelets may lag behind it, never lead it; `kubeadm` has to be
the new version to know how to produce the new manifests.

Two strategies for the workers:

- **Rolling** - drain, upgrade, uncordon one node at a time. The cluster stays
  up throughout; capacity drops by one node at a time.
- **Add new, remove old** - bring up nodes already on the new version, drain
  and delete the old ones. Cleaner for clouds with node groups; more work on
  bare metal.

One minor version per upgrade. 1.29 → 1.30, then 1.30 → 1.31.

## kubeadm's view of it

```bash
kubeadm upgrade plan
```

```
[upgrade/versions] Cluster version: v1.29.4
[upgrade/versions] kubeadm version: v1.30.2
Components that must be upgraded manually after you have upgraded the control plane with 'kubeadm upgrade apply':
COMPONENT   NODE           CURRENT   TARGET
kubelet     controlplane   v1.29.4   v1.30.2
kubelet     node01         v1.29.4   v1.30.2

Upgrade to the latest stable version:
COMPONENT                 NODE           CURRENT   TARGET
kube-apiserver            controlplane   v1.29.4   v1.30.2
kube-controller-manager   controlplane   v1.29.4   v1.30.2
kube-scheduler            controlplane   v1.29.4   v1.30.2
kube-proxy                               1.29.4    v1.30.2
CoreDNS                                  v1.11.1   v1.11.1
etcd                      controlplane   3.5.12-0  3.5.12-0

You can now apply the upgrade by executing the following command:
        kubeadm upgrade apply v1.30.2
```

`plan` reads as a checklist: it tells you the target, which components
`apply` will handle, and - in the "manually" section - the kubelets you have
to do yourself. Run it before every upgrade; it also checks that the jump is
allowed.

## What `kubeadm upgrade apply` does

On the control plane node, with the new kubeadm installed:

1. checks the cluster is healthy and the version jump is legal;
2. pulls the new control plane images;
3. rewrites the static Pod manifests in `/etc/kubernetes/manifests` one
   component at a time, waiting for each to come back healthy (the kubelet
   restarts them);
4. upgrades the kube-proxy DaemonSet and CoreDNS;
5. renews the certificates it manages;
6. writes the new version into the `kubeadm-config` ConfigMap.

It does **not** touch the kubelet binary or the node's packages - that is the
manual step after it.

On additional control plane nodes (HA) and on workers the command is
`kubeadm upgrade node`: it reads the new configuration from the cluster and
updates the local kubelet config (and, on control plane nodes, the local
static Pod manifests). No version argument - it follows what `apply` already
set.

## The worker side

```bash
# from a machine with kubectl:
kubectl drain node01 --ignore-daemonsets
# on node01:
apt-get install -y kubeadm=1.30.2-*
kubeadm upgrade node
apt-get install -y kubelet=1.30.2-* kubectl=1.30.2-*
systemctl daemon-reload && systemctl restart kubelet
# back on the control plane:
kubectl uncordon node01
kubectl get nodes            # node01 shows v1.30.2
```

:::exam-tip
The task will say which version, and it is usually the next minor's latest
patch. Do the control plane first, **check `kubectl get nodes` shows the new
VERSION on it**, then the worker. If the worker still shows the old version
after you are done, you forgot to restart the kubelet - `systemctl restart
kubelet` and look again. The VERSION column is the kubelet's version.
:::

## Things that commonly go wrong

| Symptom | Cause |
|---|---|
| `kubeadm=1.30.2-*` not found | the package repository still points at `/v1.29/` |
| `upgrade apply` refuses: "skipping phase ... pre-flight" | control plane unhealthy - fix that first, or the specific check it names |
| node shows old version after upgrade | kubelet not upgraded, or not restarted |
| a Pod is stuck during drain | a PDB, or an unmanaged Pod without `--force` |

## Check yourself

1. Write the four phases of an upgrade in order, and say which node each one
   runs on.
2. What does `kubeadm upgrade apply` change, and what does it leave for you to
   do by hand?
3. A worker still reports the old version in `kubectl get nodes` after you
   ran every command. What did you most likely skip?
