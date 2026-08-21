## The five domains and their weights

The exam's task list is drawn from five domains. The weights decide how
many tasks each gets - and therefore where your study hours go.

| Domain | Weight | This track |
|---|---|---|
| **Operations Deployment** | **25%** | weeks 5-7 |
| **Networking** | **25%** | weeks 9-10 |
| **Storage** | **20%** | weeks 11-12 |
| **Essential Commands** | **20%** | weeks 1-4 |
| **Users and Groups** | **10%** | week 8 |

(Weights from the current Linux Foundation domain list; confirm against the
exam page when you book - they are revised every year or two.)

Half the exam is operations and networking. Those are also the domains
where the tasks are longest - a systemd unit, a firewall rule set, a
bonded interface - so the time you spend there pays twice.

## Module by module

**Essential Commands (weeks 1-4)** - the things everyone thinks they
know: logging in, `man`, files and links, permissions including SUID/SGID/
sticky, `find`, the text tools (`sort`, `cut`, `sed`, `tr`), `grep` with
basic and extended regular expressions, `tar` and the compressors,
redirection and pipes, reading and making certificates with `openssl`,
and Git basics. Everyone "knows" these; the exam checks whether you can do
them fast and exactly.

**Operations Deployment (weeks 5-7)** - the system as a running thing:
booting, targets, shutting down without losing data; writing shell
scripts; `systemctl` and **writing a unit file**; processes and signals;
`journalctl` and `/var/log`; `cron`, `at` and timers; packages and
repositories; compiling from source; checking integrity and resources;
`sysctl`; **SELinux** contexts and booleans; containers with podman/docker;
VMs with libvirt.

**Users and Groups (week 8)** - `useradd` and friends and the files behind
them, groups, `/etc/skel`, profiles, `ulimit` and `limits.conf`, `sudo`
and `visudo`, root access policy, and pointing a host at LDAP.

**Networking (weeks 9-10)** - addressing and resolution with `nmcli` and
netplan, checking services with `ss`, bridges and bonds, **firewalld and
nftables**, **NAT and port forwarding**, nginx as reverse proxy and load
balancer, `chrony`, and `sshd` hardening with keys.

**Storage (weeks 11-12)** - partitions with `fdisk`/`parted`, swap,
`mkfs`, **`/etc/fstab`**, mount options, NFS server and client, NBD,
**LVM** create/extend/reduce, `iostat`/`iotop`, and ACLs with `setfacl`.

**Exam prep (week 13)** - four mocks and the conclusion.

## The shape of a task

Most tasks are two or three commands plus a verification, phrased like
the objectives: "Create a 2 GiB logical volume named `data` in volume group
`vg0`, format it ext4 and mount it persistently at `/mnt/data`." Each
bold word is a step and a point of failure. The mocks in week 13 are
written in exactly this voice so it stops sounding like a foreign
language.

:::exam-tip
Read the weights once more: a perfect Users and Groups score is 10% of the
exam; a perfect Operations Deployment score is 25%. The pass mark is around
two-thirds. You can afford to be weak in one small domain; you cannot
afford to be weak in operations or networking.
:::

## Check yourself

1. Which two domains together make up half the exam?
2. Which week covers systemd unit files, and which covers LVM?
3. Take the task "Create a 2 GiB logical volume... mount it persistently":
   list the steps it hides.
