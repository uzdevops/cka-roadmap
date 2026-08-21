## CKA’dan o’qish bilan o’ta olmaysiz

Imtihon - bu terminal. Haqiqiy klasterda o’tkazgan har bir soatingiz o’qishga
sarflangan uch soatga arziydi. Bu dars sizga bir necha daqiqada buzib, qaytadan
qura oladigan klaster beradi.

## Lokal klaster tanlash

| Vosita | Ko’p node | Tezlik | Nimaga eng mos |
| --- | --- | --- | --- |
| **kind** | Ha, juda oson | Eng tez | Kundalik mashq, ko’p node’li stsenariylar |
| **minikube** | Ha (`--nodes`) | Tez | Addon’lar: ingress, metrics-server, dashboard |
| **VM’larda kubeadm** | Ha | Eng sekin | 4-bosqich: yangilash, etcd, sertifikatlar |

**kind** dan boshlang. 4-bosqichda haqiqiy VM’larga o’ting, chunki klasterni
o’rnatish va yangilash vazifalarini kind’da mashq qilib bo’lmaydi.

## Vositalarni o’rnatish

```bash
# kubectl - har doim klasteringizning minor versiyasiga moslang
curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version --client

# kind
[ $(uname -m) = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind
```

## Uch node’li kind klasteri

```yaml
# kind-cluster.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: cka
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 8080
        protocol: TCP
  - role: worker
  - role: worker
```

```bash
kind create cluster --config kind-cluster.yaml
kubectl get nodes
# NAME                STATUS   ROLES           AGE   VERSION
# cka-control-plane   Ready    control-plane   45s   v1.31.x
# cka-worker          Ready    <none>          30s   v1.31.x
# cka-worker2         Ready    <none>          30s   v1.31.x
```

Uni yo’q qilib, noldan boshlash bir daqiqadan kam vaqt oladi - buzuvchi
vazifalarni mashq qilganda aynan shu kerak bo’ladi:

```bash
kind delete cluster --name cka
```

## kubeconfig’ni tushunish

Har bir `kubectl` buyrug’i `~/.kube/config` dan uchta narsani aniqlaydi:
**cluster** (qayerda), **user** (kim) va **namespace** - bularning hammasi
**context** ichida jamlangan.

```bash
kubectl config view --minify              # aslida ishlatayotgan kontekstingiz
kubectl config get-contexts
kubectl config use-context kind-cka
kubectl config set-context --current --namespace=dev   # -n dev yozishni bas qiling
```

```yaml
# ~/.kube/config, soddalashtirilgan
clusters:
  - name: kind-cka
    cluster:
      server: https://127.0.0.1:39443
      certificate-authority-data: LS0tLS1C...
users:
  - name: kind-cka
    user:
      client-certificate-data: LS0tLS1C...
      client-key-data: LS0tLS1C...
contexts:
  - name: kind-cka
    context:
      cluster: kind-cka
      user: kind-cka
      namespace: default
current-context: kind-cka
```

:::warning
Imtihon vazifalari tez-tez "`xyz` klasterida" yoki "`abc` namespace’ida" deb
boshlanadi. To’g’ri buyruqni noto’g’ri kontekstda bajarish nol ball beradi.
`kubectl config use-context` ni har bir savolda birinchi yozadigan narsangizga
aylantiring.
:::

## Vaqt yutdiradigan shell sozlamasi

Ikki soat - ko’p emas. Buni imtihonning birinchi daqiqasida va har bir mashq
seansida sozlang, toki u mushak xotirasiga aylansin.

```bash
# alias'lar
alias k=kubectl
complete -o default -F __start_kubectl k

# dry-run + yaml chiqishi, manifest karkasini yasash uchun doim ishlatiladi
export do="--dry-run=client -o yaml"
export now="--force --grace-period=0"

# ishlatilishi
k run nginx --image=nginx $do > pod.yaml
k delete pod nginx $now
```

Yangi terminal ularni saqlab qolishi uchun `~/.bashrc` ga qo’shing:

```bash
cat <<'EOF' >> ~/.bashrc
alias k=kubectl
complete -o default -F __start_kubectl k
export do="--dry-run=client -o yaml"
export now="--force --grace-period=0"
EOF
source ~/.bashrc
```

## YAML uchun Vim sozlamalari

YAML bo’shliqlarga sezgir va imtihon sizga `vim` beradi. Busiz siz indentatsiya
xatolariga vaqt yo’qotasiz:

```bash
cat <<'EOF' >> ~/.vimrc
set expandtab
set tabstop=2
set shiftwidth=2
set number
EOF
```

:::exam-tip
`vim` da hujjatlardan blok nusxalashdan oldin `:set paste` qilish ketma-ket
avtomatik indentatsiyaning oldini oladi. Blokni tanlash uchun `Ctrl-v`, keyin
bir nechta qatorga yozish uchun `Shift-i` - nusxalangan parchani indentatsiya
qilishning eng tez yo’li.
:::

## Muhitingizni tekshiring

Sozlash tugadi deb hisoblashdan oldin bularning hammasini ishga tushiring:

```bash
kubectl get nodes                       # hammasi Ready
kubectl get pods -A                     # kube-system dagilar hammasi Running
kubectl run test --image=nginx --restart=Never
kubectl get pod test -o wide            # worker'ga joylashtirilgan
kubectl exec test -- nginx -v
kubectl delete pod test
```

Agar bularning har biri ishlasa, sizda ishlaydigan klaster va ishlaydigan CLI
bor.

:::tip
`metrics-server` ni erta o’rnating, shunda `kubectl top` ishlaydi - u sizga
autoscaling va nosozlikni bartaraf etish bosqichlarida kerak bo’ladi. kind’da
unga bitta qo’shimcha flag kerak, chunki kubelet serving sertifikatlari
o’z-o’zidan imzolangan:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch -n kube-system deployment metrics-server --type=json \
  -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```
:::

## O’zingizni tekshiring

1. kubeconfig *context*’i qaysi uchta narsani bir-biriga bog’laydi?
2. Pod’ni yaratmasdan uning manifestini qanday generatsiya qilasiz?
3. Nega `kind` klaster yangilashni mashq qilish uchun mos emas?
