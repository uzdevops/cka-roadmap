## The request side

A PersistentVolumeClaim is a user's request for storage, in a namespace:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: myclaim
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Mi
  storageClassName: manual          # must equal the PV's, or both omitted
  # selector:                       # optional: only PVs with these labels
  #   matchLabels: {type: ssd}
```

```bash
kubectl apply -f pvc.yaml
kubectl get pvc
# NAME      STATUS   VOLUME    CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# myclaim   Bound    pv-vol1   1Gi        RWO            manual         3s
```

## How binding works

The PV controller looks for an `Available` PV that satisfies the claim:

| The claim wants | The PV must |
|---|---|
| `storage: 500Mi` | have capacity ≥ 500Mi (the claim gets the **whole** PV - 1Gi here, shown as CAPACITY) |
| access mode RWO | list that mode |
| `storageClassName: manual` | have the same class name (empty matches empty only) |
| a selector | carry matching labels |

The smallest adequate PV is preferred, but it is still one-to-one: a 100Gi PV
bound to a 1Gi claim is **used up**. If nothing fits, the claim stays
`Pending` and `kubectl describe pvc` explains - or, with a dynamic
StorageClass, a PV is created to fit (next lesson).

```bash
kubectl describe pvc myclaim | tail -5
#  Warning  ProvisioningFailed / no persistent volumes available for this claim and no storage class is set
```

:::exam-tip
A Pending claim on a cluster with a hand-made PV is almost always one of:
access mode mismatch, `storageClassName` mismatch (one side says `manual`,
the other says nothing), or the PV is already `Bound`/`Released`. `kubectl
get pv` and `kubectl describe pvc` side by side shows which.
:::

## Using the claim in a Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: webapp
spec:
  containers:
    - name: webapp
      image: webapp
      volumeMounts:
        - name: log
          mountPath: /log
  volumes:
    - name: log
      persistentVolumeClaim:
        claimName: myclaim
```

The Pod names the **claim**, never the PV. That is the point: the Pod spec is
the same on every cluster; the claim finds whatever storage that cluster
has.

A claim that is `Pending` makes the Pod stay `Pending` too, with
`ContainerCreating` or an event about unbound claims - look at the claim, not
the Pod.

## Deleting

```bash
kubectl delete pvc myclaim
# (hangs if a Pod is still using it - finalizer kubernetes.io/pvc-protection)
kubectl get pv pv-vol1         # STATUS Released (Retain) or gone (Delete)
```

Two protections to know:

- **pvc-protection**: a claim in use by a Pod is not deleted until the Pod
  is gone - `kubectl delete pvc` just waits (`Terminating`). Delete the Pod
  first, or that is the explanation for "delete hangs".
- **pv-protection**: likewise a bound PV waits for its claim.

## Expanding

If the StorageClass allows it (`allowVolumeExpansion: true`), edit the claim's
`resources.requests.storage` upward and the volume grows (filesystem resize
happens on the next mount or online, depending on the driver). Shrinking is
not supported.

```bash
kubectl patch pvc myclaim -p '{"spec":{"resources":{"requests":{"storage":"2Gi"}}}}'
kubectl describe pvc myclaim | grep -i condition -A3
```

## The usual sequence, end to end

```bash
kubectl apply -f pv.yaml && kubectl get pv             # Available
kubectl apply -f pvc.yaml && kubectl get pvc           # Bound, VOLUME = the PV
kubectl apply -f pod.yaml && kubectl get pod           # Running
kubectl exec webapp -- sh -c 'echo hi > /log/test && cat /log/test'
kubectl delete pod webapp && kubectl apply -f pod.yaml
kubectl exec webapp -- cat /log/test                   # still there - that is persistence
```

## Check yourself

1. A 1Gi claim binds to a 5Gi PV. How much can the Pod use, and can another
   claim share the rest?
2. A Pod references a PVC; the PVC is Pending. What state is the Pod in, and
   where do you look?
3. `kubectl delete pvc` sits at Terminating. Why, and what do you do?
