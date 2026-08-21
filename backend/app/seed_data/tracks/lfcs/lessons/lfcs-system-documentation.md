## The only reference you get

On the exam there is no web browser. Everything you cannot remember has to
come from the system's own documentation - and it is all there, if you
know the four places to look.

## man: the manual

```bash
man ls                   # the page for ls
man 5 passwd             # the FILE FORMAT page for /etc/passwd, not the passwd command
man -k "copy files"      # search page names and one-line descriptions (same as apropos)
man -f passwd            # which sections have a page called passwd (same as whatis)
man man                  # the manual about the manual
```

Sections - the number in `ls(1)`, `passwd(5)`:

| # | What | Example |
|---|---|---|
| 1 | user commands | `man 1 ls` |
| 5 | **file formats and configuration files** | `man 5 fstab`, `man 5 crontab`, `man 5 sshd_config`, `man 5 sudoers` |
| 8 | **administration commands** | `man 8 mount`, `man 8 useradd`, `man 8 systemctl` |
| 2, 3 | system calls, library functions | for programmers |
| 4 | devices | `man 4 null` |
| 7 | overviews and conventions | `man 7 signal`, `man 7 regex`, `man 7 hier` |

When a name exists in several sections (`passwd` in 1 and 5; `crontab` in
1 and 5), `man name` shows the lowest; give the number for the other.

Inside a page (it opens in `less`): `/pattern` searches, `n` next match,
`N` previous, `g`/`G` top/bottom, `q` quits, `h` help. The layout is
always NAME, SYNOPSIS, DESCRIPTION, OPTIONS, then FILES, EXAMPLES, SEE
ALSO - jump to EXAMPLES with `/^EXAMPLES`.

```bash
man -k ^lv               # every LVM command's page
man 5 fstab | grep -A3 "fourth field"
mandb                    # rebuild the index if man -k finds nothing after installing a package
```

## --help and help

```bash
ls --help | less         # most GNU commands: a usage summary, faster than man for a flag
tar --help | grep -- -z
help cd                  # bash BUILTINS (cd, export, alias, ulimit...) have no man page of their own; `help` is theirs
help -m ulimit           # or `man bash` and search for the builtin
type cd                  # "cd is a shell builtin" - that is how you know to use help
```

## info

```bash
info coreutils           # the GNU manuals: longer, with chapters and examples
info ls
```

Navigation: `n`/`p` next/previous node, `u` up, `Enter` on a link, `q`.
Less used than `man`, but some GNU tools (coreutils, grep, sed, bash) have
their fullest documentation here.

## /usr/share/doc

```bash
ls /usr/share/doc/nginx/
zcat /usr/share/doc/nginx/README.Debian.gz
ls /usr/share/doc/sudo/examples/
```

Per-package READMEs, changelogs, and often **example configuration files**
- the place to find a sample `chrony.conf` or a sudoers snippet when the
man page is dense.

## Which to reach for

| Question | Reach for |
|---|---|
| "what flag does X?" | `X --help`, then `man X` |
| "what goes in this config file?" | `man 5 file` |
| "which command does Y?" | `man -k Y` / `apropos Y` |
| "how do I use this shell builtin?" | `help builtin` |
| "is there an example config?" | `/usr/share/doc/pkg/` |
| "what are the signal numbers / regex rules / directory layout?" | `man 7 signal`, `man 7 regex`, `man 7 hier` |

:::exam-tip
Practise the reflex now, not in the exam: every lesson from here on names
the man page for its commands. Open it, find the flag the lesson used, read
one paragraph around it. After twelve weeks, `man 5 fstab` and a `/` search
will be faster than any memory.
:::

## Check yourself

1. What is the difference between `man passwd` and `man 5 passwd`?
2. Why does `man cd` fail, and what do you use instead?
3. Which command finds the manual page when you know what a tool does but
   not its name?
