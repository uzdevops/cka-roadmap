## A file is an inode; a name is a link

On a Linux filesystem a file's **data and metadata** (permissions, owner,
timestamps, size, where the blocks are) live in an **inode**, identified
by a number. A **filename** in a directory is just an entry that points at
an inode number. Create a second entry pointing at the same inode, and the
file has two names. That second entry is a **hard link**.

```
 directory entries                 inode 5281 (mode, owner, size, blocks, link count = 2)
   report.txt  ──▶ 5281 ◀──  final.txt
```

```bash
echo "draft" > report.txt
ln report.txt final.txt             # ln TARGET LINKNAME
ls -li report.txt final.txt
# 5281 -rw-r--r-- 2 ahmad ahmad 6 Aug 19 10:00 final.txt
# 5281 -rw-r--r-- 2 ahmad ahmad 6 Aug 19 10:00 report.txt
```

`-i` shows the inode: **the same number**. The `2` after the mode is the
**link count** - how many names point at this inode.

## Consequences

- Edit through either name and both show the change - there is only one
  file.
- `rm report.txt` removes **one name**; the link count drops to 1; the
  data stays, reachable as `final.txt`. The data is freed only when the
  count reaches **0** and no process has it open.
- Permissions, owner, size and timestamps are per-inode, so they are
  identical through every name; `chmod` through one is `chmod` through all.
- `ls -l` on a directory shows the link count for directories too: `.`
  inside it and every subdirectory's `..` point at it, so an empty
  directory has 2 and one with three subdirectories has 5.

```bash
stat report.txt                     # Inode: 5281   Links: 2
find / -samefile report.txt 2>/dev/null    # every name of this inode
find /data -inum 5281
find /data -type f -links +1        # files with more than one name
rm report.txt; cat final.txt        # still "draft"
```

## Limits of hard links

| Cannot | Why |
|---|---|
| link across **filesystems** | an inode number is meaningful only inside its own filesystem; `ln: failed to create hard link ... Invalid cross-device link` |
| link a **directory** | would allow loops in the tree; only `.` and `..` are permitted (the kernel makes those) |
| tell which name is "the original" | there is none; all names are equal |

Soft links (next lesson) exist precisely for those two cases.

## Why use them

- A file that must appear in two places and stay **identical** with no
  copy to drift (a config under two names; a library's versioned and
  unversioned name).
- Backup schemes (`rsync --link-dest`, `cp -al`): unchanged files are hard
  links to the previous snapshot, so ten daily backups of a 100 GB tree
  that barely changes cost little more than 100 GB.
- Safety against deletion: as long as one name exists, the data exists.

```bash
cp -al snapshot.0 snapshot.1        # an instant "copy" by hard-linking every file
```

## Reading ls -l with links in mind

```
-rw-r--r-- 2 ahmad ahmad 6 Aug 19 10:00 final.txt
           ^ link count: 2 names for this inode
drwxr-xr-x 5 ahmad ahmad 4096 ... projects   <- 5 = . + .. entries of 3 subdirectories... (2 + 3)
```

:::exam-tip
"Create a hard link to `/etc/app/config` named `/etc/app/config.bak`" is
`ln /etc/app/config /etc/app/config.bak`. Verify with `ls -li` - same
inode, link count 2. If the task's two paths are on different filesystems
(`/boot` and `/home`, say), a hard link is impossible and a symbolic link
is the answer - the task usually says which.
:::

## Check yourself

1. What does the number after the permissions in `ls -l` mean, and what
   happens to a file's data when it reaches zero?
2. Name the two things a hard link cannot do.
3. How do you find every name that refers to the same file as
   `/var/app/data.db`?
