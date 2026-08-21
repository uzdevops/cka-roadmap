## /etc/skel: what a new home starts as

When `useradd -m` creates a home directory, it **copies** the contents of
`/etc/skel` into it and chowns everything to the new user. Whatever is in
skel is what every future user begins with.

```bash
ls -la /etc/skel/
# .bash_logout  .bashrc  .profile
sudo useradd -m -s /bin/bash newuser
ls -la /home/newuser/          # the same three files, owned by newuser
```

Only **new** users are affected - existing homes are untouched.

## Customising the template

```bash
sudo cp /etc/skel/.bashrc /etc/skel/.bashrc.orig       # keep a copy of the original

sudo tee -a /etc/skel/.bashrc <<'EOF'

# --- company defaults ---
alias ll='ls -alF'
alias ..='cd ..'
export EDITOR=vim
export HISTTIMEFORMAT="%F %T "
EOF

sudo mkdir -p /etc/skel/.ssh /etc/skel/bin /etc/skel/Documents
sudo chmod 700 /etc/skel/.ssh
sudo tee /etc/skel/.vimrc <<'EOF'
set nu ts=4 sw=4 et ai
syntax on
EOF
sudo tee /etc/skel/README.txt <<'EOF'
Welcome. Company policy: no shared accounts, no passwords in files.
Support: helpdesk@example.com
EOF
```

Permissions are copied with the files, so `chmod 700 /etc/skel/.ssh` in
the template gives every new user a correctly-locked `.ssh`.

Test it:

```bash
sudo useradd -m -s /bin/bash testuser
sudo ls -la /home/testuser
sudo userdel -r testuser
```

## Which skeleton, and where it is configured

```bash
grep SKEL /etc/default/useradd
# SKEL=/etc/skel
grep -E "CREATE_HOME|UMASK|HOME_MODE" /etc/login.defs
sudo useradd -m -k /etc/skel-developers -s /bin/bash dev1     # a different template for this user
```

Several templates - `/etc/skel-developers`, `/etc/skel-contractors` - plus
`-k` is how one machine serves different classes of user.

## Home directory permissions

```bash
grep HOME_MODE /etc/login.defs        # 0750 on many systems; else derived from UMASK
ls -ld /home/*
sudo chmod 750 /home/alice            # others cannot browse it
sudo chmod 700 /home/alice            # nobody but alice (and root)
```

`HOME_MODE` (or `UMASK`) in `/etc/login.defs` decides what `useradd -m`
sets. Default `755` homes mean every user can read every other user's
files - on a shared machine, set `HOME_MODE 0750` before creating accounts.

## Fixing existing users

skel does not reach back in time. To roll a new file out to everyone:

```bash
for h in /home/*; do
    u=$(basename "$h")
    id "$u" &>/dev/null || continue
    sudo cp /etc/skel/.vimrc "$h/.vimrc"
    sudo chown "$u:$u" "$h/.vimrc"
done
```

Or, better, put shared settings in `/etc/profile.d/` and
`/etc/bash.bashrc` (previous lesson) - system-wide files apply to
everyone, now and later, without touching homes at all.

| Put it in | When |
|---|---|
| `/etc/skel` | a **starting point** the user may edit or delete |
| `/etc/profile.d/`, `/etc/bash.bashrc` | a **policy** that should apply to everyone, always |

:::warning
Never put a private SSH key, a token or a password in `/etc/skel` - every
future user gets a copy, and `/etc/skel` itself is world-readable. A public
key in `/etc/skel/.ssh/authorized_keys` is legitimate (an admin's access to
new accounts); a private key never is.
:::

:::exam-tip
"Ensure every newly created user gets file X in their home directory" →
put X in `/etc/skel`, then prove it by creating a test user, listing the
home, and deleting the user with `userdel -r`. If the task says "all
users, including existing ones", skel alone is not enough - copy it out to
the existing homes as well and say so.
:::

## Check yourself

1. When is `/etc/skel` used, and which users does a change to it affect?
2. How would you give developers a different template from other users?
3. Where should a setting live if it must apply to every user including
   existing ones?
