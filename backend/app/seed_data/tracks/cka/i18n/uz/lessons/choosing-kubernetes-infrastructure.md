## Klasterga ega bo’lishning uchta yo’li

| Turkum | Nima olasiz | Nima qilasiz | Misollar |
|---|---|---|---|
| **Lokal / o’rganish** | bir necha daqiqada mashinangizda klaster | operatsion jihatdan hech narsa | minikube, kind, k3d, Docker Desktop |
| **Turnkey / o’zingiz boshqaradigan** | siz nazorat qiladigan VM’larda klaster quradigan va yangilaydigan vositalar | VM ajratasiz, vositani ishga tushirasiz, klasterni boshqarasiz | kubeadm, kops, Kubespray, Cluster API, RKE2, OpenShift, Talos |
| **Hosted / managed** | provayder boshqaradigan control plane | node’lar (ba’zan), workload’lar | GKE, EKS, AKS, DigitalOcean, Linode, OpenShift Dedicated |

Muhim chegara: birinchi ikkitasida control plane **sizniki** - yangilashlar,
sertifikatlar, etcd backup’lari, HA. Uchinchisida esa provayderniki; siz
kubeconfig va node pool olasiz.

## Lokal

```bash
minikube start --nodes 2 --cni calico
kind create cluster --config kind-3node.yaml       # control plane + 2 worker, Docker konteynerlari sifatida
k3d cluster create lab --servers 1 --agents 2
```

- **minikube** - har bir node uchun VM yoki konteyner, ko’plab addon’lar, eng
  uzun tarix.
- **kind** - Docker ichidagi Kubernetes; tez, ko’p node’li, bu yo’nalish
  lablari ishlatadigani; add-on’siz LoadBalancer yo’q va node’lar konteyner
  bo’lgani uchun "node"dagi `systemctl` - bu `docker exec`.
- **k3s/k3d** - bitta binardan iborat Kubernetes; juda kichik, edge va CI
  uchun yaxshi.

Ularning hech biri sizga kubeadm’ning nosozlik holatlarini o’rgatmaydi, aynan
shuning uchun o’rnatish darslari haqiqiy VM’lardan foydalanadi.

## Turnkey

- **kubeadm** - upstream vosita: birinchi control plane’da `init`,
  qolganlarida `join`. U control plane’ni static Pod sifatida o’rnatadi, OS,
  runtime, CNI va load balancer’ni esa sizga qoldiradi. Bu **aynan** CKA
  vositasi.
- **kops** - AWS/GCP’da kubeadm uslubidagi klasterlar, bulut resurslari (VPC,
  ASG) siz uchun yaratiladi.
- **Kubespray** - bare metal va istalgan bulut uchun kubeadm atrofidagi
  Ansible playbook’lari.
- **Cluster API** - Kubernetes Kubernetes’ni boshqaradi: klasterlar custom
  resurs sifatida, workload klasterlarni yaratadigan boshqaruv klasteri.
- **Distributivlar** - RKE2/Rancher, OpenShift, Talos, Charmed Kubernetes:
  o’z installeri va supporti bilan keladigan tayyor to’plamlar.

```bash
kubeadm init --pod-network-cidr=10.244.0.0/16 --control-plane-endpoint=lb.example.com:6443
kubeadm join lb.example.com:6443 --token ... --discovery-token-ca-cert-hash sha256:...
```

## Hosted

```bash
gcloud container clusters create prod --num-nodes 3 --region europe-west1
aws eks create-cluster ... / eksctl create cluster
az aks create ...
```

Siz control plane node’larini hech qachon ko’rmaysiz. Yangilash - bu tugma
(yoki flag); etcd backup’lari provayderniki; HA ichiga kiritilgan. Evaziga:
API server’da o’zingizning admission flaglaringiz yo’q, o’zingizning
encryption-at-rest konfiguratsiyangiz yo’q (ular o’z KMS’ini taklif qiladi),
versiya tanlovi provayder qo’llab-quvvatlaydigani bilan cheklangan va har bir
klaster-soati uchun hisob.

## Tanlash

| Agar | Unda |
|---|---|
| CKA’ni o’rganayotgan bo’lsangiz | 2-3 ta VM’da kubeadm; tezkor tajribalar uchun kind |
| kichik jamoa, ops xodimi yo’q, bulutda | managed |
| talab bo’yicha ma’lumot o’z binongizda qolishi kerak | on-prem turnkey: kubeadm/Kubespray/RKE2, ustiga MetalLB va storage CSI |
| o’nlab klaster | Cluster API yoki flot vositalari bilan keladigan distributiv |
| edge / IoT | k3s / Talos |

:::exam-tip
"Qaysi infratuzilma" - CKA savoli emas. CKA savoli - keyingi darslardagi
kubeadm workflow’i va `kind` yoki `minikube` klasteri kubeadm klasteridan
narsalar qayerda joylashishi bilan farq qilishini bilish (kind node’lari -
konteynerlar: `docker exec kind-control-plane cat /etc/kubernetes/manifests/...`).
:::

## O’zingizni tekshiring

1. Uchta turkumning qaysilarida control plane sizniki bo’ladi va "sizniki"
   nimalarni o’z ichiga oladi?
2. Nega bu yo’nalish o’rnatish darslarida kind emas, VM’larda kubeadm
   ishlatadi?
3. Managed provayder API server’da qilishingizga ruxsat bermaydigan ikkita
   narsani ayting.
