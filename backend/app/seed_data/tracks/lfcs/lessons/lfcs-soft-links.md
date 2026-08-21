## A soft link is a file that contains a path

A **symbolic (soft) link** is its own small file whose content is a
**path** to another name. Opening the link follows the path. It does not
share an inode with the target; it points at a *name*, not at the data.

```bash
ln -s /var/log/syslog currentlog          # ln -s TARGET LINKNAME
ls -l currentlog
# lrwxrwxrwx 1 ahmad ahmad 15 Aug 19 10:05 currentlog -> /var/log/syslog
```

`l` at the start, `-> target` at the end, and the size (15) is the length
of the path string. The permissions shown on a symlink are always
`rwxrwxrwx` and mean nothing - the **target's** permissions apply.

## What soft links can do that hard links cannot

| | hard link | soft link |
|---|---|---|
| to a directory | no | **yes** - the common case: `/usr/lib/jvm/default -> java-17` |
| across filesystems | no | **yes** |
| to a target that does not exist (yet) | no | yes - a **dangling** link |
| survives the target being deleted | yes (it *is* the file) | no - dangles |
| survives the target being replaced (rm + new file) | no (points at the old inode) | yes - follows the name |
| own inode, own permissions | no | yes (but permissions unused) |

## Relative vs absolute targets

The path stored in the link is used **literally**, relative to the link's
own directory:

```bash
cd /opt/app
ln -s releases/v2 current              # relative: /opt/app/current -> releases/v2 ; resolves to /opt/app/releases/v2
ln -s /opt/app/releases/v2 current     # absolute
```

Relative links survive moving the whole tree (`mv /opt/app /srv/app` -
`current` still finds `releases/v2` next to it); absolute links survive
moving the link alone. Pick relative for links inside a tree that moves
together; absolute for pointers into fixed system locations.

The classic mistake is making a relative link from the wrong directory:

```bash
ln -s releases/v2 /opt/app/current     # from /, but the path is relative to /opt/app - fine here
ln -s /opt/app/releases/v2 /opt/app/current   # safest when you are not in /opt/app
```

## Inspecting and fixing

```bash
readlink current                       # what it points at, literally
readlink -f current                    # fully resolved, absolute, all links followed
ls -l current                          # -> shown; a red/blinking one in most terminals = dangling
file current                           # "symbolic link to releases/v2" / "broken symbolic link to ..."
find /opt -xtype l                     # every dangling symlink under /opt
ln -sfn releases/v3 current            # -f replace existing; -n do not descend into a link-to-directory
rm current                             # removes the link, never the target (mind: no trailing slash!)
```

:::warning
`rm current/` with a trailing slash on a link to a directory, or `rm -r
current` - both can reach into the target. `rm current` (no slash) removes
only the link. And `ln -s new current` when `current` already links to a
directory creates `current/new` *inside* the target - use `ln -sfn`.
:::

## Seeing links in the wild

```bash
ls -l /etc/alternatives/ | head          # Debian's alternatives: symlinks choosing between versions
ls -l /etc/systemd/system/multi-user.target.wants/   # "enabled" units are symlinks to unit files (week 5)
ls -l /dev/disk/by-uuid/                 # stable names for disks are symlinks to /dev/sdX (week 11)
ls -l /bin                               # /bin -> usr/bin on merged-/usr systems
```

Half of system configuration is symlinks; reading `->` fluently is a daily
skill.

:::exam-tip
"Create a symbolic link `/usr/local/bin/app` pointing to
`/opt/app/bin/app-2.1`": `ln -s /opt/app/bin/app-2.1 /usr/local/bin/app`.
Verify with `ls -l /usr/local/bin/app` and `readlink -f`. Remember the
order: **target first, link name second** - the same as `cp source dest`.
:::

## Check yourself

1. What does a soft link actually contain, and what happens when its
   target is deleted?
2. When would you use a relative target and when an absolute one?
3. Why does `ln -s new current` sometimes create `current/new`, and which
   flags prevent it?
