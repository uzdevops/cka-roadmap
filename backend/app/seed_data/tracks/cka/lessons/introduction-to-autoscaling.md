## Two axes, two levels

"Autoscaling" in Kubernetes means four different things, and every
conversation about it goes wrong until the four are separated.

```
                 │  scale OUT/IN (more copies)        │  scale UP/DOWN (bigger copies)
─────────────────┼────────────────────────────────────┼────────────────────────────────
 workload (Pods) │  Horizontal Pod Autoscaler (HPA)   │  Vertical Pod Autoscaler (VPA)
 cluster (nodes) │  Cluster Autoscaler / Karpenter    │  (change the instance type)
```

- **Horizontal** - add or remove replicas. The application must tolerate
  running as many copies (stateless, or stateful with care).
- **Vertical** - give the same replica more or less CPU and memory. No
  change to the application, but the Pod has to be restarted - unless the
  cluster supports in-place resize.
- **Workload level** - Kubernetes objects adjust Kubernetes objects.
- **Cluster level** - a controller talks to the cloud to add or remove nodes
  when Pods cannot be scheduled (or nodes sit empty). Out of CKA scope beyond
  knowing it exists.

## Manual scaling, the baseline

Everything automatic is a controller doing what you could do by hand:

```bash
kubectl scale deployment web --replicas=5                         # horizontal, by hand
kubectl set resources deployment web --requests=cpu=500m,memory=512Mi   # vertical, by hand (rolls the Pods)
```

The HPA writes `spec.replicas` for you; the VPA writes the resource requests
for you. If you understand those two commands you understand what the
controllers are allowed to touch.

## What they need to work

| Autoscaler | Needs |
|---|---|
| HPA | the **Metrics Server** (or a custom/external metrics adapter) and **resource requests** on the Pods - a percentage target is "percent of request" |
| VPA | the VPA components installed (it is not built in) and, for Auto mode, tolerance for Pod restarts |
| Cluster Autoscaler | a cloud provider and node groups it may resize |

:::exam-tip
The HPA is the one the exam tests directly - `kubectl autoscale` and the
`autoscaling/v2` manifest - and its two prerequisites are where the trouble
hides: an HPA showing `<unknown>/50%` means no metrics (Metrics Server
missing or Pods without CPU requests). The VPA and in-place resize are newer
curriculum items; know the concepts and the objects.
:::

## Choosing

- Traffic-driven, stateless, many small replicas cheaper than one big one
  → **HPA**.
- A single-replica service whose right size you do not know, or a batch
  workload that is over- or under-provisioned → **VPA**, or at least VPA in
  recommendation-only mode.
- Both on the same Deployment for the same metric (CPU) → **no**: they fight.
  HPA on CPU plus VPA on memory, or VPA in `Off` mode just to get
  recommendations, are the combinations that work.
- Pods Pending for lack of room → **Cluster Autoscaler**; the HPA can only
  ask for replicas, it cannot make nodes.

## The week ahead

1. A lab scaling by hand, to feel what the controllers automate.
2. The HPA: the object, the algorithm, `kubectl autoscale`, watching it
   react to load.
3. In-place Pod resize: changing a container's resources without a restart.
4. The VPA: components, update modes, and when to prefer it.

## Check yourself

1. Put each of these in the right box of the grid: HPA, VPA, Cluster
   Autoscaler.
2. An HPA shows `<unknown>` as the current CPU. Name the two usual causes.
3. Why should an HPA and a VPA not both act on the CPU of the same
   Deployment?
