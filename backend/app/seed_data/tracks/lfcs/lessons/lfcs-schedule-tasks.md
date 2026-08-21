## Three schedulers

| Tool | For |
|---|---|
| **cron** | repeating jobs at fixed times - the classic |
| **at** | a one-off job at a future time |
| **systemd timers** | repeating jobs with systemd's logging, dependencies and calendar syntax |

## crontab syntax

```
 ┌─ minute (0-59)
 │ ┌─ hour (0-23)
 │ │ ┌─ day of month (1-31)
 │ │ │ ┌─ month (1-12 or jan-dec)
 │ │ │ │ ┌─ day of week (0-7, 0 and 7 = Sunday, or sun-sat)
 │ │ │ │ │
 * * * * *  command to run
```

| Entry | Runs |
|---|---|
| `0 3 * * *` | every day at 03:00 |
| `*/15 * * * *` | every 15 minutes |
| `0 */4 * * *` | every 4 hours |
| `30 2 * * 1` | Mondays at 02:30 |
| `0 0 1 * *` | first day of each month |
| `0 9-17 * * 1-5` | hourly, 09:00-17:00, weekdays |
| `15 2 1,15 * *` | 02:15 on the 1st and 15th |
| `@reboot` | once at every boot |
| `@daily` `@weekly` `@monthly` `@hourly` `@yearly` | the shorthands |

**Day-of-month and day-of-week together are an OR**: `0 0 13 * 5` runs on
the 13th *and* every Friday, not only Friday the 13th.

## Per-user crontabs

```bash
crontab -e                 # edit YOUR crontab (uses $EDITOR)
crontab -l                 # list
crontab -r                 # remove it entirely (no confirmation - careful)
crontab -l > backup.cron   # back up before -r
crontab backup.cron        # install from a file
sudo crontab -u alice -e   # another user's
sudo crontab -u alice -l
```

Stored in `/var/spool/cron/crontabs/<user>` (Debian) or
`/var/spool/cron/<user>` (RHEL) - edit only through `crontab -e`, which
validates the syntax.

## System crontabs

```bash
cat /etc/crontab           # has an extra USER field
ls /etc/cron.d/            # drop-in files, same format as /etc/crontab
ls /etc/cron.{hourly,daily,weekly,monthly}/     # scripts, run by run-parts - no time fields at all
```

```
# /etc/cron.d/backup     ← note the user column
30 2 * * *  root  /usr/local/bin/backup.sh
```

A script in `/etc/cron.daily/` must be **executable**, owned by root, and
- on Debian - have **no dot in its filename** (`run-parts` skips
`backup.sh` unless configured; name it `backup`).

## The environment trap

cron runs with a minimal environment: `PATH=/usr/bin:/bin`, no `~/.bashrc`,
`HOME` set, `SHELL=/bin/sh`. A script that works in your terminal and does
nothing in cron is almost always this.

```
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAILTO=admin@example.com

0 3 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1
```

Rules: **absolute paths** for commands and files; redirect output (or cron
mails it, or it disappears); test with `env -i /bin/bash --noprofile
--norc /path/script.sh` to reproduce cron's bare environment.

```bash
%           # in a crontab, % means newline - escape it: date +\%F
0 3 * * * echo "run at $(date +\%F)" >> /var/log/x.log
```

## Checking that it ran

```bash
grep CRON /var/log/syslog | tail             # Debian
journalctl -u cron -f                        # or -u crond on RHEL
journalctl _COMM=cron --since today
sudo systemctl status cron
ls -l /var/spool/cron/crontabs/
```

Access control: `/etc/cron.allow` (if it exists, only these users may use
cron) and `/etc/cron.deny`.

## anacron: for machines that are not always on

```bash
cat /etc/anacrontab
# period  delay  job-identifier  command
# 1       5      cron.daily      run-parts --report /etc/cron.daily
```

cron skips jobs whose time passed while the machine was off; **anacron**
runs them late instead. Laptops and desktops need it; always-on servers
usually do not.

## at: once, later

```bash
at 22:00                       # then type commands, Ctrl-D to finish
at now + 1 hour
at 09:00 tomorrow
at 14:30 2026-09-01
echo "/usr/local/bin/report.sh" | at 06:00 tomorrow
atq                            # queue
atrm 3                         # remove job 3
at -c 3                        # show what job 3 will run (including its saved environment)
sudo systemctl enable --now atd
```

`at` saves your **current environment**, which makes it friendlier than
cron for one-offs. `/etc/at.allow`, `/etc/at.deny` control access.

## systemd timers

```ini
# /etc/systemd/system/backup.service
[Unit]
Description=Nightly backup
[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh
```

```ini
# /etc/systemd/system/backup.timer
[Unit]
Description=Run backup nightly
[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true          # run at boot if the last run was missed (anacron-like)
RandomizedDelaySec=300
[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now backup.timer
systemctl list-timers --all               # NEXT, LEFT, LAST, PASSED, UNIT
systemctl status backup.timer
journalctl -u backup.service              # the output is in the journal, not in mail
systemd-analyze calendar "Mon *-*-* 02:30:00"     # verify a schedule expression
```

`OnCalendar=` forms: `hourly`, `daily`, `weekly`, `Mon..Fri 09:00`,
`*-*-01 04:00:00`, `*:0/15` (every 15 minutes). Timers give you
dependencies, resource limits and journal logging that cron does not - use
them for anything non-trivial on a systemd machine.

:::exam-tip
Cron is the more likely ask: "run /usr/local/bin/x.sh every day at 05:30
as user alice" → `sudo crontab -u alice -e`, line `30 5 * * *
/usr/local/bin/x.sh`. Verify with `crontab -u alice -l`. Watch the field
order (minute first!) and use absolute paths. For "every 10 minutes" it is
`*/10 * * * *`.
:::

## Check yourself

1. Write the crontab line for 02:15 every Monday and Thursday.
2. Why does a script that works in your shell often fail under cron, and
   what are the two fixes?
3. What does `Persistent=true` do in a systemd timer, and which cron tool
   does it replace?
