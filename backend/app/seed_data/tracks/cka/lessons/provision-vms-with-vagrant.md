## Reproducible nodes

A kubeadm walkthrough is only worth doing if you can throw the machines
away and start again. **Vagrant** gives you that: a `Vagrantfile` describes
the VMs, `vagrant up` builds them, `vagrant destroy` removes them, and the
next `vagrant up` is identical. VirtualBox is the usual provider on a
laptop; libvirt on Linux; VMware and Parallels work too.

```bash
vagrant --version
vagrant box add ubuntu/jammy64        # a base image, downloaded once
```

## A three-node Vagrantfile

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

  # run on every node: the OS prep from the kubeadm docs
  config.vm.provision "shell", path: "prep.sh"
end
```

```bash
vagrant up                 # builds all three
vagrant status
vagrant ssh controlplane   # a shell on a node
vagrant halt / vagrant destroy -f
```

Two details that save an afternoon:

- **`private_network` with fixed IPs.** The default NAT interface gives every
  VM the same `10.0.2.15`; kubeadm must advertise on the private one
  (`--apiserver-advertise-address=192.168.56.11`), and the kubelet may need
  `--node-ip` in `/etc/default/kubelet` so that `kubectl get nodes -o wide`
  shows the right address.
- **2 CPUs, 2 GB** per node minimum - kubeadm's preflight refuses less on
  the control plane.

## prep.sh: what every node needs before kubeadm

```bash
#!/bin/bash
set -e
# swap off, now and at boot
swapoff -a
sed -i '/ swap / s/^/#/' /etc/fstab

# kernel modules and sysctls for the CNI
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

# containerd with the systemd cgroup driver
apt-get update && apt-get install -y containerd
mkdir -p /etc/containerd
containerd config default | sed 's/SystemdCgroup = false/SystemdCgroup = true/' > /etc/containerd/config.toml
systemctl restart containerd

# kubeadm, kubelet, kubectl from pkgs.k8s.io, pinned
apt-get install -y apt-transport-https ca-certificates curl gpg
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' > /etc/apt/sources.list.d/kubernetes.list
apt-get update && apt-get install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl
```

Every line corresponds to a preflight check or a later fault: swap → kubelet
refuses to start; `br_netfilter` → Services unreachable from same-node
Pods; `SystemdCgroup` → kubelet and containerd disagree and Pods flap; the
version-pinned repo → `kubeadm upgrade` works later.

:::exam-tip
In the exam the nodes are provisioned and prepped; what you type is from
`kubeadm init` onward. But when an install task fails preflight, the error
names one of the lines above (`[ERROR Swap]`, `[ERROR NumCPU]`,
`[ERROR FileContent--proc-sys-net-bridge-bridge-nf-call-iptables]`) and the
fix is that line.
:::

## Check yourself

1. Why give each Vagrant VM a `private_network` IP, and which kubeadm flag
   uses it?
2. Which three things in `prep.sh` does kubeadm's preflight check directly?
3. What does the `SystemdCgroup = true` line prevent?
