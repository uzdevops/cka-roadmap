## Har bir node’ga nima kerak

Pod’lardan oldin node’larning o’zi gaplasha olishi kerak. Har bir node’ga
kerak:

- kamida bitta IP’li interfeys, betakror hostname va betakror MAC - bir xil
  MAC yoki `machine-id`’ga ega klonlangan VM’lar klasterning klassik
  nosozligi;
- node’lar orasida kerakli portlarning ochiqligi;
- CNI tayanadigan yadro sozlamalari.

```bash
hostname; ip -br addr; ip link show eth0 | grep ether
cat /sys/class/dmi/id/product_uuid          # har bir node'da farq qilishi shart
```

## Portlar

| Komponent | Port | Protokol | Kim ulanadi |
|---|---|---|---|
| kube-apiserver | **6443** | TCP | hamma |
| etcd | **2379** (klientlar), **2380** (peer’lar) | TCP | API server; boshqa etcd a’zolari |
| kubelet | **10250** | TCP | API server (loglar, exec, metrikalar) |
| kube-scheduler | 10259 | TCP | localhost health/metrikalar |
| kube-controller-manager | 10257 | TCP | localhost health/metrikalar |
| kube-proxy | 10256 | TCP | health |
| NodePort Service’lar | **30000-32767** | TCP/UDP | tashqi klientlar, har bir node’da |
| CNI | turlicha: Flannel VXLAN 8472/UDP, Calico BGP 179/TCP, Weave 6783 TCP/UDP + 6784 UDP | node’dan node’ga |

```bash
ss -tlnp | grep -E "6443|2379|2380|10250"        # bu node aslida nimani tinglaydi
kubectl get svc -A | grep NodePort                # qaysi node portlari band
```

Node’lar orasida 10250 ni to’sadigan firewall sizga `kubectl get` ishlaydigan,
`kubectl logs`/`exec` esa kutish vaqti bilan tugaydigan klaster beradi; CNI
portini to’sadigani esa faqat o’sha node’dagi boshqa Pod’largagina yeta
oladigan Pod’lar beradi. Qaysi alomat qayerga ishora qilishini payqay
oladigan darajada bu jadvalni biling.

## Yadro va sysctl

```bash
cat /etc/modules-load.d/k8s.conf
# overlay
# br_netfilter
cat /etc/sysctl.d/k8s.conf
# net.bridge.bridge-nf-call-iptables  = 1
# net.bridge.bridge-nf-call-ip6tables = 1
# net.ipv4.ip_forward                 = 1
sysctl --system
```

`br_netfilter` va ustiga `bridge-nf-call-iptables=1` iptables’ga bridge
orqali o’tayotgan trafikni ko’rish imkonini beradi - ularsiz kube-proxy’ning
Service qoidalari o’sha node’dagi Pod’dan Service’ga ketayotgan trafikka
qo’llanmaydi va sizda "Service node A’dan ishlaydi, lekin node A’dagi
Pod’lardan ishlamaydi" jumbog’i paydo bo’ladi. `ip_forward` - node’ning o’z
Pod’lari uchun marshrutlashi. Bular o’chiq bo’lsa, kubeadm’ning preflight
tekshiruvlari shikoyat qiladi.

## Uchta tarmoq

Klasterda bir-biri bilan kesishmasligi kerak bo’lgan uchta manzil diapazoni
bor:

| Diapazon | Nima turadi | Qayerda beriladi |
|---|---|---|
| node tarmog’i | node’larning o’z IP’lari | sizning infratuzilmangiz |
| **Pod CIDR** | Pod IP’lari; har bir node bir bo’lak oladi | `kubeadm init --pod-network-cidr`, controller manager’da `--cluster-cidr`, CNI config’i |
| **Service CIDR** | ClusterIP’lar | API server’da `--service-cluster-ip-range` (sukut bo’yicha `10.96.0.0/12`) |

```bash
kubectl cluster-info dump | grep -m1 -- --cluster-cidr
kubectl cluster-info dump | grep -m1 -- --service-cluster-ip-range
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.podCIDR}{"\n"}{end}'
```

:::exam-tip
"Bu klasterning Pod CIDR / Service CIDR’i qanday / node01’ga qaysi diapazon
berilgan" kabi savollarga o’sha uchta buyruq va CNI’ning ConfigMap’ini o’qish
javob beradi (`kubectl get cm kube-flannel-cfg -n kube-flannel
-o yaml` → `Network`). Agar CNI’da sozlangan diapazon va
`--pod-network-cidr` bir-biriga mos kelmasa, Pod’lar node’lar marshrutlay
olmaydigan IP’lar oladi - o’rnatish bosqichining sevimli nosozligi.
:::

## CNI haqida imtihon nimani kutadi

CKA sizning qaysi CNI’ni bilishingizga qiziqmaydi; u sizning quyidagilarni
qila olishingizga qiziqadi:

- CNI umuman yo’q klasterni tanib olish (`NotReady` node’lar,
  `ContainerCreating` Pod’lar, bo’sh `/etc/cni/net.d`);
- uni manifestidan **o’rnatish** va uning Pod CIDR’ini klasternikiga mos
  qilib qo’yish;
- qaysi biri o’rnatilganini va u nima sifatida ishlashini topish (odatda
  `kube-system`’dagi yoki o’zining namespace’idagi DaemonSet);
- NetworkPolicy uni majburlay oladigan CNI talab qilishini bilish.

```bash
kubectl get pods -A -o wide | grep -iE "flannel|calico|weave|cilium"
kubectl get ds -A | grep -iE "flannel|calico|weave|cilium"
```

## O’zingizni tekshiring

1. `kubectl logs` ishlashi uchun control plane’dan har bir node’ga qaysi port
   ochiq bo’lishi kerak?
2. Klasterdagi uchta manzil diapazonini ayting va Service’nikini qaysi flag
   belgilaydi?
3. Service node’ning shell’idan yetib boradi, lekin o’sha node’dagi
   Pod’lardan yo’q. Qaysi sysctl’ni tekshirasiz?
