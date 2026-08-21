## Mock imtihon 3

Ikki soat. O’nta vazifa. Umumiy og’irlik 100. Uchtasining eng qiyini:
buzilgan control plane va buzilgan kubeconfig bilan ikkita nosozlik
vazifasi, klaster darajasidagi RBAC, NetworkPolicy, taint’lar, security
context’lar. Yozishni boshlashdan oldin har bir vazifani ikki marta o’qing.

```bash
alias k=kubectl; export do="--dry-run=client -o yaml"
```

---

**1.** (12) `pvviewer` ServiceAccount’ini, `persistentvolumes` ustida
`list`’ga ruxsat beruvchi `pvviewer-role` ClusterRole’ini va uni shu
ServiceAccount’ga beradigan `pvviewer-role-binding` ClusterRoleBinding’ini
yarating. Keyin o’sha ServiceAccount’dan foydalanadigan `pvviewer` Pod’ini
(image `redis`) yarating.

**2.** (6) JSONPath yordamida barcha node’larning `InternalIP` manzillarini
bitta qatorda, bo’sh joy bilan ajratib chiqaring va `/root/CKA/node_ips`
fayliga saqlang.

**3.** (10) Ikkita konteynerli `multi-pod` Pod’ini yarating: `alpha` (image
`nginx`) `name=alpha` env bilan va `beta` (image `busybox`, buyruq
`sleep 4800`) `name=beta` env bilan.

**4.** (8) `redis:alpine` image’idan foydalanib, `runAsUser: 1000` va
`fsGroup: 2000` bilan `non-root-pod` Pod’ini yarating.

**5.** (12) `default` namespace’ida `np-test-1` Pod’i (label
`run=np-test-1`, image `nginx`) va `np-test-service` Service’i bor (ularni
yarating). Shuningdek default-deny-ingress NetworkPolicy ham qo’llangan
(uni ham yarating). `np-test-1`’ga istalgan Pod’dan `80` portga **kiruvchi**
trafikka ruxsat beradigan `ingress-to-nptest` NetworkPolicy’sini yarating.
`busybox:1.28` Pod’i va `nc -z -v -w 2 np-test-service 80` bilan tekshiring.

**6.** (10) `node01` worker’ini `env_type=production:NoSchedule` bilan taint
qiling. `dev-redis` Pod’ini (image `redis:alpine`) yarating va u `node01`’ga
**joylashtirilmaganini** tasdiqlang. Taint’ga toleratsiya qiladigan
`prod-redis` Pod’ini (image `redis:alpine`) yarating va u `node01`’ga
**joylashtirilganini** tasdiqlang.

**7.** (6) `hr` namespace’ida `environment=production` va `tier=frontend`
label’lari bilan, `redis:alpine` image’idan `hr-pod` Pod’ini yarating.

**8.** (12) `/root/CKA/super.kubeconfig` kubeconfig fayli yaratilgan, lekin
ishlamaydi. Muammoni toping va tuzating. (Mock’dan oldin:
`cp ~/.kube/config /root/CKA/super.kubeconfig` va server portini `9999`’ga
o’zgartiring.)

**9.** (14) `nginx-deploy` Deployment’i (uni yarating: image `nginx`, 1
replika) `3`’ga masshtablangan, lekin yangi Pod’lar umuman paydo
bo’lmayapti. Sababni toping va tuzating. (Mock’dan oldin, control-plane
node’da: `sed -i 's/kube-controller-manager/kube-contro1ler-manager/' /etc/kubernetes/manifests/kube-controller-manager.yaml`
- 1 raqamiga e’tibor bering - keyin
`k scale deploy nginx-deploy --replicas=3`.)

**10.** (10) `web` Deployment’i uchun (yarating: `nginx`, 1 replika, request
cpu `100m`) `web-hpa` HorizontalPodAutoscaler’ini yarating: min `2`, max
`5`, maqsad CPU `50%`. Deployment minimumgacha masshtablanishini
tasdiqlang. (metrics-server kerak bo’ladi; u yo’q bo’lsa, HPA `<unknown>`
ko’rsatadi - obyektning o’zi baribir baholanadi.)

---

Ballarni hisoblang, keyin yechimlarga o’ting.

:::exam-tip
9-vazifa - imtihonning eng qiyin nosozlik savolining shakli: simptom
workload’da (Pod’lar paydo bo’lmayapti), sabab control plane’da (ishlamay
turgan komponent), tuzatish esa faylda. Simptomdan faylgacha yo’l:
`get deploy` → `get rs` (yaratilgan, lekin Pod’lar yo’qmi?) →
"ReplicaSet’dan Pod’larni kim yaratadi" → `get pods -n kube-system` →
manifest. Yursangiz uch daqiqa; taxmin qilsangiz o’ttiz.
:::

## O’zingizni tekshiring

1. 9-vazifada Deployment’dan control plane tomonga ishora qilgan birinchi
   kuzatuv nima edi?
2. 5-vazifada policy qaysi Pod’ni tanladi va `policyTypes` ichida nima bor
   edi?
3. 8-vazifada faylni ochishdan oldin kubeconfig’da nima noto’g’riligini
   qaysi buyruq aytdi?
