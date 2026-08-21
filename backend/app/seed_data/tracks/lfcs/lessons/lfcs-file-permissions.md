## Reading a mode

```bash
ls -l /etc/passwd /etc/shadow /usr/bin/vim
# -rw-r--r-- 1 root root   2941 ... /etc/passwd
# -rw-r----- 1 root shadow 1347 ... /etc/shadow
# -rwxr-xr-x 1 root root 3.1M  ... /usr/bin/vim
```

```
 - rw- r-- r--
 │ │   │   └── other  (everyone else)
 │ │   └────── group  (members of the file's group)
 │ └────────── user   (the owner)
 └──────────── type: - file, d directory, l link, c/b device, p pipe, s socket
```

Each triplet is **r**ead, **w**rite, e**x**ecute. Which triplet applies to
you is decided once, in order: are you the **owner**? then the user bits,
and nothing else. Else, are you in the **group**? then the group bits.
Else, the other bits. (So an owner with `---` and group `rwx` cannot read
their own file - the first match wins.) root ignores r/w and needs only
one `x` somewhere to execute.

| Bit | On a file | On a directory |
|---|---|---|
| `r` | read the contents | **list** the names in it (`ls`) |
| `w` | modify the contents | **create, delete, rename** entries in it (deleting a file is a write to the *directory*, not the file) |
| `x` | run it as a program | **enter** it (`cd`), and reach things inside it by name |

A directory with `r` but not `x`: you can see names but open nothing. With
`x` but not `r`: you can open a file if you already know its name but
cannot list. Both matter for shared directories.

## chmod: symbolic

```bash
chmod u+x script.sh               # add execute for the owner
chmod g-w file                    # remove write for group
chmod o=r file                    # set other to exactly r
chmod a+r file                    # all three (a = ugo)
chmod ug+rw,o-rwx file            # several at once
chmod -R g+rX dir/                # recursive; capital X: execute only on directories and already-executable files
chmod u=rwx,g=rx,o= dir/
```

`+` add, `-` remove, `=` set exactly. `X` is the safe way to make a tree
traversable without making every data file executable.

## chmod: octal

| Value | Bits |
|---|---|
| 4 | r |
| 2 | w |
| 1 | x |

Add per triplet: `rwx`=7, `rw-`=6, `r-x`=5, `r--`=4.

```bash
chmod 644 file        # rw-r--r--   typical file
chmod 600 ~/.ssh/id_ed25519       # rw-------   private key
chmod 755 script.sh   # rwxr-xr-x   executable / typical directory
chmod 750 dir/        # rwxr-x---
chmod 700 ~/.ssh      # rwx------
chmod 664 shared.txt  # rw-rw-r--
```

Four digits (`2775`, `4755`, `1777`) put the special bits first - next
lesson.

## chown and chgrp

```bash
chown alice file                  # owner
chown alice:devs file             # owner and group
chown :devs file                  # group only  (same as chgrp devs file)
chgrp devs file
chown -R alice:devs /srv/project  # recursive
chown --reference=a b             # copy a's owner/group to b
```

Only **root** can change a file's owner; an owner can change the group to
any group **they belong to**.

## umask: the defaults

New files are created with `666 & ~umask`, new directories with `777 &
~umask`. The usual umask `022` gives `644` and `755`; `027` gives `640` and
`750`; `077` gives `600` and `700`.

```bash
umask                 # 0022
umask 027             # this shell, now
# persistently: ~/.bashrc or /etc/profile.d/umask.sh, or /etc/login.defs UMASK
touch f; mkdir d; ls -ld f d
```

## Checking what you did

```bash
ls -l file; stat -c '%A %a %U:%G %n' file       # symbolic and octal at once
namei -l /srv/project/data/file.txt             # permissions of every directory on the path - the "why can't they reach it" tool
id; groups alice                                # which triplet applies to whom
sudo -u alice cat /srv/project/data/file.txt    # test as the user
```

:::warning
Removing `x` from a directory locks everyone out of everything beneath it,
however open the files are - `namei -l` shows the path's weakest link.
And `chmod -R 777` is never the answer; it is how a shared directory
becomes a place where anyone deletes anyone's files (the sticky bit, next
lesson, is the actual fix).
:::

:::exam-tip
Tasks read "make `/srv/data` readable and writable by group `devs`, not
accessible to others": `chgrp -R devs /srv/data; chmod -R 770 /srv/data`
(or `2770` to keep the group on new files - next lesson). Verify with `ls
-ld` and `ls -l` inside. "Only the owner can read the file": `chmod 600`.
:::

## Check yourself

1. A file is `-rw-r-----  root shadow`. Who can read it?
2. What does `w` on a directory allow, and why can a user delete a file
   they cannot write?
3. What permissions does `umask 027` give to new files and directories?
