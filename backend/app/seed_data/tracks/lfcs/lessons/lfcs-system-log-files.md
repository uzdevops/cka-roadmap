## Two log systems, side by side

Modern Linux keeps a binary **journal** (systemd-journald) and, usually,
plain text files in `/var/log` written by rsyslog. Both hold the same
events; the journal has structure and filters, the files are greppable and
survive being copied.

```bash
journalctl                       # everything, oldest first (it is a pager: q to quit)
journalctl -e                    # jump to the end
journalctl -f                    # follow, like tail -f
journalctl -n 50                 # last 50 lines
journalctl -r                    # newest first
```

## Filtering the journal

```bash
journalctl -u nginx                       # one unit
journalctl -u nginx -u sshd               # several
journalctl -u nginx -f                    # follow one unit
journalctl -b                             # this boot
journalctl -b -1                          # the previous boot
journalctl --list-boots
journalctl -k                             # kernel messages (like dmesg)
journalctl -p err                         # priority: err and worse
journalctl -p warning..err
journalctl --since "2026-08-19 09:00" --until "2026-08-19 10:00"
journalctl --since "1 hour ago"
journalctl --since yesterday --until today
journalctl _PID=1234
journalctl _UID=1000
journalctl /usr/sbin/sshd                 # by executable
journalctl -u myapp -o json-pretty | head -40      # every structured field
journalctl -o cat                         # bare messages, no timestamps - good for piping
journalctl -xe                            # end, with explanations - the standard "what just broke"
journalctl -u myapp --grep "timeout"
```

Priorities, low number = worse: `0 emerg`, `1 alert`, `2 crit`, `3 err`,
`4 warning`, `5 notice`, `6 info`, `7 debug`.

## Journal storage: volatile or persistent

```bash
journalctl --disk-usage
ls /var/log/journal/           # exists → persistent;  only /run/log/journal → RAM only, lost at reboot
sudo mkdir -p /var/log/journal && sudo systemd-tmpfiles --create --prefix /var/log/journal
sudo systemctl restart systemd-journald
```

```ini
# /etc/systemd/journald.conf
[Journal]
Storage=persistent
SystemMaxUse=500M
MaxRetentionSec=1month
```

```bash
sudo journalctl --vacuum-size=200M
sudo journalctl --vacuum-time=7d
sudo journalctl --verify
```

If `journalctl -b -1` says "Specifying boot ID has no effect, no persistent
journal was found", the journal is in RAM - that is the setting to change
**before** the next crash, not after.

## /var/log: the text files

| File | Holds |
|---|---|
| `/var/log/syslog` (Debian) / `/var/log/messages` (RHEL) | general system messages |
| `/var/log/auth.log` (Debian) / `/var/log/secure` (RHEL) | authentication, sudo, sshd |
| `/var/log/kern.log` | kernel |
| `/var/log/boot.log` | boot messages |
| `/var/log/dmesg` | kernel ring buffer at boot |
| `/var/log/cron` / journal | cron jobs |
| `/var/log/apt/`, `/var/log/dnf.log` | package operations |
| `/var/log/nginx/`, `/var/log/mysql/` | per-service directories |
| `/var/log/wtmp`, `/var/log/btmp`, `/var/log/lastlog` | binary: use `last`, `lastb`, `lastlog` |

```bash
sudo tail -f /var/log/syslog
sudo grep -i "failed password" /var/log/auth.log | tail
sudo less /var/log/nginx/error.log
last | head; sudo lastb | head; lastlog | grep -v "Never"
```

## rsyslog: which message goes where

```bash
cat /etc/rsyslog.conf; ls /etc/rsyslog.d/
```

```
auth,authpriv.*                 /var/log/auth.log
*.*;auth,authpriv.none          -/var/log/syslog
kern.*                          -/var/log/kern.log
*.emerg                         :omusrmsg:*
local7.*                        @@logserver.example.com:514      # @@ TCP, @ UDP - central logging
```

`facility.priority  destination`. After editing: `sudo systemctl restart
rsyslog`. Test with `logger`:

```bash
logger "test message"                       # goes to syslog as user.notice
logger -p local7.err -t myapp "disk full"   # facility, priority, tag
journalctl -t myapp
```

## logrotate: keeping /var/log from filling the disk

```bash
cat /etc/logrotate.conf; ls /etc/logrotate.d/
```

```
/var/log/myapp/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 myapp adm
    sharedscripts
    postrotate
        systemctl reload myapp > /dev/null 2>&1 || true
    endscript
}
```

```bash
sudo logrotate -d /etc/logrotate.d/myapp     # debug: what WOULD happen
sudo logrotate -f /etc/logrotate.d/myapp     # force a rotation now
cat /var/lib/logrotate/status                 # when each file last rotated
```

`create` matters: a rotated file must keep the permissions and ownership
the service needs, or the service writes to a file it cannot open.
`copytruncate` is the option for programs that hold the file open and do
not reopen on reload.

## When the disk fills with logs

```bash
df -h /var
du -sh /var/log/* | sort -rh | head
sudo journalctl --vacuum-size=200M
sudo find /var/log -name "*.gz" -mtime +30 -delete
lsof +L1 | head        # deleted files still held open by a process - restart it to release the space
```

That last one is the trap: deleting a log a process still has open frees
no space until the process reopens it. `df` stays full, `du` says the file
is gone.

:::exam-tip
Know both worlds: `journalctl -u X`, `-b`, `-p err`, `--since` for systemd,
and `/var/log/auth.log`/`syslog` with grep for text. "Find all failed login
attempts" → `grep "Failed password" /var/log/auth.log` or `journalctl -u
sshd -p err`. "Make the journal persistent" → `Storage=persistent` +
restart. "Configure rotation for /var/log/myapp" → a file in
`/etc/logrotate.d/` and test with `logrotate -d`.
:::

## Check yourself

1. Which journalctl options show: one unit, the previous boot, errors only,
   the last hour?
2. How do you make the journal survive a reboot, and how do you tell
   whether it does now?
3. Why can deleting a large log file leave `df` unchanged?
