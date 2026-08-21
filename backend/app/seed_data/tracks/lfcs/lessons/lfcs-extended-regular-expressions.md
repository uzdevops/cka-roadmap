## ERE: the same language with the backslashes removed

Extended regular expressions add nothing a basic one cannot express with
GNU escapes; they make the common operators **unescaped**. `grep -E`,
`egrep`, `sed -E` (or `-r`), `awk` - all use ERE.

| Operator | BRE | ERE | Meaning |
|---|---|---|---|
| one or more | `\+` | `+` | |
| zero or one | `\?` | `?` | |
| n to m | `\{n,m\}` | `{n,m}` | |
| group | `\(…\)` | `(…)` | |
| alternation | `\|` | `|` | **or** |
| literal `+ ? { } ( ) |` | `+ ? { } ( ) |` | `\+ \? \{ \} \( \) \|` | the escaping flips |

`. * ^ $ [ ]` are the same in both.

## Alternation

```bash
grep -E 'error|warn|crit' /var/log/syslog
grep -E '^(root|admin):' /etc/passwd
grep -Ei '(jan|feb|mar) [0-9]+' log
grep -E 'colou?r' file                  # the ? without a backslash
```

Parentheses scope the `|`: `^root|admin:` means "starts with root, OR
contains admin:"; `^(root|admin):` means "starts with root: or admin:".

## Counting with braces

```bash
grep -E '^[0-9]{1,3}(\.[0-9]{1,3}){3}$' ips          # IPv4 shape: 1-3 digits, then three times ".1-3 digits"
grep -E '^[a-f0-9]{32}$' hashes                      # MD5
grep -E '^.{80,}$' file                              # long lines
grep -E '(ab){2,}' file                              # abab, ababab...
grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}' log            # lines starting with a date
```

## Groups, captures and back-references

```bash
grep -E '([a-z])\1' file                             # doubled letter
sed -E 's/([0-9]+)\.([0-9]+)\.([0-9]+)/\3.\2.\1/' f   # reverse a dotted triple
sed -E 's/^(#?)Port .*/Port 2222/' sshd_config       # replace a line whether commented or not
echo "user=alice" | sed -E 's/^user=(.*)$/\1/'        # extract
awk '/^[0-9]+ /' file                                # awk patterns are ERE
```

## Shortcuts (GNU)

| | |
|---|---|
| `\w`, `\W` | word char `[A-Za-z0-9_]` / not |
| `\s`, `\S` | whitespace / not |
| `\b` | word boundary; `\<` `\>` start/end of word |
| `\d` | **not** supported by grep/sed - use `[0-9]` or `[[:digit:]]` |

```bash
grep -E '\bsshd\b' log
grep -Eo '\w+@\w+\.\w+' file                         # crude email extraction
grep -Eo '[0-9]+' file | sort -n | tail -1           # the largest number in a file
```

## grep -o and -E together: extracting

`-o` prints only the matched part, once per match - with ERE it is a tiny
extractor:

```bash
grep -Eo '[0-9]{1,3}(\.[0-9]{1,3}){3}' access.log | sort | uniq -c | sort -rn | head    # client IPs by count
grep -Eo 'HTTP/[0-9.]+" [0-9]{3}' access.log | awk '{print $2}' | sort | uniq -c          # status codes
grep -Eo '^[^:]+' /etc/passwd                                                             # usernames (same as cut -d: -f1)
grep -Eo 'inet [0-9.]+' <(ip a) | awk '{print $2}'                                       # IPv4 addresses on the host
```

## Choosing

| Use | When |
|---|---|
| `grep 'pattern'` (BRE) | literals, anchors, classes, `*` - most of the time |
| `grep -E 'pattern'` | you need `+ ? {} () |` and do not want to escape them |
| `grep -F 'string'` | the "pattern" is a literal string with metacharacters (`$HOME`, `1.2.3.4`, `a+b`) - no regex at all |
| `grep -P` | Perl regex (`\d`, lookahead) - GNU only, not POSIX; avoid on the exam unless needed |
| `sed -E`, `awk` | editing/extracting with groups |

:::exam-tip
When a task says "lines containing either X or Y" → `grep -E 'X|Y'`; "a
number of at least three digits" → `grep -E '[0-9]{3,}'`; "lines matching
the literal string `$PATH`" → `grep -F '$PATH'`. If a pattern with `+` or
`|` matches nothing in plain `grep`, you forgot `-E` - that is the single
most common regex failure.
:::

## Check yourself

1. Rewrite `grep 'colou\?r\|gray'` as an ERE.
2. Write an ERE that matches lines consisting only of a MAC address
   (`aa:bb:cc:dd:ee:ff`).
3. When is `grep -F` the right tool, and why?
