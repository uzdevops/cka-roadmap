## Mock exam 1 - solutions

For each: the fast path, the verification, the trap.

### 1. nginx-pod

```bash
k run nginx-pod --image=nginx:alpine
k get pod nginx-pod
```

Trap: `nginx:alpine`, not `nginx`. The grader checks the image string.

### 2. messaging with a label

```bash
k run messaging --image=redis:alpine -l tier=msg
k get pod messaging --show-labels
```

Trap: `--labels` works too; `-l` on `run` sets labels (on `get` it filters).

### 3. Namespace

```bash
k create ns apx-x9984574
```

Trap: copy-paste the name; there is no partial credit for a typo.

### 4. nodes as JSON to a file

```bash
k get nodes -o json > /opt/outputs/nodes-z3444kd9.json
cat /opt/outputs/nodes-z3444kd9.json | head
```

Trap: the directory may need `mkdir -p /opt/outputs` first; check the
file is not empty.

### 5. ClusterIP Service for a Pod

```bash
k expose pod messaging --name=messaging-service --port=6379
k get svc messaging-service; k get ep messaging-service      # endpoints non-empty
```

Trap: `expose pod` takes the Pod's labels as the selector automatically -
faster and safer than writing the Service by hand. `--target-port` defaults
to `--port`.

### 6. Deployment

```bash
k create deploy hr-web-app --image=kodekloud/webapp-color --replicas=2
k get deploy hr-web-app
```

### 7. Static Pod

```bash
k run static-busybox --image=busybox $do --command -- sleep 1000 > /etc/kubernetes/manifests/static-busybox.yaml
k get pod static-busybox-controlplane        # appears within seconds, name suffixed with the node
```

Traps: `--command --` before the command, or `sleep 1000` becomes
**args** to the image's entrypoint; the file must be in the **kubelet's
staticPodPath** (`/etc/kubernetes/manifests` on kubeadm - check
`/var/lib/kubelet/config.yaml` if unsure) on the **control-plane node**.
If the task named a worker, `ssh` there first.

### 8. Pod in a namespace

```bash
k create ns finance            # if it does not exist
k run temp-bus --image=redis:alpine -n finance
```

Trap: `-n finance` on the `run`, not just on the `get`.

### 9. The failing orange Pod

```bash
k describe pod orange            # Init:CrashLoopBackOff; init container exit code 127
k logs orange -c init-myservice  # sh: sleeeep: not found
k edit pod orange                # fix 'sleeeep' → 'sleep'; the edit is rejected (init containers immutable) and saved to /tmp/...yaml
k replace --force -f /tmp/kubectl-edit-xxxx.yaml
k get pod orange                 # Running 1/1
```

Trap: only a few Pod fields are editable in place; for anything else,
`edit` → reject → `replace --force` with the temp file it wrote, or `get -o
yaml > f; vi f; replace --force -f f`. Exit code 127 = command not found.

### 10. NodePort Service with a fixed node port

```bash
k expose deploy hr-web-app --name=hr-web-app-service --type=NodePort --port=8080 $do > svc.yaml
vi svc.yaml          # add  nodePort: 30082  under ports[0]
k apply -f svc.yaml
k get svc hr-web-app-service     # 8080:30082/TCP
```

Trap: `expose` has no `--node-port` flag - dry-run to YAML, add it, apply.
`--target-port` is 8080 because the app listens on 8080.

### 11. JSONPath osImage

```bash
k get nodes -o jsonpath='{.items[*].status.nodeInfo.osImage}' > /opt/outputs/nodes_os_x43kj56.txt
cat /opt/outputs/nodes_os_x43kj56.txt
```

Trap: if you do not remember the path, `k get node <n> -o json | grep -i
osImage -B5` shows it under `status.nodeInfo`.

### 12. PersistentVolume

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-analytics
spec:
  capacity:
    storage: 100Mi
  accessModes: [ReadWriteMany]
  hostPath:
    path: /pv/data-analytics
```

```bash
k apply -f pv.yaml; k get pv pv-analytics      # Available
```

Trap: there is no imperative `create pv`; the docs page "Configure a Pod to
Use a PersistentVolume for Storage" has a hostPath PV to copy.

### 13. Rollback a stuck rollout

```bash
k rollout status deploy web-front -n frontend        # stuck: new ReplicaSet's Pods ImagePullBackOff
k rollout history deploy web-front -n frontend
k rollout undo deploy web-front -n frontend
k rollout status deploy web-front -n frontend        # successfully rolled out
k get deploy web-front -n frontend                   # 3/3 AVAILABLE
```

Trap: `undo` goes to the previous revision; `--to-revision=N` for a
specific one. Verify `AVAILABLE`, not just that the command returned.

## Scoring and what it tells you

| Tasks | Domain |
|---|---|
| 1, 2, 3, 6, 8, 10, 13 | Workloads & Scheduling - imperative commands, Services, rollouts |
| 7 | Cluster Architecture - static Pods |
| 9 | Troubleshooting - reading describe/logs, replacing a Pod |
| 4, 11 | Troubleshooting - JSONPath |
| 5, 10 | Services & Networking |
| 12 | Storage |

Anything below full marks in a row: that domain's lessons and labs, this
week.

:::exam-tip
The pattern across all thirteen: **imperative first, YAML only when a
field has no flag** (nodePort, PV, static Pod's command), and **verify with
`get`** after every one. That is the whole speed strategy.
:::

## Check yourself

1. Why does `sleep 1000` need `--command --` in the static Pod command?
2. How do you set a specific nodePort, given that `expose` has no flag for
   it?
3. What does exit code 127 in an init container tell you?
