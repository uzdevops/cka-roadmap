## virt-install: one command to define and boot

`virt-install` creates the domain XML, allocates the disk, attaches the
network and starts the machine.

```bash
sudo virt-install \
  --name web01 \
  --memory 2048 \
  --vcpus 2 \
  --disk path=/var/lib/libvirt/images/web01.qcow2,size=20,format=qcow2 \
  --os-variant ubuntu24.04 \
  --network network=default \
  --graphics none \
  --console pty,target_type=serial \
  --location http://archive.ubuntu.com/ubuntu/dists/noble/main/installer-amd64/ \
  --extra-args 'console=ttyS0,115200n8'
```

| Option | Means |
|---|---|
| `--name` | the domain name |
| `--memory` | MiB of RAM |
| `--vcpus` | virtual CPUs |
| `--disk path=...,size=N` | disk image (created if absent), size in GiB |
| `--os-variant` | tells libvirt which devices/defaults suit the guest (`osinfo-query os` lists them) |
| `--network network=default` | the NAT network; or `bridge=br0` |
| `--graphics none` + `--console` | headless: install and log in over the serial console |
| `--location` | a network installer tree (text install) |
| `--cdrom /path.iso` | boot an ISO instead (next lesson) |
| `--import` | do not install: boot an existing disk image |
| `--noautoconsole` | do not attach the console immediately |

`--os-variant` is worth getting right: it decides virtio drivers and
defaults, and a wrong value costs performance.

## The fast path: a cloud image

Installing from an ISO takes twenty minutes of answering prompts. Cloud
images are pre-installed disks that configure themselves at first boot
from a **cloud-init** seed - the way to get a working VM in about a minute.

```bash
cd /var/lib/libvirt/images
sudo wget https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img
sudo qemu-img convert -O qcow2 noble-server-cloudimg-amd64.img web01.qcow2
sudo qemu-img resize web01.qcow2 20G
```

```bash
cat > user-data <<'EOF'
#cloud-config
hostname: web01
users:
  - name: ahmad
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    ssh_authorized_keys:
      - ssh-ed25519 AAAA... your key here
package_update: true
packages: [nginx]
EOF
echo -e "instance-id: web01\nlocal-hostname: web01" > meta-data
sudo cloud-localds /var/lib/libvirt/images/web01-seed.iso user-data meta-data
```

```bash
sudo virt-install --name web01 --memory 2048 --vcpus 2 \
  --disk /var/lib/libvirt/images/web01.qcow2,device=disk,bus=virtio \
  --disk /var/lib/libvirt/images/web01-seed.iso,device=cdrom \
  --os-variant ubuntu24.04 --network network=default \
  --graphics none --console pty,target_type=serial --import --noautoconsole
```

`--import` skips installation entirely: the disk already contains a
system, and cloud-init applies your `user-data` on first boot.

## Reaching the machine

```bash
virsh list
virsh console web01                 # serial console; Ctrl+] to detach
virsh domifaddr web01               # its DHCP address
ssh ahmad@192.168.122.45
sudo virsh net-dhcp-leases default  # every lease on the NAT network
```

If `virsh console` shows nothing, the guest is not writing to the serial
port: boot with `console=ttyS0` on the kernel command line (cloud images
do this already), or use `virt-manager`/VNC.

## Everyday operations

```bash
virsh start web01; virsh shutdown web01; virsh reboot web01
virsh autostart web01
virsh dominfo web01; virsh domstats web01
virsh setmem web01 4G --config      # takes effect after a restart
virsh setvcpus web01 4 --config --maximum
virsh attach-disk web01 /var/lib/libvirt/images/data.qcow2 vdb --persistent --subdriver qcow2
virsh detach-disk web01 vdb --persistent
virsh snapshot-create-as web01 clean "Fresh install"
virsh dumpxml web01 | grep -A3 "<disk"
```

That `attach-disk` line is how you give yourself the spare disks the
storage weeks need:

```bash
sudo qemu-img create -f qcow2 /var/lib/libvirt/images/lab-disk1.qcow2 5G
sudo virsh attach-disk web01 /var/lib/libvirt/images/lab-disk1.qcow2 vdb --persistent --subdriver qcow2
# inside the guest: lsblk shows /dev/vdb
```

## Cloning

```bash
virsh shutdown web01
sudo virt-clone --original web01 --name web02 --auto-clone
sudo virt-sysprep -d web02          # reset hostname, SSH host keys, machine-id, logs
virsh start web02
```

`virt-sysprep` matters: a clone that keeps the original's machine-id and
SSH host keys will confuse DHCP and every SSH client that ever connected.

:::exam-tip
The LFCS asks you to create and boot a VM, not to master libvirt. Know
`virt-install` with `--name --memory --vcpus --disk --os-variant
--network`, know `virsh start/shutdown/list --all/autostart/console`, and
know that `--import` boots an existing image while `--cdrom`/`--location`
installs a new one.
:::

## Check yourself

1. What do `--import`, `--cdrom` and `--location` each do in
   `virt-install`?
2. How do you find a VM's IP address from the host, in two ways?
3. Why run `virt-sysprep` after cloning a VM?
