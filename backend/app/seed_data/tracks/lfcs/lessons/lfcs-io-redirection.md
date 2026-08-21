## Three streams

Every process starts with three open file descriptors:

| FD | Name | Default |
|---|---|---|
| **0** | stdin | the keyboard |
| **1** | stdout | the terminal |
| **2** | stderr | the terminal |

Redirection re-points them at files, or at each other, or at another
process. That is the whole idea, and it is what makes small commands
compose.

## Output

```bash
ls > files.txt              # stdout to a file, TRUNCATING it
ls >> files.txt             # append
ls /nope 2> errors.txt      # stderr to a file
ls /nope 2>> errors.txt     # append stderr
ls > out.txt 2> err.txt     # separately
ls > all.txt 2>&1           # stderr to WHERE STDOUT NOW GOES - order matters
ls &> all.txt               # bash shorthand for the same
ls &>> all.txt              # appending shorthand
command > /dev/null         # discard stdout
command 2> /dev/null        # discard errors (find, grep on /proc...)
command > /dev/null 2>&1    # discard everything
command 2>&1 > file         # WRONG for "everything to file": stderr goes to the terminal, stdout to file
```

`2>&1` means "make FD 2 a copy of FD 1 **as it is now**". Put it **after**
the stdout redirect, or the copy is of the terminal.

## Input

```bash
sort < unsorted.txt              # stdin from a file
mysql -u root < dump.sql
while read line; do echo "$line"; done < /etc/passwd

cat <<EOF > /etc/motd            # here-document: text until EOF
Welcome to $(hostname)
EOF

cat <<'EOF' > script.sh          # quoted delimiter: NO variable expansion
echo $HOME stays literal
EOF

cat <<-EOF                       # <<- strips leading TABS (for indented scripts)
	indented
	EOF

grep root <<< "root:x:0:0"       # here-string: one line as stdin
```

## Pipes

```bash
ps aux | grep nginx | wc -l
journalctl -u sshd | grep Failed | awk '{print $NF}' | sort | uniq -c | sort -rn
cat /etc/passwd | cut -d: -f1 | sort        # (cat is redundant: cut -d: -f1 /etc/passwd | sort)
command1 |& command2                        # bash: pipe stdout AND stderr
command 2>&1 | less                         # the portable form of the same
```

A pipe connects the left command's **stdout** to the right command's
**stdin**; stderr is not piped unless you redirect it in. The exit status
of a pipeline is the **last** command's, unless `set -o pipefail`.

## tee: to a file *and* onward

```bash
ls | tee files.txt                      # write to file AND print
ls | tee -a files.txt                   # append
make 2>&1 | tee build.log | tail -20    # log everything, show the end
echo "net.ipv4.ip_forward=1" | sudo tee /etc/sysctl.d/99-fw.conf    # the way to write a root-owned file from a pipe
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward > /dev/null
```

`sudo command > /root/file` fails - the **shell** opens the file, as you,
before sudo runs. `| sudo tee file` is the fix.

## Other file descriptors

```bash
exec 3> /tmp/log             # open FD 3 for writing
echo "hello" >&3
exec 3>&-                    # close it
command 3>&1 1>&2 2>&3       # swap stdout and stderr
diff <(sort a) <(sort b)     # process substitution: each becomes a /dev/fd/N "file"
wc -l < <(grep ERROR log)
comm -13 <(sort a) <(sort b)
```

## Odds and ends worth knowing

```bash
command < /dev/null              # give a command no input (for daemons, cron)
: > file                        # truncate a file to zero without deleting it
> file                          # the same, shorter
nohup long-job > job.log 2>&1 &  # survive logout, log everything
yes | apt install pkg            # feed 'y' forever
xargs                            # turn stdin into ARGUMENTS (not stdin): find ... | xargs rm
echo /etc/*.conf | xargs ls -l
```

The `xargs` distinction matters: `echo file | rm` does nothing (rm reads
no stdin); `echo file | xargs rm` deletes it.

:::exam-tip
Redirection appears inside almost every exam task: "save the output to
/root/x.txt" → `> /root/x.txt`; "including errors" → `> file 2>&1`;
"append" → `>>`; "write a root-owned file from a pipeline" → `| sudo tee`.
Check the result with `cat` - an empty file usually means the output was
on stderr and you only redirected stdout.
:::

## Check yourself

1. Why does `command 2>&1 > file` not send errors to the file?
2. How do you write to a file that requires root, from inside a pipeline?
3. What is the difference between `|` and `xargs`?
