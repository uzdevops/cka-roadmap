## Stopping one user from taking the machine

Limits cap what a process may consume - open files, processes, memory,
CPU time. Without them, one runaway loop or one fork bomb takes the host
down.

## ulimit: the shell's view

```bash
ulimit -a                # every limit for this shell
# core file size          (blocks, -c) 0
# data seg size           (kbytes, -d) unlimited
# open files                      (-n) 1024
# max user processes              (-u) 15678
# virtual memory          (kbytes, -v) unlimited
ulimit -n                # one value
ulimit -Hn               # the HARD limit (the ceiling)
ulimit -Sn               # the SOFT limit (what applies now)
ulimit -n 4096           # raise the soft limit, up to the hard limit - this shell only
ulimit -Hn 8192          # lower the hard limit (root only can raise it)
```

Every limit has a **soft** value (enforced, raisable by the user up to the
hard value) and a **hard** value (the ceiling; only root raises it). A
`ulimit` change lasts for the shell and its children, and dies with it.

| Flag | Limits |
|---|---|
| `-n` | open file descriptors - the one you will actually change |
| `-u` | processes per user - the anti-fork-bomb |
| `-f` | maximum file size a process may create |
| `-c` | core dump size |
| `-v` | virtual memory |
| `-m` | resident memory |
| `-t` | CPU seconds |
| `-s` | stack size |
| `-l` | locked-in memory |

## Persistent limits: /etc/security/limits.conf

Read by PAM's `pam_limits` at **login**, so they apply to login shells,
SSH sessions and su - not to systemd services.

```
# /etc/security/limits.conf   (or a file in /etc/security/limits.d/)
#<domain>   <type>  <item>   <value>
alice        soft   nofile   4096
alice        hard   nofile   8192
@developers  soft   nproc    100
@developers  hard   nproc    200
*            hard   core     0
*            soft   nofile   2048
root         hard   nofile   65536
```

- **domain**: a username, `@group`, `*` (everyone except root), or `%group`
  for a per-group total.
- **type**: `soft`, `hard`, or `-` for both at once.
- **item**: `nofile`, `nproc`, `fsize`, `core`, `memlock`, `cpu`, `as`,
  `maxlogins`, `priority`.

```bash
sudo tee /etc/security/limits.d/90-developers.conf <<'EOF'
@developers  soft  nofile  4096
@developers  hard  nofile  8192
@developers  hard  nproc   200
EOF
```

A separate file in `limits.d/` is preferred over editing `limits.conf`.
The user must **log out and back in**; `ulimit -a` in an existing session
shows the old values.

```bash
grep pam_limits /etc/pam.d/common-session /etc/pam.d/sshd    # confirm PAM applies them
su - alice -c 'ulimit -a'                                     # test as the user
```

## Limits for services: systemd

`limits.conf` does **not** apply to units - systemd starts them directly,
not through a login. Use the unit:

```ini
[Service]
LimitNOFILE=65535
LimitNPROC=512
LimitCORE=0
MemoryMax=2G            # cgroup limits, stronger than rlimits
CPUQuota=50%
TasksMax=4096
```

```bash
sudo systemctl daemon-reload && sudo systemctl restart myapp
systemctl show myapp -p LimitNOFILE -p MemoryMax
cat /proc/$(pgrep -f myapp | head -1)/limits
```

Defaults for all units: `DefaultLimitNOFILE=` in
`/etc/systemd/system.conf`, and `UserTasksMax=` in `logind.conf` for user
sessions.

## System-wide ceilings

```bash
sysctl fs.file-max                    # kernel-wide open files
sysctl kernel.pid_max                 # maximum PIDs
sysctl -w fs.file-max=200000
cat /proc/sys/fs/file-nr              # allocated / free / max, right now
```

A per-user `nofile` above `fs.file-max` cannot be reached - raise both when
tuning a database or a web server.

## Checking a running process

```bash
cat /proc/1234/limits
prlimit --pid 1234                     # readable table
sudo prlimit --pid 1234 --nofile=8192:16384    # change a RUNNING process's limits
ulimit -a
```

That `prlimit` is the answer to "the service needs more file descriptors
and I cannot restart it right now".

:::warning
`nproc` limits count **all** processes of a UID, including SSH sessions -
set it too low and the user cannot log in to fix it. And a `*` domain in
limits.conf does not cover root; a `nofile` that is fine for humans can be
far too small for a database running as its own user, which needs a unit
setting anyway.
:::

:::exam-tip
"Limit user X to N open files / processes" → a line in
`/etc/security/limits.d/*.conf` with both soft and hard, then verify with
`su - X -c 'ulimit -n'` (a fresh login, not your shell). If the task is
about a **service**, the answer is `LimitNOFILE=` in the unit, not
limits.conf.
:::

## Check yourself

1. What is the difference between a soft and a hard limit, and who may
   raise each?
2. Why does `limits.conf` not affect a systemd service, and what does?
3. How do you check the limits of a process that is already running, and
   change them without restarting it?
