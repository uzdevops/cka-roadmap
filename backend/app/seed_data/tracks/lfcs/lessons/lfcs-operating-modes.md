## Targets: what "the system is up" means

SysV had **runlevels** (0-6); systemd has **targets**, named units that
group the services a given mode needs. A target is reached by starting
everything it wants.

| Target | Old runlevel | Means |
|---|---|---|
| `poweroff.target` | 0 | shut down |
| `rescue.target` | 1, S | single user: root shell, local filesystems, **no network, no other services** |
| `multi-user.target` | 2, 3, 4 | full system, network, all services, **text login** - the server default |
| `graphical.target` | 5 | multi-user + a display manager |
| `reboot.target` | 6 | reboot |
| `emergency.target` | - | the most minimal: root shell, `/` mounted **read-only**, almost nothing else |

```bash
systemctl get-default                       # graphical.target / multi-user.target
sudo systemctl set-default multi-user.target   # what to boot into from now on (a symlink in /etc/systemd/system)
ls -l /etc/systemd/system/default.target
systemctl list-units --type=target           # what is active now
systemctl list-dependencies multi-user.target | head -30
```

## Switching now

```bash
sudo systemctl isolate multi-user.target     # stop the GUI, keep the system up
sudo systemctl isolate graphical.target      # start it again
sudo systemctl isolate rescue.target         # drop to single user (asks for the root password)
sudo systemctl rescue                        # the same, plus a wall message
sudo systemctl emergency
sudo systemctl default                       # back to the default target
runlevel; who -r                             # the compatibility view: "N 5"
sudo init 3                                  # still works: mapped onto isolate multi-user.target
```

`isolate` starts the target's units and **stops everything not part of
it** - that is the difference from a plain `start`. Do not `isolate` a
target over SSH unless it includes the network: `rescue.target` will drop
your connection.

## Choosing a mode at boot

At the GRUB menu, press `e` on the entry and append to the `linux` line:

| Append | Effect |
|---|---|
| `systemd.unit=rescue.target` | boot into rescue |
| `systemd.unit=emergency.target` | boot into emergency |
| `single` or `1` | rescue, the old spelling |
| `init=/bin/bash` | no systemd at all - a root shell with `/` read-only; `mount -o remount,rw /` first |
| `systemd.mask=some.service` | boot without one unit |
| `rd.break` | stop in the initramfs (RHEL) |

Ctrl+X boots with the edit, for this boot only. This is how you get in when
a broken service, a bad `fstab`, or a lost root password locks you out -
and, permanently, in `/etc/default/grub` + `update-grub`.

```bash
# resetting a forgotten root password, from init=/bin/bash:
mount -o remount,rw /
passwd root
exec /sbin/init          # or: mount -o remount,ro / ; reboot -f
```

## Rescue vs emergency, in practice

| | rescue | emergency |
|---|---|---|
| filesystems | local ones mounted rw | only `/`, **read-only** |
| services | basic ones started | none |
| use for | fixing a broken service, a full disk | fixing `/etc/fstab`, a filesystem that will not mount |

In emergency mode the first command is almost always:

```bash
mount -o remount,rw /
vi /etc/fstab            # comment out the offending line
mount -a                 # prove the rest is fine
systemctl reboot
```

## Masking a unit that breaks the boot

```bash
sudo systemctl mask broken.service      # link it to /dev/null: it cannot be started at all
sudo systemctl unmask broken.service
```

`mask` is stronger than `disable` and is the tool for "this service hangs
the boot" - covered again in the services lesson.

:::exam-tip
Three commands cover this objective: `systemctl get-default`, `systemctl
set-default <target>`, `systemctl isolate <target>`. Know the two useful
targets by name (`multi-user`, `graphical`) and the two recovery ones
(`rescue`, `emergency`). If a task says "make the system boot to the
command line", it is `set-default multi-user.target` - and verify with
`get-default`.
:::

## Check yourself

1. What is the difference between `systemctl start` and `systemctl
   isolate`?
2. Which target does a server normally boot into, and how do you change
   it permanently?
3. In emergency mode, why is `mount -o remount,rw /` almost always the
   first command?
