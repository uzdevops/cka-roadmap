## One copy on every node

Some things must run on every node, no more and no less: the CNI plugin,
kube-proxy, a log shipper, a node-exporter for metrics, a storage driver. A
Deployment cannot promise that - it promises a *count*. A **DaemonSet**
promises *one Pod per node*, and adds one automatically when a node joins.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
      containers:
        - name: fluentd
          image: fluentd:v1.16
```

Same shape as a ReplicaSet - selector plus template - with **no `replicas`**:
the node count *is* the replica count.

```bash
kubectl get ds -A
# NAMESPACE     NAME         DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR
# kube-system   kube-proxy   3         3         3       3            3           kubernetes.io/os=linux
# kube-flannel  kube-flannel 3         3         3       3            3           <none>
kubectl describe ds kube-proxy -n kube-system
```

## How it schedules

Since Kubernetes 1.12 DaemonSet Pods go through the **default scheduler**
like everyone else - the DaemonSet controller simply creates one Pod per node
with a required node affinity for `kubernetes.io/hostname=<that node>`. That
means:

- taints apply: a DaemonSet that must run on control plane nodes needs the
  toleration above (kube-proxy and CNI DaemonSets carry it);
- `nodeSelector` and node affinity in the template restrict which nodes get a
  copy ("only Linux nodes", "only nodes with `monitoring=true`");
- resource requests are honoured - a node too full to fit the Pod shows a
  Pending DaemonSet Pod, which is a useful alarm.

## Writing one quickly

There is no `kubectl create daemonset`. Generate a Deployment and fix it:

```bash
kubectl create deployment fluentd --image=fluentd:v1.16 -n kube-system $do > ds.yaml
# in ds.yaml: kind: DaemonSet ; delete the replicas: and strategy: lines
kubectl apply -f ds.yaml
```

:::exam-tip
The three edits - `kind`, remove `replicas`, remove `strategy` - take twenty
seconds. Forgetting `replicas` gives a validation error naming the field, so
even the mistake is cheap.
:::

## Updating

`updateStrategy` is `RollingUpdate` by default (one node at a time,
`maxUnavailable: 1`) or `OnDelete` (new Pods only when you delete the old
ones). `kubectl rollout status ds/fluentd -n kube-system` works as for
Deployments.

## And StatefulSets, for contrast

A **StatefulSet** is the other "not a Deployment" workload: ordered, named
replicas (`db-0`, `db-1`, `db-2`) that each keep their own PersistentVolume
and their own stable DNS name through a headless Service. Databases,
brokers, anything where replica identity matters. It is a storage-phase topic
in detail; the one-line distinction to carry:

| | Deployment | DaemonSet | StatefulSet |
|---|---|---|---|
| how many | `replicas` | one per node | `replicas`, ordered |
| Pod names | random suffix | random suffix | `name-0`, `name-1`, ... |
| storage | shared or none | usually hostPath | one PVC per replica, kept |
| typical use | stateless apps | node agents | databases |

## Check yourself

1. Why does a DaemonSet have no `replicas` field, and what happens when a new
   node joins?
2. Your DaemonSet runs on the workers but not on the control plane node. What
   is missing from the template?
3. Starting from `kubectl create deployment ... $do`, what three edits turn
   the output into a valid DaemonSet?
