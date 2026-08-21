## Finding lines

`grep` prints the lines of its input that match a pattern. It is the
command you will type most often in this track after `ls`.

```bash
grep root /etc/passwd                   # lines containing "root"
grep -i error /var/log/syslog           # case-insensitive
grep -n Listen /etc/apache2/ports.conf  # with line numbers
grep -v '^#' /etc/ssh/sshd_config       # lines NOT matching (invert)
grep -c failed /var/log/auth.log        # count matching lines
grep -r "server_name" /etc/nginx/       # recursive through a directory
grep -rn TODO src/                      # recursive with file:line
grep -l "PermitRootLogin" /etc/ssh/*    # only file names that match
grep -L "PermitRootLogin" /etc/ssh/*    # file names that do NOT match
grep -w cat file                        # whole word only (not "concatenate")
grep -o '[0-9]\+' file                  # print only the matching part, one per line
grep -A3 -B1 "panic" log                # 3 lines after, 1 before; -C2 both
grep -E 'warn|error' log                # extended regex (next two lessons); same as egrep
grep -F '$HOME' file                    # fixed string, no regex (same as fgrep)
grep -e '-x' file; grep -- -x file      # a pattern starting with -
grep -q pattern file && echo found      # quiet: exit status only (0 match, 1 none, 2 error) - for scripts
grep -h pattern *.log                   # no file name prefix
grep -s pattern *                       # no "cannot open" errors
```

## Reading piped input

```bash
ps aux | grep nginx | grep -v grep      # (or: pgrep -a nginx)
journalctl -u sshd | grep -i "failed password"
dmesg | grep -i usb
ss -tulpn | grep :22
env | grep -i proxy
```

## Patterns: what you are really typing

A grep pattern is a **regular expression**, not a glob. `grep *.log file`
does not mean ".log files" - the shell expands `*.log` first, and what
remains is a regex where `.` means "any character". Three rules that save
confusion until the regex lessons:

1. **Quote the pattern** (`'...'`) so the shell does not expand `*`, `$`,
   spaces.
2. `.` matches any character; to match a literal dot, `\.`.
3. `^` anchors the start of a line, `$` the end: `'^root'`, `'bash$'`.

```bash
grep '^root' /etc/passwd                # lines starting with root
grep 'bash$' /etc/passwd                # lines ending with bash
grep '^$' file | wc -l                  # empty lines
grep '192\.168\.1\.' /var/log/syslog    # literal dots
grep -v '^\s*#' /etc/fstab | grep -v '^$'    # strip comments and blanks
```

## Useful combinations

```bash
grep -rl "old.example.com" /etc | xargs sed -i 's/old\.example\.com/new.example.com/g'   # find files then edit
grep -c "" file                                  # count lines (like wc -l)
grep -n . file | tail -1                         # last non-empty line with its number
grep -E -o '\b[0-9]{1,3}(\.[0-9]{1,3}){3}\b' log | sort | uniq -c | sort -rn | head     # IPs by frequency
grep -i "failed password" /var/log/auth.log | awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head   # who is brute-forcing
```

## Exit status

`0` something matched, `1` nothing matched, `2` an error. Scripts and
`&&`/`||` chains rely on it:

```bash
if grep -q '^alice:' /etc/passwd; then echo "alice exists"; fi
grep -q nameserver /etc/resolv.conf || echo "no DNS configured"
```

:::exam-tip
"Save all lines containing X from file Y to file Z" → `grep X Y > Z`;
"count the lines" → `grep -c`; "ignore case" → `-i`; "lines that do not
contain" → `-v`; "search every file under a directory" → `-r`. Quote the
pattern every time. The regex lessons next make the pattern itself
precise.
:::

## Check yourself

1. What do `-v`, `-c`, `-l` and `-o` do?
2. Why should a grep pattern be quoted, and what does `.` mean in one?
3. How do you use grep's exit status in a script?
