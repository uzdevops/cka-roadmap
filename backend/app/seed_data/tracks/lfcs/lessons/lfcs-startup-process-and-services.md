## systemd runs everything

PID 1 is `systemd`; everything else is a **unit** it manages. The unit
types you meet: `.service` (a daemon), `.socket`, `.timer` (week 6),
`.mount`, `.target` (last lesson), `.path`, `.device`.

```bash
systemctl status nginx
# ● nginx.service - A high performance web server
#      Loaded: loaded (/lib/systemd/system/nginx.service; enabled; preset: enabled)
#      Active: active (running) since Wed 2026-08-19 09:12:01 UTC; 2h ago
#    Main PID: 1234 (nginx)
#       Tasks: 3 (limit: 4657)
#      Memory: 12.4M
#         CGroup: /system.slice/nginx.service
#                 ├─1234 nginx: master process
#                 └─1235 nginx: worker process
# Aug 19 09:12:01 web01 systemd[1]: Started A high performance web server.
```

Two words carry most of the meaning: **Loaded: … enabled** (will it start
at boot?) and **Active: active (running)** (is it running now?). They are
independent - a service can run now and not at boot, or vice versa.

## The verbs

```bash
sudo systemctl start nginx            # now
sudo systemctl stop nginx
sudo systemctl restart nginx          # stop then start
sudo systemctl reload nginx           # re-read config without dropping connections (if supported)
sudo systemctl reload-or-restart nginx
sudo systemctl enable nginx           # at boot
sudo systemctl disable nginx
sudo systemctl enable --now nginx     # both, in one command
sudo systemctl disable --now nginx
sudo systemctl mask nginx             # cannot be started at all, even as a dependency
sudo systemctl unmask nginx
systemctl is-active nginx; systemctl is-enabled nginx; systemctl is-failed nginx
```

`enable` creates a **symlink** from the target's `.wants` directory to the
unit file - which is why "enabled" is visible in the filesystem:

```bash
ls -l /etc/systemd/system/multi-user.target.wants/
```

## Looking around

```bash
systemctl                                    # every active unit
systemctl list-units --type=service          # services only
systemctl list-units --type=service --state=running
systemctl --failed                           # what is broken - the first command on a strange system
systemctl list-unit-files --type=service     # every INSTALLED unit and its enabled/disabled state
systemctl list-unit-files --state=enabled
systemctl cat nginx                          # the unit file(s), including drop-ins
systemctl show nginx -p ExecStart -p Restart # single properties
systemctl list-dependencies nginx            # what it needs
systemctl list-dependencies --reverse nginx  # what needs it
systemd-analyze verify /etc/systemd/system/my.service    # syntax check
```

## Where unit files live

| Path | What | Wins |
|---|---|---|
| `/lib/systemd/system/` (or `/usr/lib/systemd/system/`) | shipped by packages | lowest |
| `/run/systemd/system/` | runtime, transient | middle |
| `/etc/systemd/system/` | **yours** - local units and overrides | **highest** |

Never edit a packaged unit in `/lib` - a package update overwrites it.
Override instead:

```bash
sudo systemctl edit nginx            # creates /etc/systemd/system/nginx.service.d/override.conf
# [Service]
# Restart=always
# RestartSec=5
sudo systemctl edit --full nginx     # copy the whole unit into /etc to edit
sudo systemctl daemon-reload         # ALWAYS after changing unit files by hand
sudo systemctl restart nginx
systemctl cat nginx                  # confirm what is now in effect
```

`systemctl edit` runs `daemon-reload` for you; hand-editing a file does
not - and a forgotten `daemon-reload` means systemd keeps running the old
definition, which is a confusing five minutes.

## Reading a failure

```bash
systemctl status myapp
# Active: failed (Result: exit-code) since ...; 10s ago
# Process: 4321 ExecStart=/usr/local/bin/myapp (code=exited, status=203/EXEC)
journalctl -u myapp -n 50 --no-pager
journalctl -u myapp -f
journalctl -u myapp -b -p err
journalctl -xeu myapp                 # the systemd-recommended combination: explanations, end, this unit
```

| status= | Usually |
|---|---|
| `203/EXEC` | the `ExecStart` binary does not exist or is not executable |
| `200/CHDIR` | `WorkingDirectory` does not exist |
| `217/USER` | the `User=` does not exist |
| `1` | the program itself failed - read its own log lines |
| `226/NAMESPACE` | a sandboxing directive (`ProtectSystem`, `PrivateTmp`) blocks something |
| `timeout` | the service did not signal readiness - wrong `Type=` |

## Dependencies, briefly

`After=`/`Before=` set ordering; `Requires=`/`Wants=` set need (`Wants` is
the loose one - the unit still starts if the wanted unit fails). A unit is
started at boot because a **target** wants it, which is what `enable`
arranges via `WantedBy=` in `[Install]`.

```bash
systemctl list-dependencies multi-user.target | grep nginx
systemctl show nginx -p After -p Wants -p WantedBy
```

:::exam-tip
The task wording maps one to one: "make X start at boot and start it now"
→ `systemctl enable --now X`; "stop it and prevent it from ever starting"
→ `systemctl mask X` (or `disable --now`); "why did it fail" →
`systemctl status X` then `journalctl -u X`. Verify every change with
`systemctl is-active` **and** `is-enabled` - tasks usually check both.
:::

## Check yourself

1. What is the difference between `start` and `enable`, and between
   `disable` and `mask`?
2. Where do your own unit files and overrides belong, and what must you
   run after editing one by hand?
3. A service fails with `status=203/EXEC`. What is wrong?
