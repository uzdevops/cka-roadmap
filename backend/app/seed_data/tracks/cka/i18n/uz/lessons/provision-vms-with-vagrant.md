## Qayta tiklanadigan node’lar

kubeadm bo’yicha mashq mashinalarni tashlab yuborib, qaytadan boshlay
olsangizgina arziydi. **Vagrant** sizga aynan shuni beradi: `Vagrantfile`
VM’larni tasvirlaydi, `vagrant up` ularni quradi, `vagrant destroy` ularni
o’chiradi va keyingi `vagrant up` bir xil natija beradi. Noutbukda odatdagi
provayder - VirtualBox; Linux’da libvirt; VMware va Parallels ham ishlaydi.

```bash
vagrant --version
vagrant box add ubuntu/jammy64        # bazaviy image, bir marta yuklab olinadi
```

## Uch node’li Vagrantfile

```ruby
# Vagrantfile
NUM_WORKERS = 2
IP_BASE = "192.168.56."

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.box_check_update = false

  config.vm.define "controlplane" do |node|
    node.vm.hostname = "controlplane"
    node.vm.network "private_network", ip: "#{IP_BASE}11"
    node.vm.provider "virtualbox" do |vb|
      vb.memory = 2048
      vb.cpus = 2
    end
  end

  (1..NUM_WORKERS).each do |i|
    config.vm.define "node0#{i}" do |node|
      node.vm.hostname = "node0#{i}"
      node.vm.network "private_network", ip: "#{IP_BASE}#{20 + i}"
      node.vm.provider "virtualbox" do |vb|
        vb.memory = 2048
        vb.cpus = 2
      end
    end
  end

  # har bir node'da bajariladi: kubeadm hujjatlaridagi OS tayyorgarligi
  config.vm.provision "shell", path: "prep.sh"
end
```

```bash
vagrant up                 # uchalasini ham quradi
vagrant status
vagrant ssh controlplane   # node'dagi shell
vagrant halt / vagrant destroy -f
```

Bir kunni tejaydigan ikkita tafsilot:

- **Qat’iy IP’li `private_network`.** Sukut bo’yicha NAT interfeysi har bir
  VM’ga bir xil `10.0.2.15`’ni beradi; kubeadm esa private manzilda e’lon
  qilishi kerak (`--apiserver-advertise-address=192.168.56.11`), va
  `kubectl get nodes -o wide` to’g’ri manzilni ko’rsatishi uchun kubelet’ga
  `/etc/default/kubelet` ichida `--node-ip` kerak bo’lishi mumkin.
- **Har bir node’ga kamida 2 CPU, 2 GB** - kubeadm’ning preflight’i control
  plane’da bundan kamiga rozi bo’lmaydi.

## prep.sh: kubeadm’dan oldin har bir node’ga nima kerak

```bash
#!/bin/bash
set -e
# swap'ni hozir ham, yuklanishda ham o'chirish
swapoff -a
sed -i '/ swap / s/^/#/' /etc/fstab

# CNI uchun kernel modullari va sysctl'lar
cat <<EOF >/etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
modprobe overlay && modprobe br_netfilter
cat <<EOF >/etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
sysctl --system

# systemd cgroup drayveri bilan containerd
apt-get update && apt-get install -y containerd
mkdir -p /etc/containerd
containerd config default | sed 's/SystemdCgroup = false/SystemdCgroup = true/' > /etc/containerd/config.toml
systemctl restart containerd

# pkgs.k8s.io dan kubeadm, kubelet, kubectl, versiyasi qotirilgan
apt-get install -y apt-transport-https ca-certificates curl gpg
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' > /etc/apt/sources.list.d/kubernetes.list
apt-get update && apt-get install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl
```

Har bir satr biror preflight tekshiruviga yoki keyinroq chiqadigan nosozlikka
mos keladi: swap → kubelet ishga tushishdan bosh tortadi; `br_netfilter` →
Service’lar bir xil node’dagi Pod’lardan ko’rinmaydi; `SystemdCgroup` →
kubelet va containerd kelisha olmaydi va Pod’lar tebranib turadi; versiyasi
qotirilgan repozitoriy → keyinroq `kubeadm upgrade` ishlaydi.

:::exam-tip
Imtihonda node’lar tayyorlangan va sozlangan bo’ladi; siz yozadigan narsa
`kubeadm init`’dan boshlanadi. Lekin o’rnatish vazifasi preflight’dan
o’tmaganda, xato yuqoridagi satrlardan birini nomlaydi (`[ERROR Swap]`,
`[ERROR NumCPU]`,
`[ERROR FileContent--proc-sys-net-bridge-bridge-nf-call-iptables]`) va
yechim - o’sha satr.
:::

## O’zingizni tekshiring

1. Nega har bir Vagrant VM’iga `private_network` IP’si beriladi va kubeadm’ning
   qaysi flagi undan foydalanadi?
2. `prep.sh`’dagi qaysi uchta narsani kubeadm’ning preflight’i bevosita
   tekshiradi?
3. `SystemdCgroup = true` satri nimaning oldini oladi?
