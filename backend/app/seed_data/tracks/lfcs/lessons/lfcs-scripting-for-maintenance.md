## A script is a file of commands

Anything you type twice belongs in a script. The LFCS asks for shell
scripts that automate maintenance: back something up, check something,
clean something, report something.

```bash
#!/bin/bash
# backup-etc.sh - archive /etc daily and keep 7 copies
set -euo pipefail

DEST=/backup
KEEP=7
STAMP=$(date +%F)

mkdir -p "$DEST"
tar -czf "$DEST/etc-$STAMP.tar.gz" -C / etc
find "$DEST" -name 'etc-*.tar.gz' -mtime +$KEEP -delete
echo "backup written: $DEST/etc-$STAMP.tar.gz"
```

```bash
chmod +x backup-etc.sh
./backup-etc.sh
bash -n backup-etc.sh        # syntax check without running
bash -x backup-etc.sh        # trace every command as it runs
```

**Shebang** `#!/bin/bash` tells the kernel which interpreter to use; it
must be the first line. `set -e` exit on any error, `-u` error on an
undefined variable, `-o pipefail` make a pipeline fail if any part does -
three flags that turn silent breakage into a stopped script.

## Variables and quoting

```bash
name="web01"
count=5
path="/var/log/$name"
echo "Host: $name has $count logs in ${path}"
today=$(date +%F)                   # command substitution
files=$(ls /etc | wc -l)
readonly MAX=100
unset name
```

Rules that prevent most bugs: **no spaces around `=`**; `"$var"` in double
quotes almost always (a path with a space breaks everything otherwise);
`${var}` when the name touches other characters; `'single quotes'` for
literal text.

```bash
"${1:-default}"     # first argument, or "default" if unset
"${var:?must be set}"   # error out with a message if empty
"${#var}"           # length
"${var%.txt}"       # strip a suffix;  ${var#*/} strips a prefix
"${var/old/new}"    # replace
```

## Arguments and environment

```bash
$0        # the script's name
$1 $2 …   # positional arguments
$#        # how many
$@        # all of them, individually quoted: "$@"
$?        # exit status of the last command
$$        # this script's PID
```

```bash
if [ $# -lt 1 ]; then
    echo "usage: $0 <directory>" >&2
    exit 1
fi
DIR=$1
```

## Conditionals

```bash
if [ -f /etc/fstab ]; then
    echo "exists"
elif [ -d /etc/fstab ]; then
    echo "it is a directory"
else
    echo "missing"
fi

[[ -f $file ]] && echo "found"           # bash's [[ ]]: no word-splitting, supports =~ and &&
systemctl is-active --quiet nginx || systemctl start nginx
```

| Test | True when |
|---|---|
| `-f f` / `-d d` / `-e p` | regular file / directory / exists |
| `-r -w -x` | readable / writable / executable |
| `-s f` | file is non-empty |
| `-z "$s"` / `-n "$s"` | string empty / non-empty |
| `"$a" = "$b"` / `!=` | string equality |
| `$a -eq -ne -lt -le -gt -ge $b` | numeric comparison |
| `[[ $s =~ ^[0-9]+$ ]]` | regex match (bash) |

```bash
case "$1" in
    start)   echo "starting" ;;
    stop)    echo "stopping" ;;
    restart) $0 stop; $0 start ;;
    *)       echo "usage: $0 {start|stop|restart}" >&2; exit 1 ;;
esac
```

## Loops

```bash
for f in /var/log/*.log; do
    gzip -k "$f"
done

for i in {1..5}; do echo "host$i"; done
for u in $(cut -d: -f1 /etc/passwd); do echo "$u"; done

while read -r line; do
    echo "line: $line"
done < /etc/fstab

while ! ping -c1 -W1 10.0.0.5 >/dev/null 2>&1; do
    echo "waiting for host..."; sleep 5
done

until systemctl is-active --quiet nginx; do sleep 1; done

for pid in $(pgrep old-daemon); do kill "$pid"; done
```

`break` leaves a loop, `continue` skips to the next iteration.

## Functions and exit codes

```bash
log() { echo "[$(date +%T)] $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

check_disk() {
    local threshold=${1:-90}
    local used
    used=$(df --output=pcent / | tail -1 | tr -dc '0-9')
    (( used > threshold )) && return 1
    return 0
}

check_disk 85 || die "root filesystem above 85%"
log "disk ok"
exit 0
```

Exit `0` means success; anything else is failure, and that is what `cron`,
systemd and `&&`/`||` read.

## Maintenance patterns

```bash
# rotate and clean
find /var/log/myapp -name '*.log' -mtime +14 -delete

# a service watchdog
systemctl is-active --quiet myapp || { systemctl restart myapp; log "restarted myapp"; }

# report to a file, quietly, from cron
{ df -h; echo; free -h; echo; systemctl --failed; } > /var/log/healthcheck.log 2>&1

# do not run twice at once
exec 9>/var/lock/mytask.lock
flock -n 9 || exit 0

# clean up on exit, even on error
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
```

:::warning
In cron, `PATH` is minimal and `$HOME` may differ - use absolute paths for
commands and files, or set `PATH` at the top of the script. A script that
works in your shell and silently fails in cron is almost always this
(week 6 returns to it).
:::

:::exam-tip
A scripting task will be small: "write a script at /usr/local/bin/x that
takes a directory as an argument and prints the number of files in it,
exiting 1 if the directory does not exist". Shebang, argument check,
`[ -d "$1" ] || exit 1`, the work, `chmod +x`. Test it with a good and a
bad argument and check `echo $?` both times.
:::

## Check yourself

1. What do `set -e`, `set -u` and `set -o pipefail` do?
2. Why should variables be quoted as `"$var"`?
3. Write a loop that gzips every `.log` file in `/var/log/app`.
