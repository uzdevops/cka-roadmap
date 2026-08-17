## Why orchestration exists

Containers solved packaging. A container image bundles your application with its
dependencies so that it runs the same way on a laptop, in CI, and in production.
What containers did **not** solve is everything that happens after `docker run`:

- A node dies at 03:00. Who restarts the twelve containers that were on it?
- Traffic triples. Who starts more replicas, and who tells the load balancer?
- You ship a new image. Who replaces the old containers without dropping requests?
- Two services need to find each other. Who hands out the addresses?

Doing this by hand is a rota of humans. Doing it with shell scripts is a rota of
humans plus a pager. Kubernetes is the answer that the industry converged on:
a control loop that continuously drives the cluster toward the state you declared.

## Declarative, not imperative

This is the single idea that everything else in Kubernetes hangs off.

An **imperative** system takes orders: *start three copies of this container*.
If one dies, nothing happens, because the order was already carried out.

A **declarative** system takes a description of the desired outcome:
*there should be three copies of this container*. Kubernetes stores that
description and then works, forever, to make reality match it.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3          # <- the desired state
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: nginx:1.27
          ports:
            - containerPort: 80
```

You submit that document. From then on, if a Pod is deleted, a node is drained,
or a container exits, a controller notices the gap and closes it. You never wrote
"restart it" anywhere.

:::tip
When you are stuck on an exam question, re-read it and ask "what is the desired
state?" The answer is almost always a small YAML change plus `kubectl apply`,
not a sequence of manual steps.
:::

## The reconciliation loop

Every controller in Kubernetes runs the same loop:

1. **Observe** the current state through the API server.
2. **Compare** it to the desired state stored in etcd.
3. **Act** to close the difference.
4. Repeat, forever.

```text
        desired state (spec)
                |
                v
   +------------------------+
   |      controller        |
   |  observe -> diff -> act|
   +------------------------+
                |
                v
        current state (status)
```

Every Kubernetes object therefore has two halves: `spec`, which you write, and
`status`, which the system writes. Getting comfortable reading `status` is what
separates people who can debug a cluster from people who can only create things.

```bash
# spec is what you asked for; status is what actually happened
kubectl get pod web-5d4f8b6c9-abcde -o yaml | less
```

## What Kubernetes gives you

| Capability | What it means in practice |
| --- | --- |
| Self-healing | Failed containers restart; Pods on dead nodes are rescheduled |
| Horizontal scaling | Replica counts change by editing a number, or automatically |
| Service discovery | Stable DNS names and virtual IPs in front of changing Pods |
| Rollouts and rollbacks | Gradual replacement with automatic revision history |
| Configuration management | ConfigMaps and Secrets injected without rebuilding images |
| Storage orchestration | Volumes provisioned and attached on demand |
| Bin packing | The scheduler places Pods based on requested resources |

## What Kubernetes is *not*

The exam expects you to know the boundaries too.

- **Not a PaaS.** It does not build your source code, run your CI, or give you a
  `git push` deploy flow. Those are layers built *on top* of Kubernetes.
- **Not a service mesh.** Retries, mTLS between services, and fine-grained
  traffic splitting come from projects like Istio or Linkerd.
- **Not a monitoring system.** It exposes metrics and events; Prometheus and
  friends collect and alert on them.
- **Not a database or message queue.** It can *run* one, but it provides no
  application-level durability guarantees of its own.
- **Not magic for stateless-hostile applications.** If your app cannot tolerate
  being restarted or moved, Kubernetes will make that worse, not better.

:::warning
A very common misconception: Kubernetes does not guarantee zero downtime by
itself. Rolling updates plus correctly configured readiness probes plus
PodDisruptionBudgets get you there. Any one of them missing and you will drop
requests during an upgrade.
:::

## Where the CKA fits

The Certified Kubernetes Administrator exam is performance-based: a live cluster,
a terminal, and roughly two hours of tasks. Nobody asks you to define
"orchestration". You are asked to *do* things, weighted like this:

- Troubleshooting - 30%
- Cluster architecture, installation and configuration - 25%
- Services and networking - 20%
- Workloads and scheduling - 15%
- Storage - 10%

:::exam-tip
Notice that troubleshooting and cluster administration are more than half the
exam. Being able to create a Deployment quickly is table stakes; being able to
work out *why* one is not progressing is what actually passes the exam. Every
lesson in this roadmap ends with the failure modes, not just the happy path.
:::

## Check yourself

Before moving on, you should be able to answer these without notes:

1. What is the difference between `spec` and `status` on a Kubernetes object?
2. Why does deleting a Pod that belongs to a Deployment not reduce your replica count?
3. Name three things people expect Kubernetes to do that it deliberately does not.
