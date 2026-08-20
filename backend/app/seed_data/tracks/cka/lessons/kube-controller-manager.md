## The reconciliation engine

Kubernetes is declarative: you write down the state you want, and *something*
keeps making reality match it. That something is a **controller** - a loop
that watches one kind of object through the API server, compares desired to
actual, and acts on the difference. Scale a Deployment to 5, a controller
creates two Pods. A node vanishes, a controller marks it and reschedules what
was on it.

There are dozens of these loops. The **kube-controller-manager** is the single
process that runs all of the built-in ones:

| Controller | Watches | Makes sure that |
|---|---|---|
| Node | Nodes and their heartbeats | a silent node becomes `NotReady`, then its Pods are evicted |
| Replication / ReplicaSet | ReplicaSets | the right number of Pods exist |
| Deployment | Deployments | ReplicaSets are created and rolled in the right order |
| Endpoints / EndpointSlice | Services and Pods | a Service's endpoint list matches its selector |
| ServiceAccount and Token | namespaces, SAs | every namespace has a default SA |
| Namespace | Namespaces | deleting a namespace deletes its contents |
| Job, CronJob, DaemonSet, StatefulSet | their kinds | each does what its name says |
| PersistentVolume binder | PVCs and PVs | claims find volumes |
| Garbage collector | owner references | orphaned children are removed |

One binary, many loops, so that each one does not need its own deployment,
leader election and credentials.

## How it runs

Another static Pod on kubeadm clusters:

```bash
cat /etc/kubernetes/manifests/kube-controller-manager.yaml
kubectl get pods -n kube-system | grep controller-manager
```

```yaml
- kube-controller-manager
- --kubeconfig=/etc/kubernetes/controller-manager.conf   # how it talks to the API server
- --cluster-signing-cert-file=/etc/kubernetes/pki/ca.crt
- --cluster-signing-key-file=/etc/kubernetes/pki/ca.key  # it is the CSR signer
- --root-ca-file=/etc/kubernetes/pki/ca.crt
- --service-account-private-key-file=/etc/kubernetes/pki/sa.key
- --controllers=*,bootstrapsigner,tokencleaner
- --leader-elect=true
- --node-monitor-period=5s
- --node-monitor-grace-period=40s
- --use-service-account-credentials=true
```

Two of those are worth a second look.

- `--cluster-signing-cert-file` / `-key-file`: when you approve a
  CertificateSigningRequest (certificates lesson), it is **this** component
  that signs it with the cluster CA. If CSRs sit approved but never issued,
  look here.
- `--node-monitor-grace-period`: how long a node may go quiet before it is
  `NotReady`. Together with the kubelet's heartbeat interval it decides how
  fast the cluster reacts to a dead node.

:::exam-tip
The controller manager and the scheduler both run with `--leader-elect=true`:
on a multi-control-plane cluster all replicas run, but only the leader acts.
Losing the leader costs a few seconds of election, not correctness.
:::

## What it looks like when it is broken

Nothing *immediately* stops working when the controller manager dies, which is
what makes it sneaky. The API server answers, kubectl is fine, existing Pods
keep running - but:

- `kubectl scale deployment web --replicas=5` changes the number and **no Pods
  appear**;
- a deleted Pod of a ReplicaSet is **not replaced**;
- new CSRs stay approved but never get a certificate;
- a new namespace has **no default ServiceAccount**, so Pods in it fail to
  create.

```bash
kubectl get pods -n kube-system | grep controller-manager   # CrashLoopBackOff?
kubectl logs -n kube-system kube-controller-manager-controlplane | tail
kubectl describe pod -n kube-system kube-controller-manager-controlplane | tail -20
```

Typical exam faults: a misspelt image or command in the manifest, a wrong
`--kubeconfig` path, a certificate path under `/etc/kubernetes/pki` that does
not exist, or a `hostPath` volume mounted from the wrong directory.

:::tip
"Scaling does nothing" is the controller manager. "Pods stay Pending" is the
scheduler. "kubectl hangs" is the API server. Three symptoms, three components
- memorise the mapping.
:::

## Check yourself

1. You scale a Deployment and the number updates but no Pods appear. Which
   component do you suspect, and what is the first command?
2. Which component actually signs an approved CertificateSigningRequest?
3. Why can the controller manager be down for a minute without any running
   application noticing?
