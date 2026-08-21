## The three compressors

Each takes a file, replaces it with a compressed one, and reverses on
request. They differ in speed and ratio, and tar has a flag for each.

| Tool | Extension | tar flag | Speed | Ratio | Notes |
|---|---|---|---|---|---|
| `gzip` | `.gz` | `-z` | fastest | good | the default everywhere |
| `bzip2` | `.bz2` | `-j` | slow | better | older, being displaced |
| `xz` | `.xz` | `-J` | slowest | best | kernel/distribution archives |
| `zstd` | `.zst` | `--zstd` | fast | very good | the modern choice where available |

## gzip

```bash
gzip file.txt                # → file.txt.gz, the ORIGINAL IS REPLACED
gzip -k file.txt             # keep the original
gzip -9 file.txt             # best compression (-1 fastest)
gzip -r logs/                # every file in the tree, individually
gunzip file.txt.gz           # or: gzip -d
zcat file.txt.gz             # read without decompressing to disk
zless, zgrep 'ERROR' f.gz, zdiff a.gz b.gz     # the z-tools work on .gz directly
gzip -l archive.gz           # compressed/uncompressed sizes and ratio
gzip -t archive.gz           # test integrity
```

The surprise for beginners: `gzip file` **removes** `file`. Use `-k`, or
compress a copy, or (better) compress an archive rather than the original
data.

## bzip2 and xz

```bash
bzip2 -k big.log; bunzip2 big.log.bz2; bzcat big.log.bz2; bzgrep ERROR big.log.bz2
xz -k big.log;    unxz big.log.xz;     xzcat big.log.xz;  xzgrep ERROR big.log.xz
xz -9 -T0 big.log            # max compression, all CPU threads
zstd -k -19 big.log; unzstd big.log.zst; zstdcat big.log.zst
```

The interfaces mirror gzip's deliberately: `-k` keep, `-d` decompress,
`-1..-9` level, `-t` test, plus the `*cat`, `*grep`, `*less` family.

## zip and unzip: the cross-platform one

```bash
zip archive.zip file1 file2          # zip both archives AND compresses (unlike tar)
zip -r site.zip site/                # recursive
zip -e secret.zip file               # password (weak - not real encryption)
unzip archive.zip                    # into the current directory
unzip -l archive.zip                 # list
unzip archive.zip -d /var/www        # into a directory
unzip -o archive.zip                 # overwrite without asking
```

Use zip when the other end is Windows; use tar+gzip for anything Unix -
zip does not preserve owners, permissions or symlinks reliably.

## Choosing, in practice

- **Logs, backups, anything you may need in a hurry**: `gzip` (`tar -czf`).
- **Long-term archives, distribution images, where CPU time is cheap and
  bytes are not**: `xz` (`tar -cJf`).
- **Sending to a non-Linux user**: `zip`.
- **Already-compressed data** (jpg, mp4, .gz, rpm/deb): do not compress
  again - you spend CPU to add bytes.

```bash
ls -lh big.log*                       # compare the results
for c in gzip bzip2 xz; do cp big.log t; $c -9 t; ls -lh t.*; rm -f t.*; done
```

## Compression without files: pipes

```bash
tar -cf - /data | gzip -9 > data.tar.gz               # tar to stdout, compress in the pipe
mysqldump db | gzip > db.sql.gz                        # compress a stream, never touch disk uncompressed
gzip -dc data.tar.gz | tar -xf - -C /restore
ssh host 'tar -czf - /etc' > etc-remote.tar.gz         # archive a remote host into a local file
dd if=/dev/sda bs=4M | gzip > disk.img.gz
```

`-` as a filename means stdin/stdout; this is how backups get made without
double disk usage.

:::exam-tip
Know both directions for all three: `gzip`/`gunzip`, `bzip2`/`bunzip2`,
`xz`/`unxz`, and the matching tar flags `-z -j -J`. If a task says
"compress the file, keeping the original", it is `-k`. If it says "read
the compressed log without extracting", it is `zcat`/`zgrep`.
:::

## Check yourself

1. What happens to `report.txt` when you run `gzip report.txt`, and how do
   you avoid it?
2. Which compressor for a long-term archive and which for a nightly log
   rotation, and why?
3. How do you grep a `.gz` log file without decompressing it to disk?
