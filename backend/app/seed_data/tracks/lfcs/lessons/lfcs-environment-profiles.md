## Which file runs when

A shell reads different startup files depending on **how** it started.
Getting this right is the difference between "my PATH works in SSH but not
in cron" and a system where variables are where you expect them.

| Shell type | Started by | Reads (in order) |
|---|---|---|
| **login** | `ssh user@host`, a TTY login, `su -`, `bash -l` | `/etc/profile` → `/etc/profile.d/*.sh` → the first of `~/.bash_profile`, `~/.bash_login`, `~/.profile` |
| **interactive non-login** | opening a terminal in a desktop, `bash` | `/etc/bash.bashrc` → `~/.bashrc` |
| **non-interactive** | a script, cron, `ssh host 'cmd'` | **neither** - only `$BASH_ENV` if set |

That third row is why cron jobs need absolute paths: none of your files
are read.

```bash
shopt -q login_shell && echo "login shell" || echo "not a login shell"
echo $0            # -bash (leading dash) = login shell
```

## The system-wide files

| File | For |
|---|---|
| `/etc/profile` | login shells, system-wide. Do not edit it - it sources the next one |
| `/etc/profile.d/*.sh` | **the place for your system-wide settings**, one file per topic |
| `/etc/bash.bashrc` (Debian) / `/etc/bashrc` (RHEL) | interactive non-login shells: aliases, prompt |
| `/etc/environment` | **not a script**: plain `KEY=value` lines, read by PAM for every login (including graphical and su) |

```bash
cat /etc/environment
# PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
# LANG="en_US.UTF-8"
```

No `export`, no `$VAR` expansion, no shell syntax - PAM reads it literally.
It is the right place for `LANG` and a static `PATH`, and the wrong place
for anything computed.

```bash
sudo tee /etc/profile.d/company.sh <<'EOF'
export EDITOR=vim
export HISTTIMEFORMAT="%F %T "
export PATH="$PATH:/opt/company/bin"
umask 027
EOF
sudo chmod 644 /etc/profile.d/company.sh
```

Changes take effect at the **next login**; test now with `source
/etc/profile.d/company.sh`.

## The per-user files

| File | Read by |
|---|---|
| `~/.bash_profile` or `~/.profile` | login shells |
| `~/.bashrc` | interactive non-login shells - and usually sourced by `~/.profile` too |
| `~/.bash_logout` | at logout |
| `~/.bash_history` | history, written at exit |

The Debian convention: `~/.profile` contains

```bash
if [ -n "$BASH_VERSION" ] && [ -f "$HOME/.bashrc" ]; then . "$HOME/.bashrc"; fi
```

so `~/.bashrc` ends up read in both cases. Put **exports** in `~/.profile`
(inherited by children anyway) and **aliases, prompt, shell options** in
`~/.bashrc` (not inherited, so they must be set in each shell).

## Variables

```bash
VAR=value                   # this shell only
export VAR=value            # this shell AND its children
export PATH="$PATH:/opt/bin"
unset VAR
env | sort | less           # exported variables
set | less                  # all variables and functions
printenv PATH
echo "${EDITOR:-vim}"       # with a default
```

Common ones: `PATH`, `HOME`, `USER`, `SHELL`, `PWD`, `LANG`, `LC_ALL`,
`EDITOR`, `PS1`, `TERM`, `TZ`, `HISTSIZE`, `HISTCONTROL`.

```bash
export PS1='\u@\h:\w\$ '            # user@host:dir$
export HISTSIZE=10000 HISTFILESIZE=20000 HISTCONTROL=ignoredups:erasedups
export TZ=Asia/Tashkent              # per-shell time zone
```

## Locale

```bash
locale                       # current settings
locale -a | head             # available locales
sudo locale-gen en_US.UTF-8  # Debian
sudo update-locale LANG=en_US.UTF-8
localectl status; sudo localectl set-locale LANG=en_US.UTF-8      # systemd, writes /etc/locale.conf
```

Locale changes sorting (`sort`), decimal separators and command messages -
scripts that parse output should set `LC_ALL=C` for stability.

## Applying and debugging

```bash
source ~/.bashrc          # or: . ~/.bashrc  - re-read in the current shell
exec bash -l              # replace the shell with a fresh login shell
bash -x -l -c exit 2>&1 | head -40      # trace which startup files are read
env -i bash --noprofile --norc          # a shell with NOTHING - reproduces cron's environment
ssh localhost 'echo $PATH'              # a non-interactive PATH - often shorter than yours
```

:::warning
A syntax error in `/etc/profile` or `/etc/profile.d/*.sh` can break login
for every user - including root over SSH. Test with `bash -n file` before
saving, keep a second root session open while editing, and prefer a new
file in `profile.d` over editing `/etc/profile` itself.
:::

:::exam-tip
"Set variable X system-wide for all users" → a file in `/etc/profile.d/`
with `export X=...` (or a line in `/etc/environment` for a static value).
"For one user" → `~/.profile`/`~/.bashrc`. Verify by logging in again (or
`su - user -c 'echo $X'`) rather than by `echo $X` in your current shell,
which has not re-read anything.
:::

## Check yourself

1. Which files does a login shell read, and which does a cron job read?
2. What is different about `/etc/environment` compared with
   `/etc/profile.d/*.sh`?
3. Where do aliases belong and why not in `~/.profile`?
