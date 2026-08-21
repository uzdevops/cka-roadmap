## Birinchi buyruqdan oldingi savollar

"Kubernetes o’rnatamiz" - bu reja emas. Reja - beshta savolga berilgan
javoblar, chunki ularning har biri nimani va qayerga o’rnatishingizni
o’zgartiradi.

### 1. U nima uchun?

| Maqsad | Shakli |
|---|---|
| o’rganish, noutbuk | minikube / kind: bitta node, control plane va worker birga |
| ishlab chiqish, test | kichik ko’p node’li klaster, ko’pincha VM’larda kubeadm, yoki har bir jamoaga bitta managed klaster |
| production | bir nechta control plane node, alohida etcd yoki ≥3 a’zo bilan stacked, yukka mos o’lchangan worker’lar, API oldida HA load balancer |

Bitta node’li klaster o’rganish uchun yaxshi va ishlab turishi shart bo’lgan
har qanday narsa uchun foydasiz: barcha komponentlar bitta nosozlik domenini
bo’lishadi.

### 2. Bulut yoki on-prem?

- **Managed** (EKS, GKE, AKS): control plane’ni provayder boshqaradi; siz API
  server’ni yangilamaysiz va etcd’ni backup qilmaysiz - lekin ularni sozlay
  ham olmaysiz. Ko’pchilik jamoalar shu yerdan boshlashi kerak.
- **Bulut VM’larida o’zingiz boshqaradigan**: kubeadm (yoki kops, Cluster
  API); to’liq nazorat, to’liq mas’uliyat, bulut integratsiyalari
  (LoadBalancer Service’lar, CSI disklar) hamon mavjud.
- **On-prem / bare metal**: kubeadm yoki distributiv (Rancher/RKE2,
  OpenShift, k3s); load balancer’ni (MetalLB), storage’ni (Ceph, NFS,
  SAN’ning CSI’si) va mashinalarni ham siz berasiz.

CKA - o’zi boshqariladigan dunyo: Linux host’larda kubeadm.

### 3. Qanchalik katta?

| Chegara (upstream’da sinalgan) | Qiymat |
|---|---|
| klasterdagi node’lar | 5,000 |
| klasterdagi Pod’lar | 150,000 |
| klasterdagi konteynerlar | 300,000 |
| node’dagi Pod’lar | 110 (kubelet’ning sukut bo’yicha `maxPods` qiymati) |

Ustiga IPAM darsidagi hisob: har bir node’ga `/24` beradigan `/16` Pod CIDR -
256 node. Control plane’ni node soniga qarab o’lchang - klaster o’sgani sari
API server va etcd ko’proq CPU va xotira (etcd uchun esa tezroq disk) talab
qiladi; upstream hujjatlarda jadval bor.

### 4. Nechta control plane node?

| Soni | Nimaga chidaydi | Izoh |
|---|---|---|
| 1 | hech nimaga | faqat lab |
| 3 | 1 nosozlikka | standart; etcd kvorumi 3 tadan 2 ta |
| 5 | 2 nosozlikka | katta yoki kritik klasterlar |

Juft sonlar hech narsa bermaydi (4 node, kvorum 3, 1 nosozlikka chidaydi -
3 bilan bir xil). Va **etcd topologiyasi**: stacked (etcd control plane
node’larda, kubeadm’ning sukut varianti, soddaroq) yoki external (etcd o’z
mashinalarida, mustaqil nosozlik, ko’proq mashina). Ikkalasi ham HA darsida.

### 5. Storage va tarmoq tanlovlari

- **CNI**: Calico (policy, BGP yoki overlay), Cilium (eBPF, policy,
  kuzatuvchanlik), Flannel (sodda, policy yo’q). NetworkPolicy hech qachon
  kerak bo’lmasligiga ishonchingiz komil bo’lmasa, uni majburlay oladiganini
  tanlang.
- **Storage**: muhitingizga mos CSI drayveri; bare metal’da Ceph/Rook,
  Longhorn yoki vendor’niki; umumiy fayl tizimlari uchun NFS.
- **Ingress/Gateway**: nginx Ingress yoki biror Gateway implementatsiyasi va
  sizga load balancer kerakmi-yo’qmi (on-prem’da MetalLB).

## Node talablari

kubeadm hujjatlariga ko’ra har bir node’da quyidagilar bo’lishi kerak:
qo’llab-quvvatlanadigan Linux (Ubuntu, Debian, RHEL oilasi, SUSE...),
**kamida 2 GB RAM va 2 CPU**
(control plane uchun ko’proq), node’lar orasida to’liq tarmoq bog’lanishi,
**noyob hostname, MAC va product_uuid**, swap **o’chirilgan** (yoki kubelet
unga chidaydigan qilib sozlangan), kerakli portlar ochiq va o’rnatilgan
konteyner runtime.

:::exam-tip
Imtihon dizayn savollarini bermaydi. U sizga talablarga allaqachon javob
beradigan node’larni beradi va klasterni **ko’tarish**, unga **qo’shilish**
yoki uni **tuzatish**ni so’raydi. Bu dars - o’rnatish qadamlari nega aynan
shunday ekanining konteksti - va "2 CPU, swap o’chirilgan, noyob machine-id"
ro’yxati aynan `kubeadm init` ishlamay qolganda uning preflight tekshiruvlari
shikoyat qiladigan narsa.
:::

## O’zingizni tekshiring

1. Nega 3 ta control plane node standart va nega 4 tasi undan yaxshiroq emas?
2. Managed klaster yelkangizdan nimani oladi va nimadan mahrum qiladi?
3. `kubeadm init` preflight tekshiruvlaridan o’tishi uchun har bir node’da
   bo’lishi shart bo’lgan to’rtta narsani ayting.
