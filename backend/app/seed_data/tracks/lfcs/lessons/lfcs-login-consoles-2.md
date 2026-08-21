## What a session is

When you log in - on a TTY, through the display manager, or over SSH - the
system starts a **session**: a login process authenticates you (PAM), sets
your identity and environment, and starts your **login shell** (or the
desktop). Everything you run is a child of that shell. Log out, and the
shell ends; its children get `SIGHUP` and usually end with it.

```bash
echo $SHELL                 # your login shell, from /etc/passwd
echo $$                     # the shell's PID
ps -o pid,ppid,tty,cmd -u $USER
loginctl list-sessions      # systemd-logind's view: every session, its user, seat/tty or remote
loginctl show-session 3
last | head                 # login history from /var/log/wtmp: who, from where, for how long
lastlog                     # each user's most recent login
```

## Switching and multiplexing

On a physical or VM console, **Ctrl+Alt+F1…F6** moves between TTYs; each
can hold a separate login - one as yourself, one as root in an emergency,
one watching a log. In a text-only session (no `Alt+Gr` desktop shortcuts)
**Alt+F2** alone switches.

```bash
chvt 3                      # switch to tty3 from the command line (root)
```

Over SSH there are no TTYs to switch to; the equivalent is a
**multiplexer**: `tmux` or `screen` keeps sessions alive when the
connection drops and lets you split and switch.

```bash
tmux                        # new session; Ctrl+b d detaches
tmux ls; tmux attach        # come back after a dropped SSH
```

## Logging out safely

| Where | How |
|---|---|
| a shell | `exit`, `logout`, or Ctrl+D on an empty line |
| a graphical session | the desktop's log-out menu; or `loginctl terminate-session <id>` |
| another user's session (root) | `loginctl terminate-session <id>`, `pkill -KILL -u user`, `loginctl kill-user user` |

"Safely" means: not mid-write. Before logging out a user or rebooting,
`w` shows what they are running; `wall "message"` writes to every
terminal; `shutdown +5` (week 5) gives them time and blocks new logins.

## Who is logged in, from where

```bash
who
# ahmad    tty1         2026-08-19 09:12
# ahmad    pts/0        2026-08-19 09:20 (10.0.0.7)
# backup   pts/1        2026-08-19 09:31 (10.0.0.9)
w
# 09:35:02 up 2 days,  3 users,  load average: 0.10, 0.05, 0.01
# USER     TTY      FROM       LOGIN@   IDLE   WHAT
# ahmad    pts/0    10.0.0.7   09:20    0.00s  w
```

The `FROM` column and `last` answer the audit question "who was on this box
at 3 a.m."; `who -b` gives the last boot time; `users` the bare list.

## Root's session

Logging in directly as root is usually disabled (week 8); you log in as
yourself and elevate: `sudo -i` for a root login shell, `su -` if root has
a password. Either way, the session is yours - `who` still shows you - and
`sudo`'s log records what you did.

:::tip
Make `tmux` a reflex on anything remote: `tmux new -s work` at the start,
`tmux attach -t work` after a dropped connection. It turns "the network
blipped and my 40-minute job died" into "reattach and carry on".
:::

## Check yourself

1. What happens to the programs you started when your login shell exits?
2. How do you see every active session, including graphical and remote
   ones, with one command?
3. What would you run before forcibly logging out another user, and why?
