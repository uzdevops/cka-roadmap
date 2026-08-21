## Where the numbers come from

Kubernetes does not store metrics. Out of the box, `kubectl top` answers
"what is using CPU and memory right now" - and only right now - and it needs
one add-on to do even that: the **Metrics Server**.

```
kubelet (cAdvisor inside it) ──▶ metrics-server ──▶ API server (metrics.k8s.io) ──▶ kubectl top / HPA
```

- Every **kubelet** already collects CPU and memory per container through
  cAdvisor and exposes them on its own port.
- **metrics-server** scrapes every kubelet every 15 seconds or so, keeps the
  latest values in memory, and registers an aggregated API
  (`metrics.k8s.io`) with the API server.
- `kubectl top` and the HorizontalPodAutoscaler read that API.

No history, no dashboards, no alerting. For those you add Prometheus (or a
vendor product) - that is outside the CKA; the exam's observability is
Metrics Server, `kubectl top`, `describe`, events and logs.

## Installing Metrics Server

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl get deployment metrics-server -n kube-system
kubectl top nodes          # works once the Pod is Ready and one scrape has happened
```

On kind, minikube and many lab clusters the kubelets serve self-signed
certificates and Metrics Server refuses to scrape them. The usual fix is one
argument on its container:

```bash
kubectl edit deployment metrics-server -n kube-system
# under containers[0].args add:  - --kubelet-insecure-tls
```

:::exam-tip
`kubectl top` returning `error: Metrics API not available` means Metrics
Server is not installed or not Ready - check `kubectl get pods -n kube-system
| grep metrics`. It is rarely the task itself; it is the thing blocking the
task that asks "which Pod uses the most CPU".
:::

## Using what it gives you

```bash
kubectl top nodes
# NAME           CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
# controlplane   180m         9%     1204Mi          31%
# node01         42m          2%     612Mi           16%

kubectl top nodes --sort-by=memory
kubectl top pods -A --sort-by=cpu | head
kubectl top pods -n kube-system --containers         # per container
kubectl top pod web -l app=web
```

`--sort-by=cpu` / `--sort-by=memory` are the two flags exam tasks are built
on: "find the node/Pod consuming the most X and write its name to a file".

```bash
kubectl top pods -A --sort-by=memory --no-headers | head -1 | awk '{print $2}' > /opt/top-pod.txt
```

## What `top` is not telling you

- It is **usage**, not requests or limits. A Pod at 80 % of its limit and a
  Pod with no limit look the same. `kubectl describe node` shows the
  *requested* side - how full the node is from the scheduler's point of view:

```bash
kubectl describe node node01 | grep -A8 "Allocated resources"
#   Resource           Requests      Limits
#   cpu                1150m (57%)   2 (100%)
#   memory             1.2Gi (31%)   2Gi (52%)
```

- It is **now**. A Pod that was OOMKilled a minute ago may show tiny usage
  now. For "what happened" you read `describe` (Last State, restart count)
  and events.

## The rest of the observability toolbox

| Question | Tool |
|---|---|
| why is this Pod not Running | `kubectl describe pod` - Events section |
| what happened recently in this namespace | `kubectl get events --sort-by=.lastTimestamp` |
| what did the application say | `kubectl logs` (next lesson) |
| is the control plane healthy | `kubectl get --raw /readyz?verbose`, `kubectl get cs` (deprecated but still answers) |
| is a node healthy | `kubectl describe node` - Conditions: MemoryPressure, DiskPressure, PIDPressure, Ready |

:::tip
`kubectl get events -A --sort-by=.lastTimestamp | tail -20` is the best
single command when "something is wrong and I do not know where". Warnings
from the scheduler, the kubelet, image pulls and probes all land there.
:::

## Check yourself

1. Which component collects container metrics on the node, and which one makes
   them available to `kubectl top`?
2. `kubectl top pods` says the Metrics API is not available. What do you check?
3. What is the difference between what `kubectl top node` shows and what
   `kubectl describe node` shows under Allocated resources?
