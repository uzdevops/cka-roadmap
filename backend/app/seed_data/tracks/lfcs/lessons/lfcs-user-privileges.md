## sudo: root, one command at a time

`sudo` runs a command as another user (root by default) according to rules
in `/etc/sudoers`. It logs every use, needs the **invoking user's** own
password, and can be scoped down to a single binary - which is why it
replaced sharing the root password.

```bash
sudo apt update                    # as root
sudo -u postgres psql              # as another user
sudo -i                            # a root LOGIN shell (root's environment, root's home)
sudo -s                            # a root shell keeping your environment
sudo -l                            # what am I allowed to run?
sudo -l -U alice                   # what is alice allowed to run?
sudo -k                            # forget the cached credentials now
sudo -v                            # refresh the timestamp
sudo !!                            # rerun the previous command with sudo (bash history)
```

## Editing the rules: visudo, always

```bash
sudo visudo                                    # edits /etc/sudoers with a SYNTAX CHECK on save
sudo visudo -f /etc/sudoers.d/developers       # a drop-in file, the preferred place
sudo visudo -c                                 # check the whole configuration
```

:::warning
Never edit `/etc/sudoers` with a plain editor. A syntax error makes `sudo`
refuse to run **at all**, and if root has no password (Ubuntu's default)
you are locked out of administration entirely - recovery then means a
rescue boot. `visudo` refuses to save a broken file, which is its entire
purpose. Keep a second root shell open while you edit.
:::

## The rule syntax

```
user    host = (runas_user:runas_group)  NOPASSWD:  command
alice   ALL  = (ALL:ALL)                            ALL
%sudo   ALL  = (ALL:ALL)                            ALL
%wheel  ALL  = (ALL)                     NOPASSWD:  ALL
bob     ALL  = (root)                               /usr/bin/systemctl restart nginx
carol   ALL  = (root)                    NOPASSWD:  /usr/bin/apt update, /usr/bin/apt upgrade
deploy  ALL  = (www-data)                           /usr/local/bin/deploy.sh
```

| Field | Means |
|---|---|
| user / `%group` | who the rule is for |
| host | which host (`ALL` - the field matters only for a shared sudoers file) |
| `(runas)` | which identity they may become |
| `NOPASSWD:` | do not ask for a password (use sparingly) |
| command | absolute paths, comma-separated; `ALL` = anything |

Aliases keep long files readable:

```
User_Alias  ADMINS = alice, bob
Cmnd_Alias  SERVICES = /usr/bin/systemctl start *, /usr/bin/systemctl stop *, /usr/bin/systemctl restart *
Cmnd_Alias  PKG = /usr/bin/apt, /usr/bin/apt-get
ADMINS  ALL = (ALL) SERVICES, PKG
```

Defaults worth knowing:

```
Defaults    env_reset                       # start from a clean environment
Defaults    secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Defaults    timestamp_timeout=15            # minutes before asking again (0 = every time)
Defaults    logfile="/var/log/sudo.log"
Defaults:alice  !authenticate               # alice is never asked (equivalent to NOPASSWD for all her rules)
Defaults    requiretty                      # refuse sudo without a terminal (blocks some scripts)
```

## Granting admin rights, the normal way

```bash
sudo usermod -aG sudo alice            # Debian/Ubuntu: the sudo group has a rule in /etc/sudoers
sudo usermod -aG wheel alice           # RHEL family
groups alice                            # confirm
sudo -l -U alice
```

Adding to the group is right when the group already has the rule; write a
rule only when you need something narrower.

## Narrow grants: the point of sudo

```bash
sudo visudo -f /etc/sudoers.d/webops
```

```
%webops  ALL = (root) NOPASSWD: /usr/bin/systemctl restart nginx, /usr/bin/systemctl status nginx, /usr/bin/nginx -t
```

```bash
sudo chmod 440 /etc/sudoers.d/webops       # sudoers files must not be group/world writable
sudo visudo -c
```

Rules to keep such a grant from becoming full root:

- **Absolute paths only**; a bare `systemctl` would match anything on PATH.
- **No wildcards that swallow arguments**: `/usr/bin/systemctl restart *`
  also permits `restart -- ; bash`-style tricks in some shells; prefer
  exact commands.
- **Never grant an editor, a shell, or anything with a shell escape**:
  `vi`, `less`, `find`, `awk`, `python`, `tar`, `git` under sudo all give
  root. (`sudoedit` / `sudo -e file` exists precisely to edit files safely.)
- `NOPASSWD` only where a script genuinely needs it.

## su, and the difference

```bash
su - alice              # a LOGIN shell as alice: her environment, her home  (needs ALICE's password)
su alice                # her identity, YOUR environment - almost always wrong
su -                    # root login shell (needs ROOT's password)
sudo su -               # root login shell via sudo (needs YOUR password) - works where root has no password
sudo -i                 # the same thing, more directly - prefer this
exit
```

`su` needs the target's password; `sudo` needs yours and is logged and
scoped. That is why `sudo` is the standard and root's password is often
left unset.

## Auditing

```bash
sudo grep sudo /var/log/auth.log | tail          # Debian
sudo journalctl _COMM=sudo --since today
sudo grep -i "NOT in the sudoers file" /var/log/auth.log      # attempted misuse
sudo -l -U alice
sudo journalctl -u sudo
```

```
Aug 19 10:22:01 web01 sudo: alice : TTY=pts/0 ; PWD=/home/alice ; USER=root ; COMMAND=/usr/bin/systemctl restart nginx
```

Every sudo invocation leaves that line - the reason sudo is preferable to a
shared root password even when the grant is `ALL`.

:::exam-tip
Two shapes appear: "give user X full sudo" → `usermod -aG sudo X`; "allow
group Y to run only command Z without a password" → a file in
`/etc/sudoers.d/` with `%Y ALL=(root) NOPASSWD: /full/path/Z`, mode 440,
created with `visudo -f`. Verify with `sudo -l -U X` and by running the
command as that user (`sudo -u X sudo -n /full/path/Z`).
:::

## Check yourself

1. Why must sudoers files be edited with `visudo`, and what happens if
   they are not?
2. What is the difference between `su -`, `su`, and `sudo -i`, and whose
   password does each need?
3. Why is granting `sudo vi` effectively granting full root?
