## A grammar for patterns

A regular expression describes a set of strings. `grep`, `sed`, `awk`,
`vi`'s `/` and `:s`, `less`, `find -regex` - all speak it. **Basic**
regular expressions (BRE) are what `grep` and `sed` use by default; the
next lesson adds the extended operators. This one is the core everyone
needs.

## Literals and the dot

| Pattern | Matches |
|---|---|
| `cat` | the three characters c, a, t in a row, anywhere in the line |
| `c.t` | c, **any one character**, t: `cat`, `cut`, `c3t`, `c t` |
| `c\.t` | c, a literal dot, t |

Characters with meaning in a regex - `. * [ ] ^ $ \` - need a backslash
to be literal. Everything else is itself.

## Anchors

| Pattern | Matches |
|---|---|
| `^root` | `root` at the **start** of the line |
| `bash$` | `bash` at the **end** |
| `^$` | an empty line |
| `^#` | a comment line |
| `^\s*$` | a blank line (spaces/tabs only; `\s` is a GNU extension) |

```bash
grep '^root' /etc/passwd
grep 'bash$' /etc/passwd
grep -v '^#' /etc/ssh/sshd_config | grep -v '^$'
```

## Character classes: one character from a set

| Pattern | Matches one character that is |
|---|---|
| `[abc]` | a, b or c |
| `[a-z]`, `[A-Z]`, `[0-9]`, `[a-zA-Z0-9]` | in a range |
| `[^0-9]` | **not** a digit (`^` inside brackets negates) |
| `[[:digit:]]`, `[[:alpha:]]`, `[[:alnum:]]`, `[[:space:]]`, `[[:upper:]]`, `[[:lower:]]`, `[[:punct:]]` | POSIX named classes - locale-safe |
| `[.]`, `[$]` | a literal dot / dollar (most metacharacters lose meaning inside brackets) |

```bash
grep '^[A-Z]' file                 # lines starting with a capital
grep '[0-9][0-9][0-9]' file        # three digits in a row
grep 'gr[ae]y' file                # gray or grey
grep '^[^#]' file                  # lines whose first char is not #
```

## Repetition: how many of the previous thing

| BRE | Meaning |
|---|---|
| `*` | **zero or more** of the previous item |
| `\+` | one or more (GNU extension in BRE; `+` is extended) |
| `\?` | zero or one (GNU; `?` is extended) |
| `\{n\}` | exactly n |
| `\{n,\}` | n or more |
| `\{n,m\}` | between n and m |

`*` applies to the **one item before it**: `ab*` is `a` followed by any
number of `b` (`a`, `ab`, `abbb`) - not "ab repeated". `.*` is "anything,
any length" - the most common idiom.

```bash
grep 'ab*c' file                    # ac, abc, abbc...
grep 'colou\?r' file                # color, colour
grep '^[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}$' ips     # an IPv4 shape
grep 'error.*timeout' log           # error, then later timeout, on one line
grep '^.\{80,\}' file               # lines 80+ characters long
grep '^-' file                      # lines beginning with a dash (escape not needed at line start after ^; or use -e)
```

## Groups and back-references

| BRE | Meaning |
|---|---|
| `\(...\)` | group (in BRE the parentheses are escaped to mean "group") |
| `\1`, `\2` | what group 1, 2 matched - in the same pattern, or in sed's replacement |
| `\<word\>`, `\bword\b` | word boundaries (GNU) |

```bash
grep '\(ab\)\{2\}' file             # abab
grep '\([a-z]\)\1' file             # a doubled letter: ll, ss, oo
sed 's/\([0-9]*\)-\([0-9]*\)/\2-\1/' file      # swap two numbers around a dash
sed -n 's/^User=\(.*\)$/\1/p' unit.service      # extract the value after User=
grep '\<cat\>' file                 # cat as a word (same as grep -w cat)
```

## The five things to get right

1. **Quote** the pattern with single quotes.
2. `.` is any char; `\.` is a dot.
3. `*` is "zero or more of the previous", and `.*` is "anything".
4. `^`/`$` anchor; `[^...]` negates a class.
5. In **BRE**, `+ ? { } ( ) |` are literals and need `\` to be operators -
   or use `grep -E` (next lesson) where they are operators without `\`.

:::exam-tip
Most exam regex is `grep` with an anchor and a class: lines starting with
a digit (`'^[0-9]'`), lines ending with `.conf` (`'\.conf$'`), non-comment
lines (`'^[^#]'`). Test the pattern on screen, then redirect. When a
pattern needs `+` or `|`, switch to `grep -E` and the backslashes go away.
:::

## Check yourself

1. What does `ab*c` match, and what does it not match?
2. Write a BRE for lines that start with a digit and end with a semicolon.
3. In BRE, how do you write "one or more digits"?
