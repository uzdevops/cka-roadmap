## Three bits beyond rwx

The fourth octal digit. Each bit means one thing on files and another on
directories, and two of them are visible in `ls -l` as an `s` or `t` where
an `x` would be.

| Bit | Octal | On an executable file | On a directory |
|---|---|---|---|
| **SUID** (set-user-ID) | `4000` | runs **as the file's owner**, whatever user started it | nothing (ignored on Linux) |
| **SGID** (set-group-ID) | `2000` | runs **as the file's group** | new files and subdirectories **inherit the directory's group** (and subdirs inherit SGID) |
| **sticky** | `1000` | nothing (historical) | only a file's **owner** (or the directory's owner, or root) may delete or rename it |

## SUID: passwd is the example

```bash
ls -l /usr/bin/passwd
# -rwsr-xr-x 1 root root 68208 ... /usr/bin/passwd
```

`/etc/shadow` is `rw-r-----` root. An ordinary user cannot write it, yet
`passwd` lets them change their own password - because `passwd` is SUID
root: the **process runs with root's effective UID** regardless of who
started it. The `s` in the owner's `x` slot is the bit.

```bash
chmod u+s file      # or chmod 4755 file
ls -l file          # -rwsr-xr-x
```

A capital **`S`** means the bit is set but the execute bit under it is
not - meaningless, usually a mistake (`chmod 4644`).

SUID binaries are the classic privilege-escalation surface: one that can
be made to spawn a shell gives root. Audit them:

```bash
find / -perm -4000 -type f 2>/dev/null           # every SUID file
find / -perm -2000 -type f 2>/dev/null           # SGID files
find / -perm /6000 -type f 2>/dev/null           # either
```

(`-perm -4000` = "has at least these bits"; `-perm /6000` = "any of".)

## SGID on a directory: shared project folders

```bash
mkdir /srv/project; chgrp devs /srv/project; chmod 2775 /srv/project
ls -ld /srv/project
# drwxrwsr-x 2 root devs 4096 ... /srv/project
touch /srv/project/a; ls -l /srv/project/a
# -rw-rw-r-- 1 ahmad devs ...              <- group devs, not ahmad's primary group
```

Without SGID, a file alice creates gets alice's primary group and bob
cannot write it. With SGID, every file gets `devs`, and (with a umask of
`002`) the group can edit each other's work. This is the **standard
answer** to "a directory shared by a group".

SGID on an **executable** makes it run with the file's group - rarer, but
e.g. `/usr/bin/wall` is SGID `tty` so it can write to everyone's terminal.

## Sticky: /tmp

```bash
ls -ld /tmp
# drwxrwxrwt 10 root root 4096 ... /tmp
```

`/tmp` is world-writable (`777`) - anyone can create files - but the `t`
means you can delete **only your own**. Without it, `777` would let any
user delete any other user's temp files.

```bash
chmod +t /srv/dropbox      # or chmod 1777
ls -ld /srv/dropbox        # drwxrwxrwt
```

Capital **`T`**: sticky set, but `x` missing for other - again usually a
mistake.

## Reading the four digits

| Mode | Meaning |
|---|---|
| `4755` | SUID, `rwxr-xr-x` - a SUID root program |
| `2775` | SGID, `rwxrwxr-x` - a group project directory |
| `1777` | sticky, `rwxrwxrwx` - a shared temp directory |
| `3775` | SGID + sticky - group-shared and delete-your-own-only |
| `6755` | SUID + SGID on an executable |

Symbolic: `u+s`, `g+s`, `+t`; remove with `u-s`, `g-s`, `-t`.

:::exam-tip
"Create a directory shared by group X where files created inside belong to
X" → `chmod 2770` (or `2775`) after `chgrp X`; verify by creating a file
and reading its group. "Users may create but only delete their own files"
→ `chmod 1777`. "Find all SUID files and save the list" → `find / -perm
-4000 -type f > file`. The `s`/`t` in `ls -l` is your verification.
:::

## Check yourself

1. Why can an ordinary user change their password although `/etc/shadow`
   is not writable by them?
2. What does SGID do on a directory, and what problem does it solve?
3. What does `drwxrwxrwt` tell you about who can delete a file in the
   directory?
