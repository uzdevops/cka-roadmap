## When kubectl itself misbehaves

Symptoms that point at the control plane rather than at a workload:

- `kubectl` hangs or says `The connection to the server ... was refused` -
  **API server**.
- new Pods stay `Pending` with no Events, nothing ever schedules -
  **scheduler**.
- Deployments do not create ReplicaSets, ReplicaSets do not create Pods,
  nodes never get marked NotReady, Services get no Endpoints -
  **controller manager**.
- everything is slow, writes fail, `etcdserver: request timed out` - **etcd**.

## First look

```bash
kubectl get nodes
kubectl get pods -n kube-system                        # kubeadm clusters: the control plane IS these Pods
# NAME                             READY   STATUS             RESTARTS
# etcd-controlplane                1/1     Running
# kube-apiserver-controlplane      1/1     Running
# kube-controller-manager-...      1/1     Running
# kube-scheduler-controlplane      0/1     CrashLoopBackOff   5     <- there it is
kubectl describe pod kube-scheduler-controlplane -n kube-system | tail -20
kubectl logs kube-scheduler-controlplane -n kube-system [--previous]
```

On a cluster where the components are **systemd services** instead of
static Pods (kubeadm is not the only way):

```bash
systemctl status kube-apiserver kube-controller-manager kube-scheduler etcd
journalctl -u kube-apiserver -f
```

## Static Pods and their manifests

kubeadm's control plane runs as **static Pods**: the kubelet on the
control-plane node reads `/etc/kubernetes/manifests/*.yaml` and runs them
directly. The API server only sees **mirror** Pods for them.

```bash
ls /etc/kubernetes/manifests/
# etcd.yaml  kube-apiserver.yaml  kube-controller-manager.yaml  kube-scheduler.yaml
```

Consequences:

- `kubectl delete pod kube-scheduler-controlplane -n kube-system` does
  nothing lasting - the kubelet recreates it from the file.
- **Editing the file** is the fix; the kubelet notices and restarts the Pod
  within seconds. No `kubectl apply`, no restart command.
- If the API server is down, `kubectl` is useless - use the container
  runtime directly.

```bash
crictl ps -a | grep -E "apiserver|scheduler|controller|etcd"
crictl logs <container-id>
ls /var/log/pods/kube-system_kube-apiserver-*/kube-apiserver/        # the same logs as files
journalctl -u kubelet | grep -i apiserver                             # the kubelet explains why it could not start it
```

## The usual breakages

| Symptom | Where | What it usually is |
|---|---|---|
| scheduler / controller-manager `CrashLoopBackOff`, log: `unknown flag` or `flag provided but not defined` | manifest `command:` | a misspelled or invalid flag |
| `ErrImagePull` for a control-plane Pod | manifest `image:` | a wrong tag (`kube-scheduler:v1.31.0-bad`) |
| controller-manager log: `unable to load client CA file` / `no such file or directory` | manifest `volumes:` hostPath or `--client-ca-file` | a wrong path - compare with the kubelet's or another manifest |
| apiserver not starting, kubectl refused | `/etc/kubernetes/manifests/kube-apiserver.yaml` | wrong `--etcd-servers`, cert path, or a typo; `crictl logs` shows it |
| apiserver log: `connection refused` to 127.0.0.1:2379 | etcd | etcd down or its manifest broken - check it first |
| everything was fine until a cert expired | `/etc/kubernetes/pki` | `kubeadm certs check-expiration`, `kubeadm certs renew all` |
| kube-scheduler Pod not listed at all | manifest file | missing or misnamed - not `.yaml`, or moved out of the directory |
| controller-manager log: `--service-account-private-key-file` or `--cluster-signing-cert-file` error | manifest | a path changed; the files live in `/etc/kubernetes/pki` |

## Reading a manifest for the mistake

```bash
cat /etc/kubernetes/manifests/kube-scheduler.yaml
```

```yaml
spec:
  containers:
  - command:
    - kube-scheduler
    - --authentication-kubeconfig=/etc/kubernetes/scheduler.conf
    - --authorization-kubeconfig=/etc/kubernetes/scheduler.conf
    - --bind-address=127.0.0.1
    - --kubeconfig=/etc/kubernetes/scheduler.conf
    - --leader-elect=true
    image: registry.k8s.io/kube-scheduler:v1.31.0
    livenessProbe: ...
    volumeMounts:
    - mountPath: /etc/kubernetes/scheduler.conf
      name: kubeconfig
      readOnly: true
  volumes:
  - hostPath:
      path: /etc/kubernetes/scheduler.conf
      type: FileOrCreate
    name: kubeconfig
```

Check, in order: the **image** tag exists; every **flag** is spelled right
(`kube-scheduler --help` lists them); every path in flags and in
**volumeMounts/hostPath** exists on the host (`ls` it). Then save; watch
with `watch crictl ps` or `kubectl get pods -n kube-system -w`.

:::warning
A broken `kube-apiserver.yaml` is the one case where you cannot use
`kubectl` to see what is wrong. `crictl ps -a` shows the container exiting;
`crictl logs` (or `/var/log/pods`) shows why; `journalctl -u kubelet` shows
the kubelet failing to create it. Fix the file, and `kubectl` comes back on
its own.
:::

## Logs of the pieces

```bash
kubectl logs -n kube-system kube-apiserver-controlplane
kubectl logs -n kube-system kube-controller-manager-controlplane
kubectl logs -n kube-system kube-scheduler-controlplane
kubectl logs -n kube-system etcd-controlplane
journalctl -u kubelet -n 100 --no-pager                  # the kubelet is not a Pod; it is the thing that runs the Pods
```

:::exam-tip
The exam's control-plane question is almost always a manifest in
`/etc/kubernetes/manifests` with one wrong thing - a flag, a path, an image
tag. `kubectl get pods -n kube-system` finds the broken one; its logs or
`describe` Events name the error; `vi` the manifest; wait. Do not
`kubectl delete` static Pods and do not restart the kubelet unless the
kubelet itself is the problem.
:::

## Check yourself

1. Where does a kubeadm cluster's control plane actually run from, and what
   does that mean for how you fix it?
2. The API server is down and `kubectl` cannot connect. How do you see the
   API server container's logs?
3. Nothing schedules and new Pods have no Events. Which component, and what
   is the first command?
