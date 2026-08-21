## The files behind a user

Before the commands, the three files they edit:

```bash
grep ahmad /etc/passwd
# ahmad:x:1000:1000:Ahmad Maxmudov,,,:/home/ahmad:/bin/bash
#   │   │  │    │          │            │           └── login shell
#   │   │  │    │          │            └── home directory
#   │   │  │    │          └── GECOS: full name and contact fields
#   │   │  │    └── primary GID
#   │   │  └── UID
#   │   └── 'x' = the password is in /etc/shadow
#   └── username
sudo grep ahmad /etc/shadow
# ahmad:$y$j9T$...:20321:0:99999:7:::
#   │        │       │   │   │   └── warn days before expiry
#   │        │       │   │   └── max age (password must change after N days)
#   │        │       │   └── min age
#   │        │       └── last change (days since 1970-01-01)
#   │        └── the hash ($y$ = yescrypt, $6$ = SHA-512); '!' or '*' = login disabled
#   └── username
```

`/etc/passwd` is world-readable (many programs map UIDs to names);
`/etc/shadow` is `640 root:shadow` and holds the hashes.

## Creating users

```bash
sudo useradd -m -s /bin/bash alice            # -m makes the home directory (essential on Debian!)
sudo passwd alice                              # set the password
sudo useradd -m -s /bin/bash -c "Alice Karimova" -G sudo,developers alice
sudo useradd -m -u 1500 -g developers -G docker -d /srv/alice -s /bin/bash alice
sudo useradd -r -s /usr/sbin/nologin -M myapp  # a SYSTEM account: no login, no home
sudo adduser alice                             # Debian's interactive wrapper - asks everything
```

| Flag | Sets |
|---|---|
| `-m` | create the home directory (copying `/etc/skel`) |
| `-M` | do **not** create a home |
| `-d /path` | home directory path |
| `-s /bin/bash` | login shell (`/usr/sbin/nologin` or `/bin/false` to forbid login) |
| `-u 1500` | UID |
| `-g devs` | **primary** group |
| `-G a,b,c` | supplementary groups |
| `-c "Full Name"` | GECOS comment |
| `-e 2026-12-31` | account expiry date |
| `-r` | system account (UID below 1000, no ageing) |
| `-k /etc/skel` | which skeleton directory to copy |

Defaults come from `/etc/default/useradd` and `/etc/login.defs`
(`UID_MIN`, `CREATE_HOME`, `PASS_MAX_DAYS`, `UMASK`):

```bash
useradd -D                       # show defaults
sudo useradd -D -s /bin/bash     # change a default
grep -E "^(UID_MIN|PASS_MAX_DAYS|CREATE_HOME|UMASK)" /etc/login.defs
```

## Modifying

```bash
sudo usermod -s /usr/sbin/nologin alice        # change shell
sudo usermod -aG docker alice                  # ADD to a group - the -a is critical
sudo usermod -G docker alice                   # WITHOUT -a: replaces ALL supplementary groups
sudo usermod -g developers alice               # change the primary group
sudo usermod -l alice_k alice                  # rename the login
sudo usermod -d /srv/alice -m alice            # new home, -m moves the contents
sudo usermod -c "Alice K." alice
sudo usermod -e 2026-12-31 alice               # account expires
sudo usermod -L alice                          # LOCK the password (prefixes the hash with !)
sudo usermod -U alice                          # unlock
sudo usermod -L -e 1 alice                     # lock AND expire - the proper "disable this account"
```

:::warning
`usermod -G` without `-a` silently removes the user from every group not
listed - including `sudo`. It is the single most common way to lock an
administrator out of their own machine. Always `usermod -aG`, and check
with `groups alice` afterwards.
:::

## Passwords and ageing

```bash
sudo passwd alice                # set/change
sudo passwd -l alice             # lock; -u unlock
sudo passwd -d alice             # delete the password (empty login - dangerous)
sudo passwd -e alice             # expire now: must change at next login
sudo passwd -S alice             # status: alice P 08/19/2026 0 99999 7 -1  (P=usable, L=locked, NP=none)
echo 'alice:NewPass123' | sudo chpasswd        # scripted, one or many

sudo chage -l alice              # show ageing settings
sudo chage -M 90 -m 7 -W 14 alice    # max 90 days, min 7 between changes, warn 14 days ahead
sudo chage -E 2026-12-31 alice       # account expiry date
sudo chage -I 30 alice               # inactive: disable N days after the password expires
sudo chage -d 0 alice                # force a change at next login
```

`passwd -l` locks the **password** only (key-based SSH still works);
`chage -E` or `usermod -e` expires the **account** (nothing works). For
"disable this user completely", do both and change the shell to `nologin`.

## Deleting

```bash
sudo userdel alice                # remove the account, KEEP the home directory
sudo userdel -r alice             # remove the home directory and mail spool too
sudo userdel -f alice             # even if logged in
```

Before deleting, find what they own - files elsewhere become "orphaned"
with a bare UID:

```bash
sudo find / -xdev -user alice -ls 2>/dev/null | head
sudo find / -xdev -nouser 2>/dev/null            # files whose owner no longer exists
sudo pkill -u alice                               # end their processes first
```

## Inspecting

```bash
id alice                          # uid, gid, groups
groups alice
getent passwd alice               # works for local AND remote (LDAP) users
getent passwd | wc -l
getent shadow alice
awk -F: '$3>=1000 && $3<65534 {print $1}' /etc/passwd     # the human users
lslogins; lslogins -u
who; w; last alice
sudo pwck; sudo grpck                             # check the files for consistency
```

:::exam-tip
Read the task's words carefully: "create user X **with** home directory"
(`-m`), "**without** login" (`-s /usr/sbin/nologin`), "member of group Y"
(`-G Y` at creation, `-aG Y` after), "password must be changed every 60
days" (`chage -M 60`), "account expires on DATE" (`chage -E DATE` or
`useradd -e`). Verify every one with `id`, `getent passwd`, `chage -l`,
`passwd -S`.
:::

## Check yourself

1. What are the seven fields of a `/etc/passwd` line?
2. Why is `usermod -aG` different from `usermod -G`, and what goes wrong?
3. Which commands lock a password, expire an account, and force a password
   change at next login?
