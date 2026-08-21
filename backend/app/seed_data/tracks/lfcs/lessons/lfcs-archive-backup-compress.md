## tar: one file out of many

`tar` ("tape archive") packs a directory tree into a single file, keeping
names, permissions, owners, timestamps and links. It does **not** compress
by itself - it calls gzip, bzip2 or xz for that, through a flag.

```bash
tar -cvf backup.tar /etc/nginx          # create, verbose, file
tar -czvf backup.tar.gz /etc/nginx      # + gzip      (.tar.gz / .tgz)
tar -cjvf backup.tar.bz2 /etc/nginx     # + bzip2     (.tar.bz2)
tar -cJvf backup.tar.xz /etc/nginx      # + xz        (.tar.xz)
```

| Flag | Means |
|---|---|
| `-c` | **c**reate |
| `-x` | e**x**tract |
| `-t` | lis**t** contents |
| `-f FILE` | the archive **f**ile - always last among the bundled letters, immediately before the name |
| `-v` | verbose |
| `-z` `-j` `-J` | gzip / bzip2 / xz |
| `-C DIR` | change to DIR first (extract **into**, or archive **from**) |
| `-p` | preserve permissions (default for root on extract) |
| `--exclude=PATTERN` | skip matches |
| `-r` / `-u` | append / append-if-newer (uncompressed archives only) |
| `--strip-components=N` | drop N leading path elements on extract |

## The three verbs

```bash
tar -czf /backup/etc-$(date +%F).tar.gz /etc                  # create
tar -tzf /backup/etc-2026-08-21.tar.gz | head                 # list - always look before extracting
tar -xzf /backup/etc-2026-08-21.tar.gz -C /restore            # extract into a directory
tar -xzf archive.tar.gz etc/nginx/nginx.conf                   # extract one member
tar -xzf archive.tar.gz --wildcards '*.conf'                   # extract by pattern
```

Modern tar auto-detects compression on extract (`-xaf`, or just `-xf`), so
`tar -xf whatever.tar.xz` works; on **create** you must say which.

## Paths: absolute vs relative

```bash
tar -czf backup.tar.gz /etc/nginx
# tar: Removing leading `/' from member names
```

tar stores `etc/nginx/...` (relative) so extraction cannot overwrite `/etc`
by accident - it lands under the current directory. To restore in place:

```bash
cd / && tar -xzf /backup/backup.tar.gz          # recreates /etc/nginx
tar -xzf /backup/backup.tar.gz -C /             # the same, without cd
```

Archiving from inside the parent keeps the tree tidy:

```bash
tar -czf nginx.tar.gz -C /etc nginx             # members are nginx/... not etc/nginx/...
```

## Excluding and selecting

```bash
tar -czf home.tar.gz --exclude='*.iso' --exclude='.cache' /home/ahmad
tar -czf src.tar.gz --exclude-vcs project/
tar -czf logs.tar.gz $(find /var/log -name '*.log' -mtime -1)
tar -czf sel.tar.gz -T filelist.txt             # names from a file
```

Put `--exclude` **before** the paths; patterns are globs matched against
the stored (relative) names.

## Incremental and snapshot-ish backups

```bash
tar -czf full.tar.gz -g snapshot.snar /data          # level 0: everything, records state
tar -czf inc1.tar.gz -g snapshot.snar /data          # level 1: only what changed since
```

`-g` (`--listed-incremental`) keeps a state file; restore by extracting the
full archive then each increment in order. For most jobs `rsync` (two
lessons on) is simpler.

## Verifying and permissions

```bash
tar -tzvf backup.tar.gz | head          # long listing: modes, owners, sizes, dates
tar -dzf backup.tar.gz -C /             # diff archive against the filesystem
sha256sum backup.tar.gz > backup.tar.gz.sha256
sha256sum -c backup.tar.gz.sha256
```

Extracting as root restores original owners and permissions; as a normal
user, files become yours (`--no-same-owner` is the default for non-root,
`--same-owner` for root). A backup of `/etc` restored by a non-root user
is not a working `/etc`.

## Other archivers you may meet

```bash
cpio -o < list > archive.cpio; cpio -idmv < archive.cpio     # initramfs images use it
zip -r site.zip site/; unzip -l site.zip; unzip site.zip -d /var/www    # cross-platform
dd if=/dev/sda of=/backup/disk.img bs=4M status=progress      # raw block copy (week 11)
```

:::warning
Never extract an untrusted archive into a sensitive directory without
listing it first (`tar -tf`). Archives can contain `../` paths or absolute
paths crafted to overwrite files outside the target - GNU tar strips them
by default, but the habit of looking first costs one command.
:::

:::exam-tip
Exam wording maps directly: "create a gzip-compressed archive of /etc/skel
at /root/skel.tar.gz" → `tar -czf /root/skel.tar.gz -C /etc skel`;
"extract /tmp/data.tar.bz2 into /srv" → `tar -xjf /tmp/data.tar.bz2 -C
/srv`; "list the contents" → `tar -tf`. Then verify with `tar -tf` or `ls`
the destination.
:::

## Check yourself

1. What do `-c`, `-x`, `-t` and `-f` do, and why must `-f` come last among
   grouped flags?
2. Why does tar strip the leading `/`, and how do you restore an archive in
   place?
3. Write the command that archives `/var/www` as xz-compressed
   `/backup/www.tar.xz`, excluding `*.log`.
