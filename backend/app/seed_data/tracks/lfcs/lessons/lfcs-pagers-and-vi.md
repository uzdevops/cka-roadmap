## Pagers: reading more than a screen

```bash
less /var/log/syslog
journalctl -u nginx | less           # less is what man and journalctl already use
more file                            # the older one: forward only, q to quit
```

Inside `less`:

| Key | Does |
|---|---|
| `Space` / `b` | page down / up |
| `j` `k` or arrows | line down / up |
| `g` / `G` | top / bottom |
| `/pattern` / `?pattern` | search forward / back; `n` `N` next / previous |
| `F` | follow (like `tail -f`); Ctrl-C to stop, then `q` |
| `-N` (or start with `less -N`) | line numbers |
| `-S` | do not wrap long lines; `-i` case-insensitive search |
| `h` | help; `q` quit |
| `v` | open the file in `$EDITOR` at this position |

`less -R` keeps colours (`ls --color=always | less -R`); `less +F file`
starts in follow mode; `less +/pattern file` starts at the first match.

## vi: enough to survive

The exam machine has `vi`/`vim` (and usually `nano`). Tasks say "edit
/etc/fstab" and you need to get in, change a line, get out, with no
mistakes. Three modes:

```
   NORMAL  ──i, a, o──▶  INSERT  (type text)
     ▲                       │
     └────────Esc────────────┘
   NORMAL  ──:──▶  COMMAND-LINE  (:w, :q, :s)
```

You start in **normal** mode (keys are commands). `i` enters insert mode
before the cursor, `a` after, `o` opens a new line below, `O` above.
**Esc** always returns to normal. `:` starts a command.

### Save and quit

| | |
|---|---|
| `:w` | save |
| `:q` | quit (refuses if unsaved) |
| `:wq` or `ZZ` | save and quit |
| `:q!` | quit **without** saving |
| `:w newname` | save as |
| `:wq!` | force-save (e.g. read-only file you own); `:w !sudo tee %` for a root file opened without sudo |

### Move (normal mode)

`h j k l` (or arrows), `0` / `$` line start/end, `w` / `b` word forward/back,
`gg` / `G` top/bottom, `:42` line 42, `Ctrl-f` / `Ctrl-b` page.

### Edit (normal mode)

| Key | Does |
|---|---|
| `x` | delete character |
| `dd` | delete (cut) line; `5dd` five lines; `dw` a word; `D` to end of line |
| `yy` | yank (copy) line; `5yy` |
| `p` / `P` | paste after / before |
| `u` | undo; `Ctrl-r` redo |
| `.` | repeat last change |
| `r` | replace one character; `R` overwrite mode |
| `cw` | change word (delete + insert); `cc` whole line |
| `J` | join lines |
| `>>` / `<<` | indent / dedent |

### Search and replace

| | |
|---|---|
| `/pattern` `n` `N` | search; next; previous |
| `:s/old/new/` | first on this line |
| `:s/old/new/g` | all on this line |
| `:%s/old/new/g` | **whole file** |
| `:%s/old/new/gc` | with confirmation |
| `:10,20s/^/#/` | comment out lines 10-20 |
| `:g/pattern/d` | delete every matching line |
| `:noh` | clear search highlight |

### Settings that help

```
:set nu            line numbers        :set nonu
:set paste         before pasting      :set nopaste
:set ts=2 sw=2 et  tabs → 2 spaces (for YAML)
:set list          show tabs/trailing spaces
:syntax on
```

Persist them in `~/.vimrc`: `set nu ts=4 sw=4 et`.

### Two files, and help

`:e other` open another, `:bn` next buffer, `vimdiff a b`, `:help :s`,
`vimtutor` (30 minutes, the best investment in this track).

## nano, if you must

`nano file`: type; **Ctrl-O** save, **Ctrl-X** exit, **Ctrl-W** search,
**Ctrl-K** cut line, **Ctrl-U** paste, **Ctrl-\** replace. The shortcuts are
on screen. Slower for edits across a file, fine for one line.

:::exam-tip
Practise exactly these until they are reflexes: `vi file` → `/pattern` →
`cw` or `dd` or `o` → Esc → `:wq`. And `:q!` when something went wrong.
Most exam edits are one line in a config file; `:%s/^#Port 22/Port 2222/`
then `:wq` is five seconds. If vi ever misbehaves, you are in the wrong
mode - press Esc twice and start the command again.
:::

## Check yourself

1. How do you search for a pattern in `less` and jump to the next match?
2. In vi: the keys to delete a line, undo, and quit without saving.
3. The command to replace every `foo` with `bar` in the whole file.
