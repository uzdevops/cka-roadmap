## The announcement that scared everyone

In late 2020 the Kubernetes project announced that `dockershim` - the piece of
the kubelet that translated between Kubernetes and the Docker daemon - was
deprecated, and in Kubernetes 1.24 it was removed. The headline "Kubernetes
drops Docker" went round the world and was misread almost everywhere.

What was actually removed: **one way for the kubelet to start containers**.

What was not removed: Docker images, Dockerfiles, `docker build`, Docker
Desktop, Docker Hub, or any workload anyone was running.

## What really changed on a node

Before 1.24, a node could run the Docker daemon and the kubelet would talk to
it through the shim:

```
kubelet ──dockershim──▶ dockerd ──▶ containerd ──▶ runc
```

Note that containerd was already in the chain - Docker itself used it. The shim
just added a hop. After 1.24 the kubelet talks to containerd directly:

```
kubelet ──CRI──▶ containerd ──▶ runc
```

The node ends up running *less* software, not different software.

## What you, the administrator, had to do

If a node used Docker as its runtime, the migration was:

1. Install containerd (usually already present - Docker depends on it) and
   enable its CRI plugin in `/etc/containerd/config.toml`.
2. Point the kubelet at the containerd socket:
   `--container-runtime-endpoint=unix:///run/containerd/containerd.sock`.
3. Drain the node, restart the kubelet, uncordon.

Docker's own answer for people who wanted to keep `dockerd` on nodes was
**cri-dockerd**, an external shim maintained by Mirantis. It works, but almost
nobody needs it.

:::warning
`docker ps` on a modern node shows **nothing** about the Pods running there -
the kubelet is not using Docker. The habit of "let me just docker ps on the
node" is the one to unlearn. Use `crictl ps`.
:::

## Where it still shows up in the exam

- Cluster installation tasks assume containerd; you will configure it, not
  Docker.
- Troubleshooting tasks may put a node into `NotReady` by stopping the
  container runtime; the fix is `systemctl start containerd`, not anything
  Docker-related.
- Questions about images are unchanged: image names, tags, pull policies and
  private registries work exactly as they always did.

:::tip
If a Dockerfile is in front of you, nothing here applies - it still builds an
OCI image, and that image still runs everywhere. The deprecation was about the
daemon on the node, never about the artefact.
:::

## Check yourself

1. What exactly did Kubernetes 1.24 remove, in one sentence?
2. A node shows `NotReady`; `docker ps` on it prints nothing. Why does that
   prove nothing, and what do you run instead?
3. What is `cri-dockerd`, and when would you actually want it?
