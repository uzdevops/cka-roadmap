## The Linux hypervisor stack

A virtual machine has its own kernel and virtual hardware, unlike a
container. On Linux the pieces are:

```
  virsh / virt-manager / virt-install     ← the tools you type
            │
        libvirtd                          ← the management daemon and API
            │
          QEMU                            ← emulates the hardware (disks, NICs, console)
            │
          KVM  (kernel module)            ← makes the CPU run guest code at native speed
```

**KVM** turns the kernel into a hypervisor, **QEMU** provides the virtual
devices, **libvirt** gives one API and XML definition format above them.
`virsh` is libvirt's command line.

## Prerequisites

```bash
egrep -c '(vmx|svm)' /proc/cpuinfo        # >0 = the CPU supports virtualisation (Intel vmx / AMD svm)
lsmod | grep kvm                           # kvm_intel or kvm_amd loaded
sudo apt install qemu-kvm libvirt-daemon-system virtinst libvirt-clients bridge-utils virt-manager
sudo dnf install qemu-kvm libvirt virt-install virt-manager
sudo systemctl enable --now libvirtd
sudo usermod -aG libvirt,kvm "$USER"       # log out and back in to use virsh without sudo
virt-host-validate                          # checks everything above and reports what is missing
```

If `/proc/cpuinfo` shows no `vmx`/`svm`, virtualisation is disabled in the
BIOS/UEFI, or you are already inside a VM without nested virtualisation.

## virsh: the vocabulary

```bash
virsh list                        # running domains ("domain" = VM)
virsh list --all                  # including stopped
virsh dominfo web01               # state, CPUs, memory, autostart
virsh domifaddr web01             # its IP addresses
virsh start web01
virsh shutdown web01              # ACPI shutdown - graceful
virsh reboot web01
virsh destroy web01               # pull the power - not graceful, not a delete
virsh undefine web01 --remove-all-storage    # delete the definition (and disks)
virsh autostart web01             # start at host boot
virsh autostart --disable web01
virsh console web01               # attach to the serial console (Ctrl+] to leave)
virsh edit web01                  # edit the domain XML
virsh dumpxml web01 > web01.xml   # export the definition
virsh define web01.xml            # import it
virsh setmem web01 2G --config; virsh setvcpus web01 2 --config
```

`shutdown` asks the guest; `destroy` is the reset button. Both leave the
domain defined - only `undefine` removes it.

## Storage: pools and volumes

```bash
virsh pool-list --all
virsh pool-info default
virsh vol-list default                     # the disk images in it
ls -lh /var/lib/libvirt/images/            # where "default" usually lives
qemu-img create -f qcow2 /var/lib/libvirt/images/web01.qcow2 20G
qemu-img info /var/lib/libvirt/images/web01.qcow2
qemu-img resize /var/lib/libvirt/images/web01.qcow2 +10G     # grow the disk (then grow the partition inside)
qemu-img convert -O qcow2 disk.raw disk.qcow2
```

**qcow2** grows as it is used and supports snapshots; **raw** is a plain
image, slightly faster. qcow2 is the default for good reasons.

## Networking

```bash
virsh net-list --all
virsh net-info default
virsh net-dumpxml default          # the NAT network: 192.168.122.0/24, dnsmasq, DHCP
virsh net-start default; virsh net-autostart default
```

| Mode | Guests get | Use |
|---|---|---|
| **NAT** (`default`) | an address on a private libvirt network; outbound works, inbound needs forwarding | laptops, labs |
| **bridge** | an address on the **physical** LAN, like another machine | servers |
| **isolated** | a private network with no route out | test environments |
| **macvtap** | the LAN directly, but cannot talk to the host | special cases |

A bridge on the host (week 9 builds one with `nmcli`) is what production
VMs attach to.

## Snapshots

```bash
virsh snapshot-create-as web01 before-upgrade "Before the 1.27 upgrade"
virsh snapshot-list web01
virsh snapshot-revert web01 before-upgrade
virsh snapshot-delete web01 before-upgrade
```

Snapshots are for short-lived safety before a risky change - not backups,
and they cost performance while they exist.

:::tip
For this track, one VM is all the lab equipment you need: the storage
lessons want spare disks (`qemu-img create` + `virsh attach-disk`), the
firewall lessons want a machine you can lock yourself out of, and the boot
lessons want a console you can reach when SSH is gone (`virsh console`).
Snapshot it before each of those weeks.
:::

## Check yourself

1. What do KVM, QEMU and libvirt each contribute?
2. What is the difference between `virsh shutdown`, `virsh destroy` and
   `virsh undefine`?
3. Which network mode gives a VM an address on the physical LAN, and which
   is the default?
