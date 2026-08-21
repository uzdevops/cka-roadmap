## Fixing SELinux properly

The previous lesson read labels. This one changes them - the four tools
that solve nearly every real denial: **restorecon**, **semanage
fcontext**, **semanage port**, and **booleans**.

The order to try them:

```
 denial → ausearch/audit2why → is the label wrong?  → restorecon (temporary path) or semanage fcontext + restorecon (permanent)
                              → is it a port?       → semanage port
                              → is it a policy switch? → setsebool -P
                              → none of the above    → audit2allow module (last resort)
```

## Modes and packages

```bash
sudo dnf install policycoreutils policycoreutils-python-utils setroubleshoot-server selinux-policy-devel
getenforce; sestatus
sudo setenforce 0 / 1                    # temporary
sudo vi /etc/selinux/config              # SELINUX=enforcing (persistent, needs reboot)
```

## 1. Relabel a file: chcon and restorecon

```bash
sudo chcon -t httpd_sys_content_t /var/www/html/index.html    # change now
sudo chcon -R -t httpd_sys_content_t /srv/web
sudo chcon --reference=/var/www/html/other.html /var/www/html/new.html
sudo restorecon -Rv /var/www                                   # reset to the POLICY default
```

The difference matters: `chcon` writes a label that the policy does not
know about, so a relabel (`restorecon -R /`, `/.autorelabel`, a package
update) reverts it. `chcon` is for testing; the permanent fix is the next
tool.

## 2. Teach the policy a path: semanage fcontext

```bash
sudo semanage fcontext -a -t httpd_sys_content_t "/srv/web(/.*)?"
sudo restorecon -Rv /srv/web                    # apply the rule to what is already there
semanage fcontext -l | grep '/srv/web'
sudo semanage fcontext -d "/srv/web(/.*)?"      # remove the rule
sudo semanage fcontext -a -e /var/www /srv/web  # -e: "label /srv/web like /var/www" (equivalence)
```

The regex form `"(/.*)?"` means the directory itself and everything under
it. `semanage fcontext` records the rule; `restorecon` applies it. Both
steps, every time - the rule alone changes nothing on disk.

## 3. Allow a non-standard port: semanage port

```bash
semanage port -l | grep http_port_t
# http_port_t   tcp   80, 81, 443, 488, 8008, 8009, 8443, 9000
sudo semanage port -a -t http_port_t -p tcp 8081       # add
sudo semanage port -m -t http_port_t -p tcp 8081       # modify, if the port is already in another type
sudo semanage port -d -t http_port_t -p tcp 8081       # delete
sudo semanage port -a -t ssh_port_t -p tcp 2222        # moving sshd to 2222 needs this AND the firewall
```

A service that refuses to bind a non-default port, with a denial naming
`name_bind`, is this. (Changing sshd's port needs three things: the config,
the firewall, and this.)

## 4. Booleans: policy switches

```bash
getsebool -a | head
getsebool httpd_can_network_connect
sudo setsebool httpd_can_network_connect on         # now
sudo setsebool -P httpd_can_network_connect on      # AND persistently  ← the -P is the point
semanage boolean -l | grep httpd_can_network
sudo semanage boolean -l -C                          # only the ones changed from default
```

Booleans the exam and real life keep hitting:

| Boolean | Turns on |
|---|---|
| `httpd_can_network_connect` | web app connecting out to a database or API |
| `httpd_can_network_connect_db` | ... to a database specifically |
| `httpd_enable_homedirs` | serving `/home/*/public_html` |
| `httpd_use_nfs` | web content on an NFS mount |
| `ftpd_full_access`, `ftpd_anon_write` | FTP writes |
| `samba_enable_home_dirs` | Samba home shares |
| `nfs_export_all_rw` | NFS exports read-write |
| `ssh_sysadm_login` | privileged SSH logins |

`-P` writes the change to policy; without it, the next reboot forgets.

## 5. Last resort: a local policy module

When the denial is legitimate and no boolean or label covers it:

```bash
sudo ausearch -m avc -ts recent | audit2why              # why it was denied
sudo ausearch -c 'myapp' --raw | audit2allow -M myapp    # generate myapp.te and myapp.pp
cat myapp.te                                              # READ IT before installing
sudo semodule -i myapp.pp                                 # install the module
sudo semodule -l | grep myapp
sudo semodule -r myapp                                    # remove
```

`audit2allow` writes a rule that permits exactly what was denied. Read the
generated `.te` first: if it grants something sweeping, the real problem is
a wrong label, not a missing rule.

## The whole workflow, once

```bash
# symptom: nginx serving /srv/web returns 403, permissions look fine
sudo setenforce 0 && curl -I localhost/          # works now? → it is SELinux
sudo setenforce 1
sudo ausearch -m avc -ts recent | audit2why
# ...denied { read } ... tcontext=...:default_t
ls -Z /srv/web/index.html                        # default_t - wrong
sudo semanage fcontext -a -t httpd_sys_content_t "/srv/web(/.*)?"
sudo restorecon -Rv /srv/web
ls -Z /srv/web/index.html                        # httpd_sys_content_t
curl -I localhost/                               # 200
```

## Relabelling the whole filesystem

```bash
sudo touch /.autorelabel && sudo reboot          # relabels everything at boot (slow)
sudo fixfiles -F relabel
sudo restorecon -Rv /home                         # a targeted relabel is usually enough
```

:::warning
Disabling SELinux is not a fix, it is the removal of a control - and on a
machine where it was enforcing, re-enabling later requires a full relabel.
If you must loosen it while diagnosing, use **permissive**, capture the
denials, fix the labels, and go back to enforcing in the same session.
:::

:::exam-tip
Three commands cover most SELinux tasks: `semanage fcontext -a -t <type>
"<path>(/.*)?"` **followed by** `restorecon -Rv <path>`; `semanage port -a
-t <type> -p tcp <port>`; and `setsebool -P <boolean> on`. The `-P` and the
`restorecon` are where marks are lost. Verify with `ls -Z`, `semanage port
-l | grep`, `getsebool`.
:::

## Check yourself

1. What is the difference between `chcon` and `semanage fcontext` +
   `restorecon`?
2. What does the `-P` in `setsebool -P` do, and what happens without it?
3. A service cannot bind to a non-standard port. Which tool fixes it, and
   what else must also be changed?
