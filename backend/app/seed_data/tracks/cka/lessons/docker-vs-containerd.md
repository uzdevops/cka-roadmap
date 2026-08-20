## Two names you will hear constantly

For years "Docker" meant the whole stack: the CLI, the daemon, image building,
image storage, the runtime that actually starts processes. Kubernetes only ever
needed the last part - something that can pull an image and run a container -
and the way it asks for that is the **Container Runtime Interface (CRI)**.

Docker's daemon never spoke the CRI natively. Kubernetes carried a shim
(`dockershim`) inside the kubelet to translate. Meanwhile Docker itself had
split its runtime out into a separate project, **containerd**, which *does*
speak the CRI. Once containerd was mature, the shim had no reason to exist.

```
kubelet ──CRI──▶ containerd ──▶ runc ──▶ your process
          (gRPC)               (OCI)
```

- **containerd** - the high-level runtime: pulls images, manages storage and
  snapshots, supervises containers. Talks CRI to the kubelet.
- **runc** - the low-level runtime: given a filesystem bundle and an OCI
  config, creates the Linux namespaces and cgroups and execs the process.
- **CRI-O** - an alternative high-level runtime built only for Kubernetes.
  Same contract, different project.

## The three CLIs

This is where the confusion lives. On a node running containerd you may find
three tools, and they are not interchangeable.

| Tool | Talks to | Purpose | Use it for |
|---|---|---|---|
| `ctr` | containerd | containerd's own debug CLI | almost nothing - it is not user-friendly and not for production |
| `nerdctl` | containerd | Docker-compatible CLI | running containers by hand on a node the way you would with `docker` |
| `crictl` | any CRI runtime | CRI debugging CLI | **inspecting what the kubelet started** - the one the exam cares about |

```bash
# What the kubelet is running on this node - including control plane containers
crictl ps
crictl ps -a                      # include exited containers
crictl logs <container-id>        # when kubectl logs cannot reach the API server
crictl images
crictl pods                       # the sandboxes (one per Pod)
```

:::exam-tip
When the API server is down, `kubectl` is useless but `crictl` still works on
the control plane node: `crictl ps -a | grep apiserver` then `crictl logs
<id>` is how you read why it crashed. This is a troubleshooting-domain move
worth a whole task.
:::

`crictl` is configured through `/etc/crictl.yaml`:

```yaml
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
```

If `crictl` complains it cannot connect, that file (or the `--runtime-endpoint`
flag) is the first thing to check.

## Images did not change

An important point that gets lost in the noise: a Docker image is an **OCI
image**. containerd runs it unchanged. Everything you build with `docker
build` today still runs on every Kubernetes cluster; what went away was a
*runtime* path, not an image format.

:::note
`nerdctl build` exists if you want to build images on a node without Docker,
but building on cluster nodes is an anti-pattern anyway - that belongs in CI.
:::

## Why this matters for the administrator

- **Installing a cluster**: kubeadm needs a CRI runtime present before
  `kubeadm init` - installing and configuring containerd is step one of the
  installation lesson later in this track.
- **Troubleshooting a node**: a `NotReady` node with a dead container runtime
  looks exactly like a dead kubelet from `kubectl`'s side. `systemctl status
  containerd` and `crictl ps` tell them apart.
- **Reading the kubelet's logs**: CRI errors name the socket and the runtime,
  so you need to recognise them.

## Check yourself

1. The API server is down. Which command shows you the API server container's
   logs, and on which node do you run it?
2. What is the difference between containerd and runc?
3. A colleague says "we can't use Docker images any more because dockershim was
   removed." What is wrong with that sentence?
