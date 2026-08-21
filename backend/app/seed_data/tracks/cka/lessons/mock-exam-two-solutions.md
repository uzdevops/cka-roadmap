## Mock exam 2 - solutions

### 1. etcd snapshot

```bash
cat /etc/kubernetes/manifests/etcd.yaml | grep -E "cert-file|key-file|trusted-ca-file|listen-client"
ETCDCTL_API=3 etcdctl snapshot save /opt/etcd-backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
ETCDCTL_API=3 etcdctl snapshot status /opt/etcd-backup.db -w table   # or: etcdutl snapshot status
```

Traps: the three cert flags are mandatory and their values come from the
manifest; `etcdctl` must run on the control-plane node (ssh if needed);
without `ETCDCTL_API=3` on old binaries the command does not exist. Verify
the file exists and has size.

### 2. emptyDir volume

```bash
k run redis-storage --image=redis:alpine $do > p.yaml
```

```yaml
spec:
  containers:
  - name: redis-storage
    image: redis:alpine
    volumeMounts:
    - name: redis-storage
      mountPath: /data/redis
  volumes:
  - name: redis-storage
    emptyDir: {}
```

```bash
k apply -f p.yaml; k describe pod redis-storage | grep -A3 Mounts
```

### 3. capability

```bash
k run super-user-pod --image=busybox:1.28 $do --command -- sleep 4800 > p.yaml
```

```yaml
    securityContext:
      capabilities:
        add: ["SYS_TIME"]
```

(Under the **container**, not the Pod - `capabilities` is container-level
only.) `k apply -f p.yaml; k get pod super-user-pod`.

### 4. Pod using a PVC

```yaml
# pv + pvc setup, then:
apiVersion: v1
kind: Pod
metadata:
  name: use-pv
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: my-pvc
```

```bash
k get pvc my-pvc      # Bound  (check before the Pod: a Pending PVC means a Pending Pod)
k get pod use-pv
```

### 5. Deployment and rolling upgrade with a change cause

```bash
k create deploy nginx-deploy --image=nginx:1.16 --replicas=1
k set image deploy nginx-deploy nginx=nginx:1.17
k annotate deploy nginx-deploy kubernetes.io/change-cause="nginx 1.17"
k rollout history deploy nginx-deploy      # REVISION 2  CHANGE-CAUSE nginx 1.17
k rollout status deploy nginx-deploy
```

Trap: `--record` is deprecated/removed; the annotation
`kubernetes.io/change-cause` is what `rollout history` displays. The
container name in `set image` is `nginx` (from the image name, as `create
deploy` names it).

### 6. User john via CSR + RBAC

```bash
openssl genrsa -out john.key 2048
openssl req -new -key john.key -subj "/CN=john" -out john.csr
cat john.csr | base64 | tr -d "\n"
```

```yaml
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: john-developer
spec:
  request: <base64 csr>
  signerName: kubernetes.io/kube-apiserver-client
  usages: [client auth]
```

```bash
k apply -f csr.yaml; k get csr; k certificate approve john-developer
k create role developer -n development --verb=create,list,get,update,delete --resource=pods
k create rolebinding john-developer -n development --role=developer --user=john
k auth can-i create pods -n development --as john       # yes
k auth can-i create pods -n default --as john           # no
```

Traps: `signerName` exactly `kubernetes.io/kube-apiserver-client` and
`usages: [client auth]` (the docs page has it); the CSR base64 must be one
line; verbs are a comma list in `create role`.

### 7. DNS lookups to files

```bash
k run nginx-resolver --image=nginx
k expose pod nginx-resolver --name=nginx-resolver-service --port=80
k get pod nginx-resolver -o wide         # note the IP, e.g. 10.244.1.8
k run test-nslookup --image=busybox:1.28 --rm -it --restart=Never -- nslookup nginx-resolver-service > /root/CKA/nginx.svc
k run test-nslookup --image=busybox:1.28 --rm -it --restart=Never -- nslookup 10-244-1-8.default.pod.cluster.local > /root/CKA/nginx.pod
cat /root/CKA/nginx.svc /root/CKA/nginx.pod
```

Traps: Pod DNS names are the IP with **dashes**, `<ip-dashed>.<ns>.pod`;
`busybox:1.28` specifically (later tags have a broken nslookup); `--rm -it
--restart=Never` for a throwaway Pod. `mkdir -p /root/CKA` if missing.

### 8. Static Pod on a worker

```bash
ssh node01
k run nginx-critical --image=nginx $do > /etc/kubernetes/manifests/nginx-critical.yaml   # if kubectl works on the node; else write it by hand or scp it
exit
k get pod nginx-critical-node01          # Running; delete it and it comes back
```

Traps: the file goes on **node01**, in that node's `staticPodPath`
(`grep staticPodPath /var/lib/kubelet/config.yaml`); kubectl on a worker
may have no kubeconfig - generate the YAML on the control plane and `scp`
it, or write it in vi. "Recreated if deleted" is what static Pods do by
definition; prove it with `k delete pod nginx-critical-node01` and watch it
return.

### 9. One per node, including control plane → DaemonSet

```bash
k get deploy api -n backend -o yaml > ds.yaml
vi ds.yaml   # kind: DaemonSet; remove replicas, strategy, progressDeadlineSeconds, status; add the toleration
```

```yaml
    spec:
      tolerations:
      - key: node-role.kubernetes.io/control-plane
        operator: Exists
        effect: NoSchedule
```

```bash
k delete deploy api -n backend
k apply -f ds.yaml
k get ds,pods -n backend -o wide     # DESIRED = number of nodes, one Pod per node
```

Trap: the control-plane taint - without the toleration the DaemonSet
skips that node. `kubectl create ds` does not exist; convert a Deployment
or copy the docs' DaemonSet example.

### 10. ConfigMap as env

```bash
k create cm app-config --from-literal=LOG_LEVEL=debug --from-literal=MODE=test
k run cm-pod --image=busybox:1.28 $do --command -- sh -c "env; sleep 3600" > p.yaml
```

```yaml
    envFrom:
    - configMapRef:
        name: app-config
```

```bash
k apply -f p.yaml; k logs cm-pod | grep -E "LOG_LEVEL|MODE"
```

Trap: "all keys" = `envFrom`, not a list of `env` entries with
`valueFrom` (that is for one key).

## Scoring

| Tasks | Domain |
|---|---|
| 1, 8 | Cluster Architecture (etcd, static Pods) |
| 2, 4 | Storage |
| 3, 6 | Security / RBAC |
| 5, 9, 10 | Workloads |
| 7 | Services & Networking - DNS |

:::exam-tip
Three of these (1, 6, 7) are **copy-from-docs** tasks: the exact flags or
the exact YAML are on one page each. Your job in the exam is not to recall
them, it is to **find the page in 20 seconds** and adapt it. If that is
where your time went, spend an hour navigating kubernetes.io with the
search box and you will get it back threefold.
:::

## Check yourself

1. Where do the three certificate paths for the etcd snapshot come from?
2. Why must the toleration be added when converting to a DaemonSet, and
   what happens without it?
3. What is the DNS name of a Pod with IP 10.244.1.8 in namespace `default`?
