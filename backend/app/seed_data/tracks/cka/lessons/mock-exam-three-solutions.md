## Mock exam 3 - solutions

### 1. ServiceAccount + ClusterRole + binding + Pod

```bash
k create sa pvviewer
k create clusterrole pvviewer-role --verb=list --resource=persistentvolumes
k create clusterrolebinding pvviewer-role-binding --clusterrole=pvviewer-role --serviceaccount=default:pvviewer
k run pvviewer --image=redis $do > p.yaml      # add  serviceAccountName: pvviewer  under spec
k apply -f p.yaml
k auth can-i list pv --as system:serviceaccount:default:pvviewer     # yes
k get pod pvviewer -o jsonpath='{.spec.serviceAccountName}'
```

Traps: `--serviceaccount=<namespace>:<name>`; `persistentvolumes` is
cluster-scoped so it needs a **Cluster**Role and **Cluster**RoleBinding;
the `--as` form for a ServiceAccount is `system:serviceaccount:<ns>:<name>`.

### 2. InternalIPs

```bash
k get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}' > /root/CKA/node_ips
cat /root/CKA/node_ips
```

Trap: quoting - single quotes outside, double inside the filter. If it
prints nothing, `k get node <n> -o json | grep -B3 InternalIP` to confirm
the path.

### 3. Multi-container Pod with env

```bash
k run multi-pod --image=nginx $do > p.yaml
```

```yaml
spec:
  containers:
  - name: alpha
    image: nginx
    env:
    - name: name
      value: alpha
  - name: beta
    image: busybox
    command: ["sleep", "4800"]
    env:
    - name: name
      value: beta
```

```bash
k apply -f p.yaml; k get pod multi-pod      # 2/2
k exec multi-pod -c beta -- env | grep name
```

Trap: rename the generated container from `multi-pod` to `alpha`; the
`busybox` container needs a command or it exits immediately.

### 4. Security context

```yaml
spec:
  securityContext:
    runAsUser: 1000
    fsGroup: 2000
  containers:
  - name: non-root-pod
    image: redis:alpine
```

`fsGroup` is Pod-level only; `runAsUser` can be either, Pod-level covers
all containers. Verify: `k exec non-root-pod -- id` → `uid=1000 gid=0
groups=2000`.

### 5. NetworkPolicy allowing ingress on 80

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ingress-to-nptest
spec:
  podSelector:
    matchLabels:
      run: np-test-1
  policyTypes: [Ingress]
  ingress:
  - ports:
    - protocol: TCP
      port: 80
```

```bash
k apply -f np.yaml
k run test-np --image=busybox:1.28 --rm -it --restart=Never -- nc -z -v -w 2 np-test-service 80
# np-test-service (10.96.x.x:80) open
```

Traps: a rule with `ports` and no `from` allows from **everywhere** on
that port - which is what "from any Pod" means; `policyTypes: [Ingress]`
only, so egress is untouched; the selector is the **target** Pod's label.

### 6. Taint and toleration

```bash
k taint node node01 env_type=production:NoSchedule
k run dev-redis --image=redis:alpine
k get pod dev-redis -o wide                 # on a node other than node01 (or Pending on a 1-worker cluster)
k run prod-redis --image=redis:alpine $do > p.yaml
```

```yaml
  tolerations:
  - key: env_type
    operator: Equal
    value: production
    effect: NoSchedule
```

```bash
k apply -f p.yaml; k get pod prod-redis -o wide     # node01
```

Trap: a toleration **allows**, it does not **force** - on a multi-worker
cluster prod-redis may land elsewhere; if the task demands node01, add
`nodeName: node01` or a nodeSelector as well. Untaint afterwards with the
trailing `-`.

### 7. Pod with labels in a namespace

```bash
k create ns hr
k run hr-pod --image=redis:alpine -n hr -l environment=production,tier=frontend
k get pod hr-pod -n hr --show-labels
```

### 8. Broken kubeconfig

```bash
k get nodes --kubeconfig /root/CKA/super.kubeconfig
# The connection to the server controlplane:9999 was refused
k cluster-info                              # the working one says :6443
vi /root/CKA/super.kubeconfig               # server: https://controlplane:6443
k get nodes --kubeconfig /root/CKA/super.kubeconfig    # works
```

Trap: the error message already says the port; compare with the working
kubeconfig (`k config view`) rather than reading the file cold. Other
variants of this task: a wrong cluster name in the context, a wrong
`certificate-authority` path.

### 9. Deployment will not scale

```bash
k get deploy nginx-deploy          # READY 1/3
k get rs                           # DESIRED 3, CURRENT 1 - the ReplicaSet exists but is not making Pods
k get pods -n kube-system          # kube-controller-manager-controlplane  CrashLoopBackOff / ErrImagePull
k describe pod kube-controller-manager-controlplane -n kube-system | tail -5
# Failed to pull image ".../kube-contro1ler-manager:v1.31.0"   or  exec: "kube-contro1ler-manager": not found
vi /etc/kubernetes/manifests/kube-controller-manager.yaml     # fix the command (and/or image) spelling
k get pods -n kube-system -w       # controller manager Running
k get deploy nginx-deploy          # 3/3
```

Trap: the ReplicaSet is there (the Deployment controller... is also in
the controller manager - in this variant the RS existed before the break).
The tell is "a controller is not doing its job" → controller manager.
Check both the `command:` line and the `image:` line; the typo can be in
either.

### 10. HPA

```bash
k autoscale deploy web --name=web-hpa --min=2 --max=5 --cpu-percent=50
k get hpa web-hpa                  # TARGETS 0%/50% (or <unknown> without metrics-server)  MINPODS 2  MAXPODS 5  REPLICAS 2
k get deploy web                   # 2/2 after a minute
```

Trap: the Deployment's containers need CPU **requests** or the HPA cannot
compute a percentage; without metrics-server the HPA still scales to
`min` but shows `<unknown>`.

## Scoring

| Tasks | Domain |
|---|---|
| 1, 4, 5 | Security: RBAC, securityContext, NetworkPolicy |
| 2 | JSONPath |
| 3, 7, 10 | Workloads |
| 6 | Scheduling |
| 8, 9 | Troubleshooting: kubeconfig, control plane |

Add the three mocks' scores. If every mock is comfortably above 66% **with
time to spare**, you are ready. If you pass only by using every minute,
the speed-drills lesson is the difference. If a domain fails across all
three mocks, the weak-domain-review lesson is the plan.

:::exam-tip
Across 33 tasks in three mocks, notice what never appeared: writing a
Helm chart, a CNI from scratch, an operator, anything you would need more
than the docs and twenty minutes for. The exam tests administration, not
engineering. Breadth, precision and speed - in that order.
:::

## Check yourself

1. Why does task 1 need a ClusterRole rather than a Role?
2. A NetworkPolicy ingress rule lists `ports` but no `from`. Who is
   allowed?
3. In task 9, what observation distinguishes "the controller manager is
   broken" from "the scheduler is broken"?
