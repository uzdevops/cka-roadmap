## What the LFCS is

The Linux Foundation Certified System Administrator is a hands-on exam:
two hours at a terminal on a live Linux system, with tasks like "create a
user whose account expires on a date", "make this filesystem mount at
boot", "forward port 8080 to 80", "set up a cron job that runs every
Monday". No multiple choice. You either did it on the machine or you did
not.

It is the Linux half of what this platform's Kubernetes tracks assume.
Every CKA troubleshooting task that ends in `ssh node01; journalctl -u
kubelet` is an LFCS skill; every storage or networking question in any
cloud is one too.

## What this track does

Thirteen weeks, six phases, seventy-nine lessons, each mapped to a line of
the official objectives:

| Phase | Weeks | Domain |
|---|---|---|
| Essential commands | 1-4 | consoles, documentation, files, links, permissions, search, text, regex, archives, redirection, SSL, Git |
| Operations deployment | 5-7 | boot and targets, scripting, systemd services, processes, logs, scheduling, packages, kernel parameters, SELinux, containers, VMs |
| Users and groups | 8 | accounts, groups, environment, limits, sudo, root, LDAP |
| Networking | 9-10 | IPv4/IPv6, services, bridges and bonds, firewalls, NAT, reverse proxies, time, SSH |
| Storage | 11-12 | partitions, swap, filesystems, fstab, mount options, NFS, NBD, LVM, performance, ACLs |
| Exam prep | 13 | four timed mocks and the conclusion |

Each lesson: the concept in a screen or two, the commands you will type,
a table where a table is clearer, a warning where people get burned, and
three questions to answer from memory. Each week ends in a lab on a real
machine and a short quiz.

## How to study it

- **Type every command.** Reading `chmod 2775` is not the same as typing
  it and seeing the `s` appear in `ls -l`. A VM (see week 7) or any Linux
  box you can break is the only equipment needed.
- **Use the man page before the lesson tells you to.** The exam gives you
  `man` and nothing else; the habit of reaching for it is worth more than
  memorising flags.
- **Keep the cheat sheet** (lesson 4 of this week) open and add to it.
- **Do the lab before the quiz**, not after - the quiz checks the lab.

:::tip
If you hold the CKA already, weeks 1-3 will feel familiar and you can move
fast; weeks 5, 7, 10 and 12 are where the new material is (systemd units,
SELinux, NAT, LVM). If you are starting from zero, go in order - later weeks
assume the redirection and permissions of the first three.
:::

## Check yourself

1. What kind of exam is the LFCS, and what does that mean for how you
   should study?
2. Name the five domains and the week numbers that cover each.
3. What one piece of equipment does this track require?
