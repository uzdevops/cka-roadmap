## Writing a unit file

The exam objective is "create systemd services" - given a program, make it
a managed service that starts at boot, restarts on failure and logs to the
journal.

```bash
sudo vi /etc/systemd/system/myapp.service
```

```ini
[Unit]
Description=My application API
Documentation=https://example.com/docs
After=network-online.target postgresql.service
Wants=network-online.target
Requires=postgresql.service

[Service]
Type=simple
User=myapp
Group=myapp
WorkingDirectory=/opt/myapp
Environment="LOG_LEVEL=info" "PORT=8080"
EnvironmentFile=-/etc/myapp/env
ExecStartPre=/opt/myapp/bin/migrate
ExecStart=/opt/myapp/bin/server --port ${PORT}
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
TimeoutStartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=myapp

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload            # ALWAYS after creating or editing a unit
sudo systemctl enable --now myapp
systemctl status myapp
journalctl -u myapp -f
```

## The three sections

**`[Unit]`** - identity and ordering. `Description` shows in `status` and
logs. `After=`/`Before=` order the start **without** creating a
requirement; `Wants=` is a soft dependency (start it too, but carry on if
it fails); `Requires=` is hard (if it fails, we fail). For anything that
needs a working network, `After=network-online.target` **and**
`Wants=network-online.target` together - `network.target` alone only means
"the network stack is up", not "an address is configured".

**`[Service]`** - how to run it.

| Directive | Meaning |
|---|---|
| `Type=simple` | default: `ExecStart` **is** the daemon and does not fork |
| `Type=forking` | the program forks and the parent exits (old-style daemons); usually with `PIDFile=` |
| `Type=oneshot` | runs and exits; pair with `RemainAfterExit=yes` for setup tasks |
| `Type=notify` | the program tells systemd when it is ready (sd_notify) |
| `ExecStart=` | the command - **absolute path**, no shell syntax (no pipes or `&&` unless you run `/bin/bash -c '…'`) |
| `ExecStartPre=` / `ExecStartPost=` | before / after; a failing `Pre` aborts the start (prefix `-` to ignore failure) |
| `ExecReload=` | what `systemctl reload` runs |
| `ExecStop=` | usually unnecessary - systemd sends SIGTERM |
| `User=` / `Group=` | run unprivileged - do this |
| `WorkingDirectory=` | must exist |
| `Environment=` / `EnvironmentFile=` | variables (`-` prefix = optional file) |
| `Restart=` | `no` (default), `on-failure`, `always`, `on-abnormal` |
| `RestartSec=` | wait before restarting |
| `TimeoutStartSec=` / `TimeoutStopSec=` | how long systemd waits |
| `StandardOutput=` / `StandardError=` | `journal` (default), `null`, `append:/var/log/x.log` |
| `PIDFile=` | for `Type=forking` |

**`[Install]`** - what `enable` does. `WantedBy=multi-user.target` is the
answer for a normal service; without an `[Install]` section, `enable`
fails with "no installation config".

## A one-shot maintenance unit

```ini
# /etc/systemd/system/cleanup.service
[Unit]
Description=Clean old temporary files

[Service]
Type=oneshot
ExecStart=/usr/local/bin/cleanup.sh
```

Run on demand (`systemctl start cleanup`) or on a schedule with a timer
(week 6). No `[Install]` is needed if only a timer starts it.

## Hardening, cheaply

```ini
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict          # / read-only for this service
ProtectHome=yes
ReadWritePaths=/var/lib/myapp
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
LimitNOFILE=65535
MemoryMax=512M
```

Five lines that turn a compromised service into a much smaller problem.
`systemd-analyze security myapp` scores a unit and lists what is missing.

## Testing the unit before trusting it

```bash
systemd-analyze verify /etc/systemd/system/myapp.service     # syntax and references
sudo systemctl daemon-reload
sudo systemctl start myapp && systemctl status myapp
sudo systemctl stop myapp; sudo systemctl restart myapp
journalctl -u myapp -n 30 --no-pager
sudo systemctl enable myapp && systemctl is-enabled myapp
sudo reboot                                                   # the real test, if you can afford it
```

## Template units, briefly

A unit named `worker@.service` is a template; `%i` is the instance name:

```ini
# /etc/systemd/system/worker@.service
[Service]
ExecStart=/opt/app/worker --queue %i
```

```bash
sudo systemctl enable --now worker@images.service worker@email.service
```

One file, many instances - how `getty@tty1` and `sshd@` work.

:::warning
`ExecStart=` is **not** a shell command line: `ExecStart=/usr/bin/foo > /var/log/foo.log`
does not redirect, it passes `>` as an argument. Use
`StandardOutput=append:/var/log/foo.log`, or
`ExecStart=/bin/bash -c '/usr/bin/foo > /var/log/foo.log'`. The same goes
for `&&`, `|`, `*` and `$VAR` expansion beyond systemd's own `${VAR}`.
:::

:::exam-tip
Expect: "create a service named X that runs /path/to/script at boot as
user Y and restarts on failure". Write the three sections, `daemon-reload`,
`enable --now`, then prove it with `systemctl is-active X`, `is-enabled X`
and `journalctl -u X`. The two mistakes that cost marks are a missing
`[Install] WantedBy=` (so `enable` fails) and a forgotten `daemon-reload`.
:::

## Check yourself

1. What are the three sections of a unit file and what does each do?
2. What is the difference between `Type=simple`, `Type=forking` and
   `Type=oneshot`?
3. Why does `ExecStart=/usr/bin/foo > /tmp/out` not do what it looks like?
