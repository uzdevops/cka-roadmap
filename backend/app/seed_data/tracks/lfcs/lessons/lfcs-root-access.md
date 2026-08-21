## Who may be root

Three questions to answer on any machine: does root have a password, can
root log in directly, and who can become root.

```bash
sudo passwd -S root
# root L 08/19/2026 0 99999 7 -1     ← L = locked (Ubuntu's default)
# root P ...                          ← P = a usable password is set
sudo grep '^root:' /etc/shadow | cut -d: -f2 | head -c3    # ! or * = no login by password
grep PermitRootLogin /etc/ssh/sshd_config
getent group sudo wheel
sudo -l -U alice
```

## Locking and unlocking root

```bash
sudo passwd -l root            # lock the password (prefix the hash with !)
sudo passwd -u root            # unlock
sudo passwd root               # set one
sudo passwd -d root            # delete the password entirely - EMPTY password, do not do this
sudo usermod -s /usr/sbin/nologin root      # forbid root a shell (drastic; breaks rescue and some scripts)
```

Ubuntu ships root **locked**: no password means no `su -`, no console
login as root, and no SSH password login as root. Administration goes
through `sudo`, which logs everything. RHEL sets a root password during
installation.

Locking the password does **not** stop root logins by SSH **key**, and does
not stop `sudo -i`. It closes the password door only.

## Direct root login over SSH

```bash
sudo vi /etc/ssh/sshd_config
```

```
PermitRootLogin no                  # no root logins at all - the usual policy
# PermitRootLogin prohibit-password # keys allowed, passwords not (the OpenSSH default)
# PermitRootLogin forced-commands-only
# PermitRootLogin yes               # avoid
```

```bash
sudo sshd -t                        # syntax check BEFORE reloading
sudo systemctl reload sshd
```

`no` is the policy for anything reachable from a network: root is the one
username every attacker already knows, so brute-force attempts have half
the problem solved. Log in as yourself, then `sudo`.

## Console and single-user access

Physical (or virtual-console) access is a different matter: someone at the
console can boot into `rescue.target` or `init=/bin/bash` and become root
without any password (the operating-modes lesson). If that matters:

```bash
sudo grub2-setpassword                       # RHEL: password-protect GRUB edits
# Debian: set superusers/password_pbkdf2 in /etc/grub.d/40_custom, then update-grub
```

Plus disk encryption, or physical security. Without one of those, "root's
password is locked" protects nothing against someone at the keyboard.

## Which terminals root may use

```bash
cat /etc/securetty         # if present: the ONLY TTYs where root may log in (empty file = none)
```

Modern systems often drop this file; where it exists, emptying it forbids
root console logins entirely - risky without another way in.

## Restricting su

```bash
sudo grep -n pam_wheel /etc/pam.d/su
# auth required pam_wheel.so use_uid           ← uncomment: only wheel/sudo members may `su`
sudo groupadd -r wheel 2>/dev/null; sudo usermod -aG wheel alice
```

Without this, any user who learns root's password can `su -`. With it,
they must also be in the group.

## A sane policy

| Setting | Value | Why |
|---|---|---|
| root password | locked (or long and stored in a vault) | no shared secret to leak |
| `PermitRootLogin` | `no` | attacks target root by name |
| admin access | `sudo` via a group | logged, revocable per person |
| `NOPASSWD` | only for specific automation commands | a stolen session should not be silent root |
| `su` | restricted with `pam_wheel` | defence in depth |
| console/GRUB | password or physical security | otherwise all the above is bypassable |
| audit | `journalctl _COMM=sudo`, `/var/log/auth.log` | who did what, when |

```bash
sudo grep -E "sudo:|su:" /var/log/auth.log | tail
sudo journalctl _COMM=su --since today
last root
sudo lastb | head                    # failed logins - brute force attempts
```

## If you are locked out

Root password lost, no sudo user working: boot with
`systemd.unit=rescue.target` (asks for the root password - useless if it
is unknown) or `init=/bin/bash`, then

```bash
mount -o remount,rw /
passwd root
# or: usermod -aG sudo alice
exec /sbin/init
```

That five-line recipe is also the reason console access is equivalent to
root access.

:::exam-tip
Expect: "prevent root from logging in over SSH" → `PermitRootLogin no` +
`sshd -t` + `systemctl reload sshd`, verified with `ssh root@localhost`
being refused. "Lock the root account" → `passwd -l root`, verified with
`passwd -S root` showing `L`. Do not lock yourself out: confirm your own
sudo works **before** changing root access.
:::

## Check yourself

1. What does `passwd -l root` stop, and what does it not stop?
2. Which sshd_config setting controls direct root login, and what are its
   useful values?
3. Why is console access equivalent to root access unless you take extra
   measures?
