## Mock exam 3

Two hours. Ten tasks. Total weight 100. The hardest of the three: two
troubleshooting tasks with a broken control plane and a broken kubeconfig,
RBAC at cluster scope, NetworkPolicy, taints, security contexts. Read
each task twice before typing.

```bash
alias k=kubectl; export do="--dry-run=client -o yaml"
```

---

**1.** (12) Create a ServiceAccount `pvviewer`, a ClusterRole
`pvviewer-role` allowing `list` on `persistentvolumes`, and a
ClusterRoleBinding `pvviewer-role-binding` granting it to the
ServiceAccount. Then create a Pod `pvviewer` (image `redis`) that uses the
ServiceAccount.

**2.** (6) List the `InternalIP` of all nodes using JSONPath, one line,
space-separated, and save it to `/root/CKA/node_ips`.

**3.** (10) Create a Pod `multi-pod` with two containers: `alpha` (image
`nginx`) with env `name=alpha`, and `beta` (image `busybox`, command
`sleep 4800`) with env `name=beta`.

**4.** (8) Create a Pod `non-root-pod` using image `redis:alpine` with
`runAsUser: 1000` and `fsGroup: 2000`.

**5.** (12) A Pod `np-test-1` (label `run=np-test-1`, image `nginx`) and a
Service `np-test-service` exist in `default` (create them). A
default-deny-ingress NetworkPolicy is also applied (create it). Create a
NetworkPolicy `ingress-to-nptest` that allows **incoming** traffic on port
`80` to `np-test-1` from any Pod. Verify with a `busybox:1.28` Pod and
`nc -z -v -w 2 np-test-service 80`.

**6.** (10) Taint the worker `node01` with `env_type=production:NoSchedule`.
Create a Pod `dev-redis` (image `redis:alpine`) and confirm it is **not**
scheduled on `node01`. Create a Pod `prod-redis` (image `redis:alpine`)
that tolerates the taint and confirm it **is** scheduled on `node01`.

**7.** (6) Create a Pod `hr-pod` in namespace `hr` with labels
`environment=production` and `tier=frontend`, image `redis:alpine`.

**8.** (12) A kubeconfig file `/root/CKA/super.kubeconfig` has been
created but does not work. Find the problem and fix it. (Before the mock:
`cp ~/.kube/config /root/CKA/super.kubeconfig` and change the server port
to `9999`.)

**9.** (14) A Deployment `nginx-deploy` (create it: image `nginx`, 1
replica) has been scaled to `3` but the new Pods never appear. Find and
fix the cause. (Before the mock, on the control-plane node: `sed -i
's/kube-controller-manager/kube-contro1ler-manager/' /etc/kubernetes/manifests/kube-controller-manager.yaml`
- note the digit 1 - then `k scale deploy nginx-deploy --replicas=3`.)

**10.** (10) Create a HorizontalPodAutoscaler `web-hpa` for a Deployment
`web` (create: `nginx`, 1 replica, requests cpu `100m`): min `2`, max `5`,
target CPU `50%`. Confirm the Deployment scales to the minimum.
(Requires metrics-server; if absent, the HPA shows `<unknown>` - the
object is still gradable.)

---

Score, then solutions.

:::exam-tip
Task 9 is the shape of the exam's hardest troubleshooting question: the
symptom is in a workload (Pods not appearing), the cause is in the control
plane (a component that is not running), and the fix is in a file. The
path from symptom to file is `get deploy` → `get rs` (created, but no
Pods?) → "who creates Pods from ReplicaSets" → `get pods -n kube-system`
→ the manifest. Three minutes if you walk it; thirty if you guess.
:::

## Check yourself

1. In task 9, what was the first observation that pointed away from the
   Deployment and toward the control plane?
2. In task 5, which Pod did the policy select, and what did `policyTypes`
   contain?
3. In task 8, what command told you what was wrong with the kubeconfig
   before you opened the file?
