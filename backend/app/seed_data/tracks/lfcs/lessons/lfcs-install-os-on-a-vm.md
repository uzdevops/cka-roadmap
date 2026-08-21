## Installing from an ISO

The long way round, and the one that teaches you what a cloud image does
for you: attach installation media, boot from it, answer the installer.

```bash
cd /var/lib/libvirt/images
sudo wget https://releases.ubuntu.com/24.04/ubuntu-24.04-live-server-amd64.iso
sha256sum ubuntu-24.04-live-server-amd64.iso        # compare with SHA256SUMS from the mirror
```

```bash
sudo virt-install \
  --name lab01 \
  --memory 2048 --vcpus 2 \
  --disk path=/var/lib/libvirt/images/lab01.qcow2,size=20,format=qcow2,bus=virtio \
  --cdrom /var/lib/libvirt/images/ubuntu-24.04-live-server-amd64.iso \
  --os-variant ubuntu24.04 \
  --network network=default \
  --graphics vnc,listen=0.0.0.0
```

With `--graphics vnc` the installer's screen is available over VNC:

```bash
virsh vncdisplay lab01           # :0  → port 5900
virt-viewer lab01                # if you have a desktop
# remote: ssh -L 5900:127.0.0.1:5900 host   then point a VNC client at localhost:5900
```

For a text-only install over the serial console, use `--location` with
`--extra-args 'console=ttyS0,115200n8'` (previous lesson) and
`virsh console lab01`.

## Walking the installer

The questions are the same on every distribution, and each maps to a topic
in this track:

| Installer step | Decide | Covered in |
|---|---|---|
| language, keyboard, time zone | locale; time zone matters for logs | week 10 (time) |
| network | DHCP or static, hostname | week 9 |
| disk layout | whole disk, LVM, manual partitions, swap size | weeks 11-12 |
| filesystem | ext4 or xfs; separate `/var`, `/home`? | week 11 |
| user account | the first user, and whether it gets sudo | week 8 |
| SSH server | install it, and whether to import keys | week 10 |
| package selection / snaps | keep it minimal on a server | week 6 |

Sensible answers for a lab machine: LVM on the whole disk (so the storage
lessons have something to extend), a 2 GB swap, one user with sudo, OpenSSH
installed, nothing else.

At the end the installer asks to reboot. Remove the ISO so it does not
boot the installer again:

```bash
virsh destroy lab01                        # if it hangs at "please remove the installation medium"
virsh change-media lab01 sda --eject --config
virsh start lab01
virsh console lab01
```

## First steps inside the new machine

```bash
sudo apt update && sudo apt upgrade -y
sudo hostnamectl set-hostname lab01
ip a; ip r                                  # did it get an address?
sudo systemctl enable --now ssh
ssh-copy-id ahmad@192.168.122.50            # from the host, so you stop using the console
timedatectl set-timezone Asia/Tashkent
sudo virsh snapshot-create-as lab01 clean "Fresh install"     # from the HOST - your rollback point
```

That snapshot is the point of the exercise: from here you can break the
machine in every lesson of this track and be back in seconds.

## Unattended installs, in one paragraph

Answering the installer by hand does not scale. Every distribution has a
file that answers it for you - Ubuntu's **autoinstall/cloud-init**
(`user-data`), Debian's **preseed**, RHEL's **kickstart**:

```bash
sudo virt-install --name lab02 ... \
  --location /var/lib/libvirt/images/ubuntu-24.04-live-server-amd64.iso \
  --extra-args 'autoinstall ds=nocloud-net;s=http://10.0.0.1/autoinstall/ console=ttyS0'
# RHEL: --extra-args "inst.ks=http://10.0.0.1/ks.cfg console=ttyS0"
```

Same installer, same questions - answered from a file. That is how a
hundred identical machines get built, and it is worth knowing exists even
though the LFCS only asks you to install one.

:::exam-tip
This objective is the practical one: attach the ISO, boot, install, remove
the media, boot the installed system. The exam is far more likely to hand
you a running machine than to make you install one - but the disk-layout
and network questions of the installer are exactly the storage and
networking objectives, so a hand install is good revision.
:::

## Check yourself

1. Which two `virt-install` options attach installation media, and how do
   they differ?
2. How do you reach the installer's screen when the host has no desktop?
3. What is the first thing to do after the install finishes, from the
   host's point of view?
