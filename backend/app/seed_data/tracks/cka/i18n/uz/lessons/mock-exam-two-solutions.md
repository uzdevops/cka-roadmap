## Mock imtihon 2 - yechimlar

### 1. etcd snapshot’i

```bash
cat /etc/kubernetes/manifests/etcd.yaml | grep -E "cert-file|key-file|trusted-ca-file|listen-client"
ETCDCTL_API=3 etcdctl snapshot save /opt/etcd-backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
ETCDCTL_API=3 etcdctl snapshot status /opt/etcd-backup.db -w table   # yoki: etcdutl snapshot status
```

Tuzoqlar: uchta sertifikat flagi majburiy va ularning qiymatlari
manifestdan olinadi; `etcdctl` control plane node’ida ishlashi kerak
(kerak bo’lsa ssh); eski binarlarda `ETCDCTL_API=3` bo’lmasa, bu buyruq
umuman mavjud emas. Fayl bor va hajmi nolga teng emasligini tekshiring.

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

(**Konteyner** ostida, Pod ostida emas - `capabilities` faqat konteyner
darajasida bo’ladi.) `k apply -f p.yaml; k get pod super-user-pod`.

### 4. PVC ishlatadigan Pod

```yaml
# pv + pvc tayyorlanadi, keyin:
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
k get pvc my-pvc      # Bound  (Pod'dan oldin tekshiring: Pending PVC - Pending Pod degani)
k get pod use-pv
```

### 5. Deployment va change cause bilan rolling upgrade

```bash
k create deploy nginx-deploy --image=nginx:1.16 --replicas=1
k set image deploy nginx-deploy nginx=nginx:1.17
k annotate deploy nginx-deploy kubernetes.io/change-cause="nginx 1.17"
k rollout history deploy nginx-deploy      # REVISION 2  CHANGE-CAUSE nginx 1.17
k rollout status deploy nginx-deploy
```

Tuzoq: `--record` eskirgan/olib tashlangan; `rollout history` ko’rsatadigan
narsa - `kubernetes.io/change-cause` annotatsiyasi. `set image`’dagi
konteyner nomi `nginx` (image nomidan, `create
deploy` uni shunday nomlaydi).

### 6. CSR + RBAC orqali john foydalanuvchisi

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

Tuzoqlar: `signerName` aynan `kubernetes.io/kube-apiserver-client` va
`usages: [client auth]` bo’lsin (hujjat sahifasida bor); CSR’ning base64’i
bitta qatorda bo’lishi shart; `create role`’da verb’lar vergul bilan
ajratilgan ro’yxat.

### 7. DNS qidiruvlari fayllarga

```bash
k run nginx-resolver --image=nginx
k expose pod nginx-resolver --name=nginx-resolver-service --port=80
k get pod nginx-resolver -o wide         # IP'ni yozib oling, masalan 10.244.1.8
k run test-nslookup --image=busybox:1.28 --rm -it --restart=Never -- nslookup nginx-resolver-service > /root/CKA/nginx.svc
k run test-nslookup --image=busybox:1.28 --rm -it --restart=Never -- nslookup 10-244-1-8.default.pod.cluster.local > /root/CKA/nginx.pod
cat /root/CKA/nginx.svc /root/CKA/nginx.pod
```

Tuzoqlar: Pod’ning DNS nomi - **chiziqchali** IP, `<ip-dashed>.<ns>.pod`;
aynan `busybox:1.28` (keyingi teglarda nslookup buzilgan); bir martalik Pod
uchun `--rm -it
--restart=Never`. Yo’q bo’lsa `mkdir -p /root/CKA`.

### 8. Worker’da static Pod

```bash
ssh node01
k run nginx-critical --image=nginx $do > /etc/kubernetes/manifests/nginx-critical.yaml   # agar node'da kubectl ishlasa; aks holda qo'lda yozing yoki scp qiling
exit
k get pod nginx-critical-node01          # Running; o'chiring - qaytib keladi
```

Tuzoqlar: fayl **node01**da, o’sha node’ning `staticPodPath`ida turishi
kerak (`grep staticPodPath /var/lib/kubelet/config.yaml`); worker’dagi
kubectl’da kubeconfig bo’lmasligi mumkin - YAML’ni control plane’da
yarating va uni `scp` qiling yoki vi’da yozing. "O’chirilsa qayta
yaratiladi" - static Pod’lar ta’rifi bo’yicha shunday qiladi; buni
`k delete pod nginx-critical-node01` bilan isbotlang va uning qaytishini
kuzating.

### 9. Har bir node’da bittadan, control plane ham → DaemonSet

```bash
k get deploy api -n backend -o yaml > ds.yaml
vi ds.yaml   # kind: DaemonSet; replicas, strategy, progressDeadlineSeconds, status'ni olib tashlang; toleration qo'shing
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
k get ds,pods -n backend -o wide     # DESIRED = node'lar soni, har node'da bitta Pod
```

Tuzoq: control plane taint’i - toleration bo’lmasa, DaemonSet o’sha node’ni
o’tkazib yuboradi. `kubectl create ds` mavjud emas; Deployment’ni
o’tkazing yoki hujjatlardagi DaemonSet misolini ko’chiring.

### 10. ConfigMap muhit o’zgaruvchilari sifatida

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

Tuzoq: "barcha kalitlar" = `envFrom`, `valueFrom` bilan yozilgan `env`
yozuvlari ro’yxati emas (u bitta kalit uchun).

## Baholash

| Vazifalar | Domen |
|---|---|
| 1, 8 | Klaster arxitekturasi (etcd, static Pod’lar) |
| 2, 4 | Saqlash |
| 3, 6 | Xavfsizlik / RBAC |
| 5, 9, 10 | Workload’lar |
| 7 | Service’lar va tarmoq - DNS |

:::exam-tip
Bulardan uchtasi (1, 6, 7) - **hujjatdan ko’chirish** vazifalari: aniq
flaglar yoki aniq YAML har biri uchun bitta sahifada turadi. Imtihonda
sizning ishingiz ularni yoddan eslash emas, **sahifani 20 soniyada topish**
va uni moslashtirish. Vaqtingiz shu yerga ketgan bo’lsa, bir soatni
kubernetes.io’da qidiruv oynasi bilan yurishga sarflang - u uch baravar
bo’lib qaytadi.
:::

## O’zingizni tekshiring

1. etcd snapshot’i uchun uchta sertifikat yo’li qayerdan olinadi?
2. DaemonSet’ga o’tkazayotganda nega toleration qo’shish shart va usiz nima
   bo’ladi?
3. `default` namespace’idagi IP’si 10.244.1.8 bo’lgan Pod’ning DNS nomi
   qanday?
