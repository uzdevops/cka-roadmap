## Three doors into a system

A Linux system can be reached through a **text console** on the machine
itself, a **graphical console** if a desktop is installed, or **remotely**
over SSH. The exam may expect you to use any of them; the job mostly uses
the third.

```
 physical keyboard+screen ──▶ tty1..tty6  (text, "virtual consoles")
                          ──▶ display manager ──▶ graphical session (GNOME/KDE...)
 network ─────────────────▶ sshd ──▶ shell
```

## Text consoles: the TTYs

The kernel provides several **virtual consoles**, `/dev/tty1` to
`/dev/tty6`, each with its own login prompt (served by `agetty` under
systemd's `getty@.service`). Switch between them with **Ctrl+Alt+F1 …
F6**; on a server without a desktop you land on one of them at boot.

```
Ubuntu 24.04 LTS server tty1

server login: ahmad
Password:
ahmad@server:~$
```

```bash
tty                      # which terminal am I on?  /dev/tty2, or /dev/pts/0 for a graphical/SSH terminal
who                      # who is logged in, on which tty, since when
w                        # the same plus what each is running
```

A session on a TTY is a **shell process** (bash) owned by you; `exit`,
`logout` or Ctrl+D ends it and `getty` shows the prompt again.

## Graphical consoles

If a desktop is installed, a **display manager** (gdm, sddm, lightdm)
takes over one TTY - usually tty1 or tty7 - and shows the graphical login.
A graphical session still has text terminals inside it (the terminal
emulator opens a **pseudo-terminal**, `/dev/pts/N`), and the other TTYs
are still there behind it: Ctrl+Alt+F3 switches to a text login, Ctrl+Alt+F1
(or F7/F2, depending on the distribution) comes back.

```bash
systemctl status display-manager        # which one, and is it running
systemctl get-default                   # graphical.target vs multi-user.target (week 5)
```

## Remote: SSH

```bash
ssh user@host                           # password or key
ssh -p 2222 user@host                   # non-default port
ssh user@host 'uptime'                  # run one command and return
exit
```

SSH gives you a pseudo-terminal (`/dev/pts/N`) on the remote host; for the
shell it is the same as sitting at the machine. The server side is
`sshd`; week 10 covers configuring it. Two practical notes now: the first
connection asks you to trust the host key (and stores it in
`~/.ssh/known_hosts`); and a closed network connection kills the session
and everything running in it unless you used `nohup`, `tmux` or `screen`.

## Which is which

| | TTY | graphical terminal | SSH |
|---|---|---|---|
| device | `/dev/ttyN` | `/dev/pts/N` | `/dev/pts/N` |
| needs | physical access (or a VM console) | a desktop | network + sshd |
| survives network loss | yes | yes | no |
| typical use | servers, rescue, when the GUI or network is broken | workstations | everything else |

:::exam-tip
On the exam the terminal you get is already a shell. A task may still say
"log in to host X" - that is `ssh`, and the host name is in the task. Know
the `Ctrl+Alt+Fn` switch for the case where a VM console is the only way in,
and `who`/`w` for "which users are logged in and from where".
:::

## Check yourself

1. What is a virtual console and how do you switch between them?
2. A terminal window inside a desktop: is it a TTY? What device does it
   use?
3. What do `who` and `w` tell you, and how do they differ?
