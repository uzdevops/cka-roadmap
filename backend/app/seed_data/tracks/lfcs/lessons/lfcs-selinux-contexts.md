## Labels on everything

SELinux (Security-Enhanced Linux) adds **mandatory access control** on top
of the usual owner/permission model: every process and every file carries
a **label**, and policy decides which process labels may touch which file
labels. Even root is bound by it.

It is default-on in the RHEL family; on Ubuntu the equivalent is AppArmor,
but the LFCS objectives name SELinux, so this is where it is taught.

```bash
getenforce                # Enforcing | Permissive | Disabled
sestatus                  # a fuller report: mode, policy, whether it is loaded
id -Z                     # YOUR context
ls -Z /var/www/html       # file contexts
ps -eZ | head             # process contexts
```

## Reading a context

```
system_u:object_r:httpd_sys_content_t:s0
    │        │            │            └── level (MLS/MCS; s0 in the targeted policy)
    │        │            └── TYPE  ← the part that matters almost always
    │        └── role (object_r for files, system_r for processes)
    └── user (SELinux user, not the Unix user)
```

Almost all day-to-day SELinux work is about the **type**. Convention:
process types end in `_t` and are called **domains** (`httpd_t`,
`sshd_t`); file types also end in `_t` (`httpd_sys_content_t`,
`ssh_home_t`). Policy says, for example, "a process in `httpd_t` may read
files labelled `httpd_sys_content_t`" - and nothing else.

```bash
ls -Z /var/www/html/index.html
# -rw-r--r--. root root unconfined_u:object_r:httpd_sys_content_t:s0 index.html
ps -eZ | grep httpd
# system_u:system_r:httpd_t:s0     1234 ?  00:00:00 httpd
ls -Z /etc/ssh/sshd_config
ls -dZ /home/ahmad
```

The `.` after the permissions in a plain `ls -l` means "this file has an
SELinux context" (a `+` means it has an ACL).

## Where a label comes from

- Files **inherit** the label of the directory they are created in - which
  is why a file *moved* (`mv`) into `/var/www` keeps its old label while a
  file *copied* (`cp`) gets the new one.
- The policy has a database of default labels per path
  (`semanage fcontext -l`), used by `restorecon` and at relabel time.

```bash
semanage fcontext -l | grep '/var/www'
# /var/www(/.*)?    all files    system_u:object_r:httpd_sys_content_t:s0
matchpathcon /var/www/html/index.html      # what the label SHOULD be
restorecon -v /var/www/html/index.html     # set it to what it should be
restorecon -Rv /var/www                     # recursively
```

## The symptom to recognise

A service that has correct Unix permissions and still gets "Permission
denied" - and the file's label looks wrong - is SELinux.

```bash
sudo ausearch -m avc -ts recent            # AVC denials (the audit record of a block)
sudo ausearch -m avc -ts today | audit2why # in English, with a suggested fix
sudo tail /var/log/audit/audit.log | grep denied
sudo journalctl -t setroubleshoot          # if setroubleshoot is installed: plain-language advice
```

```
type=AVC msg=audit(...): avc: denied { read } for pid=1234 comm="httpd"
  name="index.html" dev="dm-0" ino=12345
  scontext=system_u:system_r:httpd_t:s0
  tcontext=unconfined_u:object_r:user_home_t:s0 tclass=file
```

Read it as: a process in `httpd_t` tried to `read` a file labelled
`user_home_t`, and policy said no. The fix is to give the file the right
label - not to switch SELinux off.

## Modes

```bash
getenforce
sudo setenforce 0          # Permissive: log denials, allow everything - TEMPORARY, for diagnosis
sudo setenforce 1          # Enforcing
cat /etc/selinux/config    # SELINUX=enforcing|permissive|disabled  ← persistent, needs a reboot
```

Permissive is a **diagnostic** state: if the problem disappears in
permissive mode, it is SELinux, and `ausearch` now lists everything that
would have been denied. Then relabel and go back to enforcing. The next
lesson does the fixing.

:::warning
`SELINUX=disabled` in `/etc/selinux/config` stops labelling entirely; when
you re-enable it, the filesystem needs a full relabel
(`sudo touch /.autorelabel && reboot`), which takes a long time on a big
disk. Prefer `permissive` over `disabled` if you must loosen it at all.
:::

:::exam-tip
For this objective the ask is usually just to **list and identify**:
`ls -Z` on a path, `ps -Z` for a process, `id -Z` for yourself, and
`getenforce`/`sestatus` for the mode - often writing the output to a file.
Know that the third field is the type and that it is the one that matters.
:::

## Check yourself

1. What are the four fields of an SELinux context, and which one does
   day-to-day work concern?
2. Why does `mv` into `/var/www` often break a web server while `cp` does
   not?
3. What does a denial in `ausearch -m avc` tell you, in terms of scontext
   and tcontext?
