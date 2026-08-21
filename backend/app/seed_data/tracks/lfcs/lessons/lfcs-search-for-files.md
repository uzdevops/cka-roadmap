## find: walk the tree and test each entry

```bash
find [where] [tests] [actions]
find /var/log -name "*.log"                 # by name (glob, quoted so the shell does not expand it)
find . -iname "readme*"                     # case-insensitive
find / -type d -name "conf*" 2>/dev/null    # directories only; discard permission errors
```

No starting path means `.`; no action means `-print`. Tests are joined
with AND by default; `-o` is OR; `!` or `-not` negates; `\( \)` groups.

## Tests you will use

| Test | Matches |
|---|---|
| `-name "*.conf"`, `-iname` | basename glob (quote it) |
| `-path "*/log/*"` | the whole path |
| `-type f` / `d` / `l` / `b` / `c` / `s` | file, dir, symlink, block, char, socket |
| `-size +1M`, `-size -10k`, `-size 100c` | larger than, smaller than, exactly; units `c` bytes `k` `M` `G` (a bare number = 512-byte blocks) |
| `-empty` | empty file or directory |
| `-user alice`, `-group devs`, `-uid 1001`, `-nouser` | ownership (`-nouser`: owner no longer exists) |
| `-perm 644` | **exactly** 644 |
| `-perm -644` | **at least** these bits (all of them set) |
| `-perm /222` | **any** of these bits (writable by anyone) |
| `-perm -4000`, `-perm -2000`, `-perm -o+w` | SUID, SGID, other-writable |
| `-mtime -7`, `-mtime +30`, `-mtime 0` | modified less than 7 days ago / more than 30 / today |
| `-mmin -60` | modified in the last 60 minutes |
| `-atime`, `-ctime`, `-amin`, `-cmin` | access, inode-change |
| `-newer ref.txt`, `-newermt "2026-08-01"` | modified after a file / a date |
| `-links +1`, `-samefile f`, `-inum N` | hard links |
| `-maxdepth 1`, `-mindepth 2` | how deep (these go **first**, before tests) |
| `-xdev` / `-mount` | stay on one filesystem |
| `-readable`, `-writable`, `-executable` | by the current user |

```bash
find /home -type f -size +100M
find /etc -type f -mtime -1                          # changed in the last day
find / -type f -perm -4000 2>/dev/null               # SUID
find /var -type f -perm /o+w ! -type l 2>/dev/null   # world-writable files
find /srv -user alice -o -group devs
find . \( -name "*.tmp" -o -name "*.bak" \) -type f
find /var/log -name "*.log" -size +10M -mtime +7
find / -maxdepth 2 -type d -name "*conf*"
find /data -type f -newermt "2026-08-01" ! -newermt "2026-08-15"
```

## Actions: do something with each match

| Action | Does |
|---|---|
| `-print` | the default |
| `-ls` | `ls -l`-style line |
| `-delete` | delete (put it **last**; test with `-print` first) |
| `-exec cmd {} \;` | run cmd once **per file**; `{}` is the name |
| `-exec cmd {} +` | run cmd once with **many files** (faster, like xargs) |
| `-ok cmd {} \;` | like `-exec` but asks |
| `-printf "%s %p\n"` | custom output: `%p` path, `%s` size, `%u` user, `%m` mode, `%TY-%Tm-%Td` mtime |

```bash
find /var/log -name "*.gz" -mtime +30 -delete
find /srv -type f -name "*.sh" -exec chmod +x {} \;
find /srv -type d -exec chmod 2775 {} +
find /home -user olduser -exec chown newuser:newuser {} +
find . -name "*.log" -exec grep -l ERROR {} +
find /etc -name "*.conf" -exec cp {} /backup/etc/ \;
find /tmp -type f -atime +10 -ok rm {} \;
find / -perm -4000 -type f -printf "%m %u %p\n" 2>/dev/null
find /var -size +50M -printf "%s %p\n" | sort -n | tail
```

`{}` is replaced by each path; `\;` ends the command (escaped so the
shell does not eat it); `+` batches. With `-exec ... +`, `{}` must be last.

## find with xargs

```bash
find . -name "*.txt" -print0 | xargs -0 grep -l "TODO"      # -print0/-0 handle spaces and newlines in names
find /var/log -name "*.log" | xargs ls -lS | head
```

`-exec ... +` does the same job without the pipe; use whichever you
remember under pressure.

## locate: the indexed search

```bash
sudo updatedb                 # build/refresh the database (a cron job does it daily)
locate sshd_config            # instant, substring match on the full path
locate -i readme | head
locate -c "*.conf"
```

Fast, but only as fresh as the last `updatedb`, and it does not know about
files created since. `find` is authoritative; `locate` is a convenience.

## Other "where is it" commands

```bash
which nginx                   # the executable on PATH
whereis nginx                 # binary, sources, man page
type ls                       # alias, builtin, or file
```

:::exam-tip
Exam tasks read exactly like `find` syntax: "find all files under /var
larger than 10 MB owned by root and save the list to /root/big.txt" →
`find /var -type f -size +10M -user root > /root/big.txt 2>/dev/null`.
Always `2>/dev/null` (permission noise) when not root, `-type f` when
they say "files", and `-delete`/`-exec` only after seeing the `-print`
list once.
:::

## Check yourself

1. What is the difference between `-perm 644`, `-perm -644` and `-perm
   /644`?
2. Write the command that finds `.log` files under `/var/log` modified
   more than 7 days ago and deletes them.
3. When is `-exec cmd {} +` preferable to `-exec cmd {} \;`?
