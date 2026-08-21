## Copying to another machine

Two tools: `scp` copies files, `rsync` synchronises trees. Both ride on
SSH, so both use your SSH keys, ports and `~/.ssh/config`.

## scp: simple copies

```bash
scp file.txt user@host:/tmp/                    # local → remote
scp user@host:/etc/nginx/nginx.conf ./          # remote → local
scp -r site/ user@host:/var/www/                # recursive
scp -P 2222 file user@host:/tmp/                # non-default port (capital P!)
scp -p file user@host:/tmp/                     # preserve times/modes
scp -i ~/.ssh/deploy_key file user@host:/tmp/
scp user@host1:/f user@host2:/f                 # between two remotes (via your machine, or -3)
```

`scp` re-copies everything every time and has no resume. It is fine for one
file; for a directory that will be copied more than once, use rsync.

## rsync: copy only what changed

```bash
rsync -av /data/ user@host:/backup/data/         # the everyday form
rsync -avz /data/ user@host:/backup/data/        # + compression on the wire
rsync -av --delete /data/ user@host:/backup/data/    # make the destination MATCH (removes extras)
rsync -av --dry-run --delete /data/ host:/backup/    # ALWAYS dry-run --delete first
rsync -av -e 'ssh -p 2222' /data/ host:/backup/
rsync -av --progress big.iso host:/tmp/          # progress, resumable via --partial
rsync -av --exclude='*.tmp' --exclude='.cache/' /home/ /backup/home/
rsync -av --include='*.conf' --exclude='*' /etc/ /backup/etc-conf/
rsync -avn /data/ /backup/data/                  # -n = dry run, show what would happen
```

| Flag | Means |
|---|---|
| `-a` | archive: recursive + preserve permissions, times, symlinks, owners, groups (`-rlptgoD`) |
| `-v` | verbose; `--progress` per-file progress |
| `-z` | compress during transfer |
| `--delete` | delete destination files that no longer exist at the source |
| `-n` / `--dry-run` | show, do nothing |
| `--exclude` / `--include` | patterns, evaluated in order |
| `-e` | the remote shell command |
| `--partial` / `-P` | keep partial files so a retry resumes (`-P` = `--partial --progress`) |
| `--link-dest=DIR` | hard-link unchanged files from DIR - cheap snapshots |
| `--bwlimit=5000` | throttle KB/s |

## The trailing slash

The single most important detail in rsync:

```bash
rsync -av /data  /backup/     # → /backup/data/...     (copies the DIRECTORY)
rsync -av /data/ /backup/     # → /backup/...          (copies its CONTENTS)
```

Source with a slash means "the contents of"; without, "the directory
itself". The destination's slash does not matter. Getting this wrong
produces `/backup/data/data/` or a flattened mess - `--dry-run` shows it
in one second.

## Snapshot backups with --link-dest

```bash
DEST=/backup/$(date +%F)
rsync -a --delete --link-dest=/backup/latest /data/ "$DEST/"
ln -sfn "$DEST" /backup/latest
```

Unchanged files become hard links to yesterday's copy (see the hard-links
lesson): thirty daily snapshots of a mostly-static 100 GB tree cost barely
more than 100 GB, and each snapshot is a complete browsable tree.

## Pull, push, and over a pipe

```bash
rsync -av user@host:/var/log/ /local/logs/        # pull
ssh host 'tar -czf - /etc' > etc-$(date +%F).tar.gz    # archive a remote host locally
tar -czf - /data | ssh host 'cat > /backup/data.tar.gz'
```

## Automating it

```bash
ssh-keygen -t ed25519 -f ~/.ssh/backup_key -N ''       # no passphrase, for cron
ssh-copy-id -i ~/.ssh/backup_key.pub backup@host
crontab -e
# 0 2 * * * rsync -a --delete -e 'ssh -i /home/ahmad/.ssh/backup_key' /data/ backup@host:/backup/data/ >> /var/log/backup.log 2>&1
```

(Keys and `sshd` hardening are week 10; cron is week 6. The pattern - key
without passphrase, restricted user, logged output - is the standard.)

:::warning
`--delete` makes the destination match the source, including deletions. A
typo in the source path (an empty or wrong directory) plus `--delete`
empties the backup. Run it with `-n` first, every time, and consider
`--delete-after` plus snapshots so a bad run is recoverable.
:::

:::exam-tip
"Synchronise /var/www to host2:/var/www preserving permissions" →
`rsync -av /var/www/ host2:/var/www/` (mind the trailing slash). "Copy a
single file to a remote host on port 2222" → `scp -P 2222 file
user@host:/path`. Verify with `ls -l` on the destination or a second rsync
run that reports nothing to transfer.
:::

## Check yourself

1. What is the difference between `rsync -av /data /backup/` and
   `rsync -av /data/ /backup/`?
2. What does `-a` include, and why is it the default habit?
3. Why must `--delete` always be preceded by a dry run?
