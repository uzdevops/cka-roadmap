## The everyday verbs

Create, look, copy, move, remove. The commands are small; the flags and
the globs are what make them fast.

```bash
pwd; cd /var/log; cd -; cd ~; cd ..          # where am I, back, home, up
ls -la; ls -lh; ls -lt; ls -ltr; ls -R; ls -d */   # long, human sizes, by time, reverse, recursive, dirs only
```

## Create

```bash
touch notes.txt                  # empty file, or update the mtime of an existing one
touch a.txt b.txt c.txt
mkdir reports                    # one directory
mkdir -p projects/2026/q3        # parents as needed, no error if it exists
mkdir -m 750 private             # with a mode
mkdir {dev,stage,prod}           # brace expansion: three directories
```

## Copy

```bash
cp file.txt copy.txt
cp file.txt /tmp/                # into a directory, same name
cp -r projects/ /backup/         # recursive for directories
cp -a projects/ /backup/         # archive: recursive + preserve mode, owner, timestamps, links
cp -i a b                        # ask before overwriting
cp -n a b                        # never overwrite
cp -v *.conf /etc/app/           # verbose
cp -p file.txt /tmp/             # preserve mode/ownership/timestamps (one file)
```

`cp dir/ dst/` vs `cp dir dst/`: with `-r`, a trailing slash on the
**destination** means "into"; whether `dst` already exists decides whether
you get `dst/dir` or `dst` as a copy of `dir`. When in doubt, `ls dst`
after.

## Move and rename

```bash
mv old.txt new.txt               # rename
mv file.txt /archive/            # move
mv -i a b; mv -n a b             # ask / never overwrite
mv dir1 dir2                     # rename a directory, or move it into dir2 if dir2 exists
mv *.log /var/log/old/
```

`mv` is atomic on the same filesystem (a rename) and a copy+delete across
filesystems.

## Remove

```bash
rm file.txt
rm -i *.tmp                      # ask each
rm -r olddir/                    # recursive
rm -rf build/                    # recursive, no prompts, no errors for missing - the dangerous one
rmdir emptydir                   # only empty directories - safe
rmdir -p a/b/c                   # remove the chain if all empty
rm -- -weird-name                # a file starting with -
rm ./-weird-name
```

:::warning
`rm -rf` with a variable that is empty or a glob that matches more than
you meant has destroyed more servers than any attacker. Before `rm -rf
$DIR/*`, `echo rm -rf $DIR/*` - look at what expands. And never alias `rm`
to `rm -i` and rely on it; the habit does not transfer to the next machine.
:::

## Globs: patterns the shell expands

| Pattern | Matches |
|---|---|
| `*` | any string, including empty (not a leading `.`) |
| `?` | exactly one character |
| `[abc]`, `[a-z]`, `[0-9]` | one character from the set/range |
| `[!abc]` or `[^abc]` | one character not in the set |
| `{a,b,c}` | brace expansion: each alternative (not a glob - expands even if no file exists) |
| `{1..5}`, `{a..e}`, `{01..10}` | sequences |
| `.*` | dot-files (hidden) - `*` alone skips them; `ls -A` shows them |

```bash
ls *.log                         # every .log in this directory
ls file?.txt                     # file1.txt, fileA.txt, not file10.txt
ls [a-c]*                        # names starting a, b or c
cp report_{2024,2025}.pdf /tmp/  # two files
mkdir day{01..07}                # seven directories
rm -- *.tmp                      # `--` ends options; protects against names starting with -
echo *                           # see what a glob expands to before using it in rm
```

Globs are expanded by the **shell**, before the command runs: `rm *.txt`
becomes `rm a.txt b.txt c.txt`. Quote to prevent it (`'*.txt'`) when the
command should see the pattern - `find -name '*.txt'` next lesson.

## Looking before you leap

```bash
ls -l target/                    # what is there
file something                   # what kind of file is it (text, ELF, directory, gzip...)
stat file.txt                    # size, inode, permissions, three timestamps
du -sh dir/                      # how big
tree -L 2 dir/                   # if installed
```

:::exam-tip
Tasks say "create directory X with subdirectories Y/Z" - `mkdir -p X/Y/Z`;
"copy directory A to B preserving permissions" - `cp -a`; "remove all
`.tmp` files under /var/app" - `find` (next lesson), not `rm -r`. Always
`ls` the result; the grader checks the end state, not the command.
:::

## Check yourself

1. What is the difference between `cp -r` and `cp -a`?
2. Write one command that creates `proj/src`, `proj/test` and `proj/docs`.
3. Why is `echo rm -rf $DIR/*` a good habit before `rm -rf $DIR/*`?
