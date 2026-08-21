## When rwx is not enough

Standard permissions describe exactly three subjects: one owner, one
group, everyone else. "alice may write, the devs group may read, bob may
read but nobody else" needs a fourth - and that is what **ACLs** provide.

```bash
ls -l report.txt
# -rw-rw-r--+ 1 ahmad devs 1234 Aug 21 10:00 report.txt
#           ↑ the + means this file has an ACL
```

Requirements: the filesystem must be mounted with `acl` (ext4 and xfs
enable it by default on modern distributions).

```bash
sudo apt install acl
findmnt -o TARGET,OPTIONS /home
sudo mount -o remount,acl /home        # only if it is missing
```

## Reading and setting ACLs

```bash
getfacl report.txt
# file: report.txt
# owner: ahmad
# group: devs
user::rw-
user:bob:r--                 ← a named user
group::rw-
group:qa:r--                 ← a named group
mask::rw-                    ← the CEILING on all named entries and the group
other::r--
```

```bash
setfacl -m u:bob:rw report.txt            # modify: give bob read+write
setfacl -m g:qa:r report.txt              # a group
setfacl -m u:bob:rwx,g:qa:rx dir/         # several at once
setfacl -R -m g:devs:rwx /srv/project     # recursive
setfacl -x u:bob report.txt               # remove bob's entry
setfacl -b report.txt                     # remove ALL ACLs
setfacl -m m:r report.txt                 # set the mask explicitly
getfacl a.txt | setfacl --set-file=- b.txt        # copy an ACL from one file to another
```

## The mask, and why permissions "do not apply"

The `mask` is an upper bound on every **named** user, every named group,
and the owning group. An entry of `rwx` under a mask of `r--` grants only
`r`. `chmod g+w file` on a file with an ACL changes the **mask**, not the
group entry - which is why ACLs sometimes appear to stop working after a
chmod.

```bash
getfacl report.txt | grep -E "mask|effective"
# group:qa:rwx                 #effective:r--     ← the mask is limiting it
setfacl -m m:rwx report.txt    # raise the mask
```

Read `#effective:` in `getfacl` output as "what this entry actually
grants".

## Default ACLs: inheritance

A **default** ACL on a directory is inherited by everything created inside
it - the ACL equivalent of SGID.

```bash
setfacl -d -m u:bob:rwx /srv/project          # -d = default
setfacl -d -m g:devs:rwx /srv/project
setfacl -d -m o::--- /srv/project
getfacl /srv/project
# default:user:bob:rwx
# default:group:devs:rwx
touch /srv/project/newfile
getfacl /srv/project/newfile                   # bob and devs are already there
setfacl -k /srv/project                        # remove the default ACL
```

The complete recipe for a shared project directory with an extra guest:

```bash
sudo mkdir -p /srv/project
sudo chgrp devs /srv/project
sudo chmod 2770 /srv/project                        # SGID: group ownership inherited
sudo setfacl -m u:bob:rwx /srv/project              # bob, who is not in devs
sudo setfacl -d -m u:bob:rwx /srv/project           # ...and on everything created later
sudo setfacl -d -m g:devs:rwx /srv/project
getfacl /srv/project
```

## Backing up and restoring ACLs

```bash
getfacl -R /srv/project > acl-backup.txt
setfacl --restore=acl-backup.txt
cp -a src dst                     # -a preserves ACLs
rsync -aHAX src/ dst/             # -A ACLs, -X extended attributes
tar --acls --xattrs -czf backup.tar.gz /srv/project
```

Plain `cp` and plain `tar` **drop** ACLs - the reason a restored directory
suddenly has different access.

## File attributes: chattr

A different mechanism, enforced by the filesystem itself, that even root
must lift before writing:

```bash
lsattr file.txt
sudo chattr +i /etc/resolv.conf        # IMMUTABLE: cannot be modified, deleted, renamed, or linked - even by root
sudo chattr -i /etc/resolv.conf
sudo chattr +a /var/log/audit.log      # APPEND-ONLY: writes may only add to the end
sudo chattr +A file                    # do not update atime
sudo chattr -R +i /etc/critical/
lsattr -d /etc/critical/
```

```bash
sudo lsattr /etc/resolv.conf
# ----i---------e------- /etc/resolv.conf
```

`+i` is the answer to "something keeps rewriting this file" (a DHCP client
overwriting `resolv.conf`, for instance) - and the cause of the
head-scratching "Operation not permitted" as root. `lsattr` is the first
thing to check when root cannot delete a file.

## Extended attributes

ACLs, SELinux contexts and capabilities are all stored as **xattrs**:

```bash
getfattr -d -m - file                       # every xattr
getfattr -n security.selinux file
sudo setfattr -n user.comment -v "reviewed" file
sudo setcap cap_net_bind_service=+ep /usr/local/bin/myserver   # bind port 80 without being root
getcap /usr/local/bin/myserver
sudo setcap -r /usr/local/bin/myserver
```

`setcap` is the modern alternative to a SUID binary: grant one capability
instead of full root.

## Diagnosing access problems

```bash
namei -l /srv/project/data/file.txt        # permissions of EVERY component of the path
getfacl file; ls -l file; lsattr file
id bob; groups bob
sudo -u bob cat /srv/project/data/file.txt        # test as the user
sudo -u bob test -w /srv/project && echo writable
ls -Z file                                         # SELinux, if enforcing (week 7)
```

The order to check: path traversal (`namei -l`), then owner/group/mode,
then ACL and its mask, then attributes (`lsattr`), then SELinux/AppArmor.

:::exam-tip
"Give user X read-write access to file F without changing its group" →
`setfacl -m u:X:rw F`, verified with `getfacl F`. "...and to everything
created in directory D afterwards" → `setfacl -d -m u:X:rwx D`. If
permissions look right but access is denied, check the **mask**
(`#effective:`) and `lsattr`.
:::

## Check yourself

1. What does the `+` at the end of an `ls -l` mode mean?
2. What is the ACL mask, and why can `chmod g+w` break an ACL?
3. Root cannot delete a file and gets "Operation not permitted". What do
   you check?
