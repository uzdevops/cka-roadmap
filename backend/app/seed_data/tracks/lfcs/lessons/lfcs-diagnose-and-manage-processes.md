## Seeing what runs

```bash
ps aux                       # BSD style: every process, with %CPU, %MEM, START, TIME, COMMAND
ps -ef                       # System V style: UID, PID, PPID, C, STIME, TTY, TIME, CMD
ps -ef --forest              # the parent/child tree
ps aux --sort=-%mem | head   # biggest memory users
ps aux --sort=-%cpu | head
ps -u ahmad                  # one user's
ps -p 1234 -o pid,ppid,user,stat,etime,cmd
ps -eo pid,ppid,user,pri,ni,stat,%cpu,%mem,etime,cmd --sort=-%cpu | head
pgrep -a nginx               # PIDs (and command lines) by name - better than ps|grep
pgrep -u ahmad -l
pidof sshd
pstree -p                    # the tree, compactly
```

The **STAT** column: `R` running, `S` sleeping (interruptible), `D`
uninterruptible sleep (usually blocked on I/O - a `D` process cannot even
be killed), `T` stopped, `Z` zombie (finished, parent has not reaped it),
plus `s` session leader, `+` foreground, `<` high priority, `N` low.

## Live views

```bash
top                          # interactive
# inside top: P sort by CPU, M by memory, k kill, r renice, u filter by user, 1 per-CPU, h help, q quit
htop                         # nicer, if installed
uptime                       # load average: 1, 5, 15 minutes
vmstat 1 5                   # CPU/memory/IO snapshots
free -h                      # memory; the "available" column is the one that matters
```

Load average is the number of processes running **or waiting for I/O**;
compare it to the CPU count (`nproc`). 4.0 on 4 CPUs is fully busy; 4.0 on
1 CPU is a queue.

## Signals

```bash
kill 1234                    # SIGTERM (15): "please stop" - the default and the polite one
kill -15 1234
kill -9 1234                 # SIGKILL: the kernel kills it; NO cleanup, unsaved data lost
kill -HUP 1234               # many daemons re-read their config on SIGHUP
kill -l                      # every signal name and number
killall nginx                # by exact name
killall -u ahmad             # everything of a user
pkill -f "python.*worker"    # by full command-line pattern
pkill -HUP -x sshd
```

| Signal | # | Means |
|---|---|---|
| `SIGTERM` | 15 | terminate politely (catchable) - **always try this first** |
| `SIGKILL` | 9 | kill immediately (uncatchable) |
| `SIGHUP` | 1 | hang-up; by convention "reload config" for daemons |
| `SIGINT` | 2 | Ctrl-C |
| `SIGSTOP` / `SIGCONT` | 19/18 | pause / resume |
| `SIGQUIT` | 3 | quit with core dump |

A process in `D` state ignores even SIGKILL until its I/O finishes; a
**zombie** (`Z`) is already dead - you cannot kill it, you restart or fix
its parent.

## Priorities: nice and renice

Niceness runs from **-20 (most favoured)** to **19 (least)**; default 0.
Only root may lower it (make a process more important).

```bash
nice -n 10 tar -czf backup.tar.gz /data      # start a job politely
nice -n -5 ./important                        # root only
renice -n 5 -p 1234                           # change a running process
renice -n 10 -u batchuser                     # all of a user's
ps -eo pid,ni,cmd | grep tar
ionice -c3 -p 1234                            # I/O priority: idle class - for backups
```

## Foreground, background, and surviving logout

```bash
long-job &                   # start in the background
jobs                         # this shell's jobs: [1]+ Running
fg %1                        # bring to the foreground
bg %1                        # resume a stopped job in the background
# Ctrl-Z  suspends the foreground job (SIGTSTP), then bg or fg
kill %1                      # by job number
nohup long-job > job.log 2>&1 &     # immune to SIGHUP: survives logout
disown -h %1                        # detach an already-running job from the shell
setsid long-job                     # new session, fully detached
tmux new -s work                    # the practical answer for remote work
```

Closing a terminal sends SIGHUP to its jobs; `nohup`, `disown`, `setsid`
or a multiplexer are the four ways to survive it.

## Finding the culprit

```bash
ps aux --sort=-%cpu | head -5
top -b -n1 | head -20                     # batch mode, for scripts and logs
lsof -p 1234                              # every file/socket the process has open
lsof /var/log/app.log                     # which process holds this file
lsof -i :8080                             # who listens on a port (also: ss -tulpn)
fuser -v /mnt/data                        # who is using a mount point (before unmounting)
fuser -km /mnt/data                       # kill them (careful)
strace -p 1234                            # syscalls, live
cat /proc/1234/status; cat /proc/1234/limits; ls -l /proc/1234/cwd /proc/1234/exe
```

## Resource limits, per process

```bash
ulimit -a                    # current shell's limits
ulimit -n 4096               # max open files, this shell
cat /proc/1234/limits        # a running process's
systemctl show myapp -p LimitNOFILE
```

Persistent per-user limits are `/etc/security/limits.conf` (week 8); per
service, `LimitNOFILE=` in the unit.

:::exam-tip
Likely tasks: "find the process using the most memory and record its PID"
(`ps aux --sort=-%mem | head -2`), "terminate the process named X"
(`pkill X`, verify with `pgrep`), "run Y with a nice value of 10"
(`nice -n 10 Y`), "change the priority of PID Z to 5" (`renice -n 5 -p Z`).
Verify with `ps -o pid,ni,cmd -p <pid>`. Try SIGTERM before SIGKILL - some
graders check the process ended cleanly.
:::

## Check yourself

1. What is the difference between SIGTERM and SIGKILL, and which do you
   send first?
2. What does a `Z` state mean, and how do you get rid of such a process?
3. Which command shows which process is holding a file that prevents an
   unmount?
