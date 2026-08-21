## Tuning a running kernel

Hundreds of kernel settings can be changed while the system runs, through
`/proc/sys`. `sysctl` is the interface to them; the name of a parameter is
its path with slashes turned into dots.

```
/proc/sys/net/ipv4/ip_forward   ⇄   net.ipv4.ip_forward
```

```bash
sysctl -a                                  # every parameter and value (hundreds)
sysctl -a | grep -i forward
sysctl net.ipv4.ip_forward                 # read one
cat /proc/sys/net/ipv4/ip_forward          # the same value, the other way
```

## Changing now (non-persistent)

```bash
sudo sysctl -w net.ipv4.ip_forward=1
sudo sysctl net.ipv4.ip_forward=1                  # -w is optional
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward    # equivalent
sudo sysctl -w vm.swappiness=10
```

These last until reboot. (`sudo echo 1 > /proc/...` fails - the shell opens
the file as you; use `| sudo tee`.)

## Changing persistently

```bash
sudo vi /etc/sysctl.d/99-custom.conf
```

```
net.ipv4.ip_forward = 1
vm.swappiness = 10
net.core.somaxconn = 1024
fs.file-max = 200000
```

```bash
sudo sysctl -p /etc/sysctl.d/99-custom.conf   # apply this file now
sudo sysctl --system                           # re-read ALL sysctl config files, in order
sysctl net.ipv4.ip_forward                     # verify
```

| Location | Purpose |
|---|---|
| `/etc/sysctl.conf` | the traditional single file (still read) |
| `/etc/sysctl.d/*.conf` | **preferred**: drop-ins, read in lexical order - `99-` wins |
| `/usr/lib/sysctl.d/`, `/run/sysctl.d/` | vendor and runtime defaults |

Later files override earlier; a setting in `99-custom.conf` beats a
vendor's `50-default.conf`. Persistent files change nothing until applied
or rebooted - always run `sysctl --system` and then read the value back.

## Parameters worth knowing

| Parameter | Does |
|---|---|
| `net.ipv4.ip_forward` | route packets between interfaces - required for NAT, routers, containers |
| `net.ipv6.conf.all.forwarding` | the IPv6 equivalent |
| `net.ipv4.conf.all.rp_filter` | reverse-path filtering (anti-spoofing) |
| `net.ipv4.icmp_echo_ignore_all` | stop responding to ping |
| `net.ipv4.tcp_syncookies` | SYN-flood protection |
| `net.core.somaxconn` | listen backlog - raise for busy servers |
| `net.ipv4.ip_local_port_range` | ephemeral port range |
| `vm.swappiness` | 0-100: how eagerly to swap (10 on servers with enough RAM) |
| `vm.max_map_count` | memory maps per process - Elasticsearch wants 262144 |
| `vm.overcommit_memory` | memory overcommit policy (Redis asks for 1) |
| `fs.file-max`, `fs.inotify.max_user_watches` | system-wide file handles; inotify watches (IDEs, log shippers) |
| `kernel.pid_max`, `kernel.panic`, `kernel.sysrq` | pid space, panic-then-reboot seconds, SysRq keys |

```bash
sudo sysctl -w net.ipv4.ip_forward=1                 # the classic: turn a host into a router (week 10)
sudo sysctl -w vm.max_map_count=262144
sysctl -a --pattern 'net.ipv4.conf.(all|default).rp_filter'
```

## Kernel modules, briefly

Some parameters only exist once a module is loaded, and modules have their
own options:

```bash
lsmod                                 # loaded modules
modinfo nbd                           # description and parameters
sudo modprobe nbd                     # load
sudo modprobe -r nbd                  # unload
echo nbd | sudo tee /etc/modules-load.d/nbd.conf      # load at boot
echo "options nbd nbds_max=8" | sudo tee /etc/modprobe.d/nbd.conf
cat /sys/module/nbd/parameters/nbds_max
```

## Boot-time kernel parameters

Different thing, same word: **command-line** parameters passed by the boot
loader (`quiet`, `nomodeset`, `systemd.unit=rescue.target`,
`transparent_hugepage=never`).

```bash
cat /proc/cmdline                     # what this boot was given
sudo vi /etc/default/grub             # GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
sudo update-grub                      # Debian/Ubuntu
sudo grub2-mkconfig -o /boot/grub2/grub.cfg    # RHEL
```

Those need a reboot; sysctl values do not.

:::exam-tip
The task is nearly always: "enable IP forwarding **persistently**". That
means both halves - a line in `/etc/sysctl.d/*.conf` **and** applying it
(`sysctl --system` or `sysctl -p`) - then `sysctl net.ipv4.ip_forward` to
show `= 1`. A `sysctl -w` alone loses the mark, because a reboot undoes it.
:::

## Check yourself

1. How does the parameter name `net.ipv4.ip_forward` relate to a path
   under `/proc`?
2. Which two steps make a sysctl change permanent, and how do you verify?
3. What is the difference between a sysctl parameter and a kernel
   command-line parameter?
