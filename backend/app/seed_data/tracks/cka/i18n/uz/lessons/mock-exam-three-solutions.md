## Mock imtihon 3 - yechimlar

### 1. ServiceAccount + ClusterRole + binding + Pod

```bash
k create sa pvviewer
k create clusterrole pvviewer-role --verb=list --resource=persistentvolumes
k create clusterrolebinding pvviewer-role-binding --clusterrole=pvviewer-role --serviceaccount=default:pvviewer
k run pvviewer --image=redis $do > p.yaml      # spec ostiga  serviceAccountName: pvviewer  qo'shing
k apply -f p.yaml
k auth can-i list pv --as system:serviceaccount:default:pvviewer     # yes
k get pod pvviewer -o jsonpath='{.spec.serviceAccountName}'
```

Tuzoqlar: `--serviceaccount=<namespace>:<name>`; `persistentvolumes` klaster
darajasidagi resurs, shuning uchun unga **Cluster**Role va
**Cluster**RoleBinding kerak; ServiceAccount uchun `--as` shakli -
`system:serviceaccount:<ns>:<name>`.

### 2. InternalIP’lar

```bash
k get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}' > /root/CKA/node_ips
cat /root/CKA/node_ips
```

Tuzoq: tirnoqlar - tashqarida bitta tirnoq, filtr ichida qo’sh tirnoq. Agar
hech narsa chiqmasa, yo’lni tasdiqlash uchun
`k get node <n> -o json | grep -B3 InternalIP`.

### 3. env bilan ko’p konteynerli Pod

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

Tuzoq: generatsiya qilingan konteyner nomini `multi-pod`’dan `alpha`’ga
o’zgartiring; `busybox` konteyneriga buyruq kerak, aks holda u darhol
tugaydi.

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

`fsGroup` faqat Pod darajasida bo’ladi; `runAsUser` ikkalasida ham bo’lishi
mumkin, Pod darajasidagisi barcha konteynerlarni qamrab oladi. Tekshirish:
`k exec non-root-pod -- id` → `uid=1000 gid=0
groups=2000`.

### 5. 80-portga ingress ruxsat beruvchi NetworkPolicy

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

Tuzoqlar: `ports` bor, `from` yo’q qoida o’sha portga **hamma joydan** ruxsat
beradi - "istalgan Pod’dan" degani shu; faqat `policyTypes: [Ingress]`,
shuning uchun egress tegilmasdan qoladi; selector - **maqsad** Pod’ning
label’i.

### 6. Taint va toleration

```bash
k taint node node01 env_type=production:NoSchedule
k run dev-redis --image=redis:alpine
k get pod dev-redis -o wide                 # node01'dan boshqa node'da (yoki bitta worker'li klasterda Pending)
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

Tuzoq: toleration **ruxsat beradi**, u **majburlamaydi** - ko’p worker’li
klasterda prod-redis boshqa joyga tushishi mumkin; agar vazifa node01’ni
talab qilsa, qo’shimcha `nodeName: node01` yoki nodeSelector qo’shing. Keyin
oxiridagi `-` bilan taint’ni olib tashlang.

### 7. namespace ichida label’li Pod

```bash
k create ns hr
k run hr-pod --image=redis:alpine -n hr -l environment=production,tier=frontend
k get pod hr-pod -n hr --show-labels
```

### 8. Buzilgan kubeconfig

```bash
k get nodes --kubeconfig /root/CKA/super.kubeconfig
# The connection to the server controlplane:9999 was refused
k cluster-info                              # ishlayotgani :6443 deydi
vi /root/CKA/super.kubeconfig               # server: https://controlplane:6443
k get nodes --kubeconfig /root/CKA/super.kubeconfig    # ishlaydi
```

Tuzoq: xato xabarining o’zi portni aytib turibdi; faylni quruq o’qish
o’rniga ishlayotgan kubeconfig bilan solishtiring (`k config view`). Bu
vazifaning boshqa variantlari: kontekstdagi noto’g’ri klaster nomi,
noto’g’ri `certificate-authority` yo’li.

### 9. Deployment masshtablanmaydi

```bash
k get deploy nginx-deploy          # READY 1/3
k get rs                           # DESIRED 3, CURRENT 1 - ReplicaSet bor, lekin Pod yaratmayapti
k get pods -n kube-system          # kube-controller-manager-controlplane  CrashLoopBackOff / ErrImagePull
k describe pod kube-controller-manager-controlplane -n kube-system | tail -5
# Failed to pull image ".../kube-contro1ler-manager:v1.31.0"   or  exec: "kube-contro1ler-manager": not found
vi /etc/kubernetes/manifests/kube-controller-manager.yaml     # command (va/yoki image) imlosini tuzating
k get pods -n kube-system -w       # controller manager Running
k get deploy nginx-deploy          # 3/3
```

Tuzoq: ReplicaSet joyida (Deployment kontrolleri ham... controller manager
ichida - bu variantda RS buzilishdan oldin mavjud edi). Belgisi - "kontroller
o’z ishini qilmayapti" → controller manager. `command:` qatorini ham,
`image:` qatorini ham tekshiring; xato yozuv ikkalasida ham bo’lishi mumkin.

### 10. HPA

```bash
k autoscale deploy web --name=web-hpa --min=2 --max=5 --cpu-percent=50
k get hpa web-hpa                  # TARGETS 0%/50% (metrics-server'siz <unknown>)  MINPODS 2  MAXPODS 5  REPLICAS 2
k get deploy web                   # bir daqiqadan keyin 2/2
```

Tuzoq: Deployment konteynerlarida CPU **request**’lari bo’lishi kerak, aks
holda HPA foizni hisoblay olmaydi; metrics-server’siz ham HPA `min`’gacha
masshtablaydi, lekin `<unknown>` ko’rsatadi.

## Baholash

| Vazifalar | Domen |
|---|---|
| 1, 4, 5 | Xavfsizlik: RBAC, securityContext, NetworkPolicy |
| 2 | JSONPath |
| 3, 7, 10 | Workload’lar |
| 6 | Rejalashtirish |
| 8, 9 | Nosozliklarni bartaraf etish: kubeconfig, control plane |

Uchala mock’ning ballarini qo’shing. Har bir mock **vaqt qolgan holda** 66%
dan bemalol yuqori bo’lsa, siz tayyorsiz. Agar har bir daqiqani ishlatib
zo’rg’a o’tsangiz, farqni speed-drills darsi qiladi. Agar biror domen uchala
mockda ham qulasa, weak-domain-review darsi - sizning rejangiz.

:::exam-tip
Uchta mockdagi 33 ta vazifa davomida nima hech qachon uchramaganiga e’tibor
bering: Helm chart yozish, noldan CNI, operator - hujjatlar va yigirma
daqiqadan ko’proq narsa talab qiladigan hech nima. Imtihon muhandislikni
emas, administratsiyani tekshiradi. Kenglik, aniqlik va tezlik - aynan shu
tartibda.
:::

## O’zingizni tekshiring

1. Nega 1-vazifada Role emas, ClusterRole kerak?
2. NetworkPolicy ingress qoidasida `ports` bor, lekin `from` yo’q. Kimga
   ruxsat beriladi?
3. 9-vazifada qaysi kuzatuv "controller manager buzilgan"ni "scheduler
   buzilgan"dan ajratadi?
