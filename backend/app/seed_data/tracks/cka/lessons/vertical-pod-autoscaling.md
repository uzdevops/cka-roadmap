## Right-sizing instead of more copies

The HPA answers "how many"; the **Vertical Pod Autoscaler** answers "how
big". It watches the actual CPU and memory usage of a workload's Pods,
computes a recommendation for their requests (and, proportionally, limits),
and - depending on its mode - applies it.

The VPA is **not built in**. It is a separate project you install from the
`kubernetes/autoscaler` repository:

```bash
git clone https://github.com/kubernetes/autoscaler.git
cd autoscaler/vertical-pod-autoscaler
./hack/vpa-up.sh
kubectl get pods -n kube-system | grep vpa
# vpa-admission-controller-...
# vpa-recommender-...
# vpa-updater-...
kubectl get crd | grep verticalpodautoscaler
```

## The three components

| Component | Does |
|---|---|
| **Recommender** | watches metrics (needs Metrics Server), computes target/lower/upper bounds per container |
| **Updater** | in `Auto`/`Recreate` mode, **evicts** Pods whose requests are too far from the recommendation so they are recreated with new values |
| **Admission controller** | a mutating webhook that writes the recommended requests into Pods *as they are created* |

Note the mechanism: classic VPA changes a Pod's resources by **evicting it**
and letting the controller recreate it, with the admission webhook injecting
the new numbers on the way in. That is why it is disruptive, and why the
newer `InPlaceOrRecreate` mode (using in-place resize when possible) exists.

## The object

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: hamster
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: hamster
  updatePolicy:
    updateMode: "Off"            # Off | Initial | Recreate | Auto | InPlaceOrRecreate
  resourcePolicy:
    containerPolicies:
      - containerName: "*"
        minAllowed: {cpu: 100m, memory: 50Mi}
        maxAllowed: {cpu: "2",  memory: 2Gi}
        controlledResources: ["cpu", "memory"]
```

| updateMode | Behaviour |
|---|---|
| `Off` | only recommends - read them, apply by hand. The safe way to start. |
| `Initial` | applies recommendations to **new** Pods only; never evicts |
| `Recreate` | evicts Pods to apply changes |
| `Auto` | currently the same as Recreate; will prefer in-place when available |
| `InPlaceOrRecreate` | tries in-place resize first, evicts only if it cannot |

```bash
kubectl describe vpa hamster
#   Recommendation:
#     Container Recommendations:
#       Container Name:  hamster
#       Lower Bound:   Cpu: 100m  Memory: 262144k
#       Target:        Cpu: 587m  Memory: 262144k
#       Upper Bound:   Cpu: 1     Memory: 500Mi
kubectl get pods -l app=hamster -o jsonpath='{.items[*].spec.containers[0].resources.requests}'
```

## HPA and VPA together

Both writing to the same Deployment on the same metric makes a mess: the HPA
adds replicas because CPU is high, the VPA raises the request so the
percentage drops, the HPA removes replicas, and so on. Working combinations:

- HPA on CPU, VPA on **memory only** (`controlledResources: ["memory"]`);
- HPA on a custom/external metric (requests per second), VPA on CPU and
  memory;
- VPA in `Off` mode purely as a recommendation dashboard, HPA doing the
  scaling.

:::exam-tip
Expect questions of the form "install the VPA / create a VPA for Deployment X
in recommendation-only mode / read the target recommendation". The CRD's
`apiVersion` is `autoscaling.k8s.io/v1` - not `autoscaling/v2`, which is the
HPA - and the mode that never touches Pods is `"Off"` (quoted, it is a
string).
:::

## When to use which

- Stateless, horizontally scalable, load-driven → HPA.
- Single replica, or a StatefulSet, or a Job, where the question is "how
  much should this ask for" → VPA.
- You simply do not know the right requests → VPA in `Off` mode for a week,
  then set them from the recommendation and move on.

## Check yourself

1. Name the three VPA components and what each does.
2. In `Recreate` mode, how does the VPA change a running Pod's requests, and
   why is that disruptive?
3. Which `updateMode` would you choose to get recommendations without the
   VPA ever touching a Pod?
