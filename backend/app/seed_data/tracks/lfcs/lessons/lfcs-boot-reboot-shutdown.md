## Stopping a machine properly

A Linux system has processes with open files, filesystems with dirty
caches and services mid-transaction. Powering off cuts all of that; the
shutdown commands unmount, flush and stop things in order.

```bash
sudo systemctl poweroff              # stop everything, power off
sudo systemctl reboot                # stop everything, reboot
sudo systemctl halt                  # stop everything, halt the CPU (no power off)
sudo systemctl suspend               # to RAM
sudo systemctl hibernate             # to disk
```

The older commands still work (they are symlinks to `systemctl`):

```bash
sudo poweroff; sudo reboot; sudo halt
sudo shutdown -h now                 # halt/power off now
sudo shutdown -r now                 # reboot now
sudo shutdown -h +10 "Patching at 22:10, please save your work"
sudo shutdown -r 22:30
sudo shutdown -c                     # cancel a scheduled shutdown
```

## Warning the people on the machine

`shutdown` with a delay does three things: it broadcasts the message to
every logged-in terminal, it creates `/run/nologin` so new logins are
refused, and it schedules the action.

```bash
who                                          # who is logged in and from where
w                                            # + what they are running
wall "Rebooting in 5 minutes for kernel update"     # broadcast without scheduling anything
sudo shutdown -r +5 "Kernel update"
sudo shutdown -c                             # changed your mind - the message goes out too
```

## Where the boot went: reading the last one

```bash
uptime                       # how long since the last boot, load average
uptime -s                    # the boot time itself
who -b                       # the same, from utmp
last reboot | head           # a history of boots
last -x | head               # + runlevel/shutdown records - was it clean?
journalctl --list-boots      # every boot the journal remembers, with ids
journalctl -b                # this boot's log
journalctl -b -1             # the PREVIOUS boot - where a crash's last words are
journalctl -b -1 -p err      # only errors from it
dmesg -T | less              # kernel ring buffer with timestamps
systemd-analyze              # how long the boot took, split kernel/userspace
systemd-analyze blame        # slowest units
systemd-analyze critical-chain
```

`journalctl -b -1` is the command for "the server rebooted overnight, why".
If there is nothing at the end but normal shutdown lines, it was a clean
reboot (someone or something asked); a log that just stops is a crash or a
power cut.

## Rebooting a remote machine safely

Nothing is worse than a server that does not come back. Before a remote
reboot:

```bash
sudo systemctl is-enabled sshd networking     # will the way back in come up?
mount | grep -c "ro,"                          # nothing important read-only unexpectedly
sudo journalctl -p err -b | tail               # unresolved errors that a reboot will not fix
findmnt --verify                               # fstab sane? a bad fstab entry can block boot (week 11)
sudo systemctl list-units --state=failed
sync                                           # flush caches (systemctl does this, but harmless)
sudo shutdown -r +1 "Reboot for kernel update"
```

Then watch it come back: `ping -c 100 host`, and reconnect.

:::warning
A wrong line in `/etc/fstab` is the classic "it never came back": at boot
systemd waits for a device that does not exist and drops to emergency mode
- which needs console access, not SSH. Always `mount -a` (or
`findmnt --verify`) after editing fstab and **before** rebooting. On a
remote machine with no console, that check is the difference between a
reboot and a data-centre trip.
:::

## Forcing, when nothing else works

```bash
sudo systemctl reboot --force            # skip stopping units, still unmount
sudo systemctl reboot --force --force    # immediate, like the reset button - last resort
# Magic SysRq, from a physical console, when the kernel still lives:
#   Alt+SysRq+R E I S U B  ("Raising Elephants Is So Utterly Boring"):
#   unRaw, tErminate, kIll, Sync, Unmount, reBoot
echo 1 | sudo tee /proc/sys/kernel/sysrq       # enable SysRq if disabled
```

:::exam-tip
Know both vocabularies (`systemctl reboot` and `shutdown -r`), the delayed
form with a message (`shutdown -r +10 "msg"`), and `shutdown -c` to
cancel. And know `journalctl -b -1` for the previous boot - "find out why
the system rebooted" is a plausible task and that is where the answer is.
:::

## Check yourself

1. What three things does `shutdown -h +10 "msg"` do?
2. Which command shows the log of the boot **before** this one, and when
   would you need it?
3. What should you verify before rebooting a remote machine, and which
   file most often prevents it coming back?
