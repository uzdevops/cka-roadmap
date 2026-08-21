## The text toolbox

Configuration, logs, CSV exports, command output - on Linux it is all
text, and these small commands, piped together, do most of what a
spreadsheet or a script would. Learn them as verbs: show, slice, sort,
count, replace, compare.

## Show

```bash
cat file                      # whole file; cat a b > c joins
cat -n file                   # numbered lines; -A shows tabs/line ends
tac file                      # reversed
head -n 5 file; head -5 file  # first lines (default 10)
tail -n 5 file; tail -f /var/log/syslog   # last lines; -f follows growth; -F survives rotation
tail -n +20 file              # from line 20 to the end
less file                     # page (next lesson)
wc -l file; wc -w; wc -c      # lines, words, bytes
```

## Slice

```bash
cut -d: -f1 /etc/passwd               # field 1 of colon-separated
cut -d: -f1,7 /etc/passwd             # fields 1 and 7
cut -d, -f2- data.csv                 # from field 2 on
cut -c1-10 file                       # characters 1-10
awk -F: '{print $1, $3}' /etc/passwd  # when cut is not enough: fields by number, any separator, conditions
awk -F: '$3 >= 1000 {print $1}' /etc/passwd        # users with uid >= 1000
awk '{print $NF}' file                # last field
```

`cut` needs a single-character delimiter and cannot handle runs of spaces
well; `awk` splits on whitespace by default and can test and compute.

## Sort and count

```bash
sort file                 # alphabetical
sort -n file              # numeric
sort -r file              # reverse
sort -k2 file             # by field 2 (whitespace-separated)
sort -t: -k3 -n /etc/passwd        # by field 3, numeric, colon-separated
sort -u file              # unique (sorted)
sort -h sizes             # human sizes: 1K 2M 3G
uniq file                 # collapse ADJACENT duplicates - sort first!
uniq -c file              # with counts
uniq -d file              # only the duplicated lines
uniq -u                   # only the unique ones
sort file | uniq -c | sort -rn | head      # the classic "top N most frequent"
```

```bash
cut -d' ' -f1 access.log | sort | uniq -c | sort -rn | head -5     # top 5 client IPs
awk '{print $9}' access.log | sort | uniq -c                        # HTTP status counts
```

## Transform

```bash
tr a-z A-Z < file                 # translate characters
tr -d '\r' < dos.txt > unix.txt   # delete characters
tr -s ' ' < file                  # squeeze repeats
tr ':' '\t' < /etc/passwd
sed 's/old/new/' file             # first occurrence per line, to stdout
sed 's/old/new/g' file            # every occurrence
sed -i 's/old/new/g' file         # in place (-i.bak keeps a backup)
sed -n '10,20p' file              # print lines 10-20 only
sed '/^#/d' file                  # delete comment lines
sed '/^$/d' file                  # delete empty lines
sed -i 's/^#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed 's#/old/path#/new/path#g'     # any delimiter when the pattern has slashes
```

`sed` is the line editor for scripts: `s/pattern/replacement/flags`,
addresses (`10,20`, `/regex/`), `d` delete, `p` print with `-n`, `-i` to
write back.

```bash
paste a.txt b.txt                 # side by side, tab-separated
paste -d, a b
join -t: a.txt b.txt              # join on a common first field (both sorted)
split -l 1000 big.log part_       # split into files of 1000 lines
rev file; nl file; fold -w 80 file; column -t file; expand/unexpand
```

## Compare

```bash
diff a.conf b.conf                # ed-style: 3c3 (changed), 5a6 (added), 8d7 (deleted)
diff -u a.conf b.conf             # unified: -/+ lines with context - what patch and git show
diff -r dir1 dir2                 # directories
diff -q a b                       # just "differ" or nothing
diff -y a b; sdiff a b            # side by side
cmp a.bin b.bin                   # first differing byte; for binaries
comm -12 <(sort a) <(sort b)      # lines in both; -23 only in a; -13 only in b
md5sum file; sha256sum file; sha256sum -c SUMS     # same content?
```

## Putting it together

```bash
grep -v '^#' /etc/ssh/sshd_config | grep -v '^$'                  # effective config
awk -F: '$7 ~ /bash/ {print $1}' /etc/passwd | sort               # users with bash
du -sh /var/* 2>/dev/null | sort -rh | head                        # biggest under /var
journalctl -p err -o cat | sort | uniq -c | sort -rn | head        # most frequent errors
ps aux --sort=-%mem | head -5 | awk '{print $2, $4, $11}'           # top memory PIDs
```

:::exam-tip
Tasks in this domain are "produce file X containing Y from Z": the answer
is a pipeline ending in `> X`. Build it left to right, checking each stage's
output on screen, then add the redirect. `sort` before `uniq`, `-n` for
numbers, `-t`/`-d` for delimiters, `sed -i` only once you have seen the
`sed` output without `-i`.
:::

## Check yourself

1. Why must `sort` come before `uniq`?
2. Write the pipeline that lists the five most common shells in
   `/etc/passwd` with counts.
3. What is the difference between `sed 's/a/b/' f` and `sed -i 's/a/b/g'
   f`?
