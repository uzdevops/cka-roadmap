## Primary and supplementary

Every user has exactly one **primary** group (the GID in `/etc/passwd`,
used for files they create) and any number of **supplementary** groups
(listed in `/etc/group`).

```bash
id alice
# uid=1001(alice) gid=1001(alice) groups=1001(alice),27(sudo),1005(developers)
#                   └── primary            └── supplementary
groups alice
getent group developers
# developers:x:1005:alice,bob
```

`/etc/group` fields: `name:x:GID:members`. The primary group's members are
usually **not** listed there - membership comes from `/etc/passwd`'s GID,
which is why `getent group developers` can look empty while users have it
as their primary group.

Debian and RHEL both default to a **user private group**: user `alice` gets
group `alice` as primary, so a default umask of 002 is safe.

## Creating and removing groups

```bash
sudo groupadd developers
sudo groupadd -g 5000 developers        # a specific GID
sudo groupadd -r appgroup               # system group (low GID)
sudo groupmod -n devs developers        # rename
sudo groupmod -g 5001 devs              # change GID (files keep the OLD gid - fix with find -gid)
sudo groupdel devs                      # refuses if it is someone's PRIMARY group
```

## Managing membership

```bash
sudo usermod -aG developers alice       # add (the -a is essential)
sudo gpasswd -a alice developers        # add - clearer intent
sudo gpasswd -d alice developers        # remove
sudo gpasswd -M alice,bob,carol devs    # set the member list exactly
sudo gpasswd -A alice devs              # make alice an administrator of the group
sudo usermod -g developers alice        # change the PRIMARY group
```

A membership change does not affect **existing sessions**: the user's
processes keep the group set they had at login.

```bash
groups                                  # what my shell has
id alice                                # what the files say - these can differ!
newgrp developers                       # start a subshell with the new group active
# or: log out and back in
```

That is the "I added myself to the docker group and still get permission
denied" answer.

## Files and groups

```bash
chgrp developers /srv/project
chgrp -R developers /srv/project
chmod 2775 /srv/project                 # SGID: new files inherit the group (week 2)
find /srv -group olddevs -exec chgrp devs {} +
find / -xdev -nogroup 2>/dev/null       # files whose group no longer exists
```

The pattern for a shared directory, complete:

```bash
sudo groupadd project-x
sudo usermod -aG project-x alice
sudo usermod -aG project-x bob
sudo mkdir -p /srv/project-x
sudo chgrp project-x /srv/project-x
sudo chmod 2770 /srv/project-x          # rwx for owner and group, nothing for others, SGID
ls -ld /srv/project-x                    # drwxrws--- root project-x
```

## Groups that mean something

| Group | Grants |
|---|---|
| `sudo` (Debian) / `wheel` (RHEL) | the right to use `sudo` (via a sudoers rule) |
| `adm` | reading most log files |
| `docker` | full control of the docker daemon - **equivalent to root** |
| `libvirt`, `kvm` | managing virtual machines |
| `dialout`, `plugdev`, `audio`, `video` | serial ports, removable devices, hardware |
| `shadow` | reading `/etc/shadow` |

Adding a user to `docker`, `libvirt` or `sudo` is a privilege decision, not
a convenience one.

## Group passwords, briefly

`/etc/gshadow` can hold a group password so a non-member can `newgrp` into
a group. It is rarely used, and adding the user to the group is almost
always the better answer.

```bash
sudo gpasswd developers        # set a group password
sudo gpasswd -r developers     # remove it
```

## Checking your work

```bash
id alice; groups alice
getent group developers
grep developers /etc/group
awk -F: '$3>=1000 {print $1, $3}' /etc/group      # non-system groups
lslogins -g developers
sudo grpck                                          # consistency check
```

:::exam-tip
"Create group X and add users A and B to it, then make /srv/x writable by
the group": `groupadd X; usermod -aG X A; usermod -aG X B; chgrp X /srv/x;
chmod 2770 /srv/x`. Verify with `getent group X`, `id A` and `ls -ld
/srv/x`. Remember that `groupdel` refuses a primary group and that
membership needs a new login to take effect.
:::

## Check yourself

1. What is the difference between a primary and a supplementary group, and
   where is each recorded?
2. A user was just added to a group but still gets "permission denied".
   Why, and what are the two fixes?
3. Write the commands that make `/srv/team` a shared directory for group
   `team` where new files stay group-owned by `team`.
