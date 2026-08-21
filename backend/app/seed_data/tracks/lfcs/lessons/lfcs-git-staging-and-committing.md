## Three places a file can be

```
  working tree  ──git add──▶  staging area (index)  ──git commit──▶  repository (history)
       edits                     what the next commit will contain          permanent
```

Git's unusual middle step, the **index**, lets you commit *some* of your
changes and not others - so one commit can be one logical change even when
you edited five things.

```bash
git status
# Changes to be committed:      <- staged (index)
#   modified: a.conf
# Changes not staged for commit:  <- modified in the working tree only
#   modified: b.conf
# Untracked files:              <- Git has never seen it
#   c.conf
```

## Staging

```bash
git add nginx.conf                 # one file
git add site1.conf site2.conf
git add .                          # everything under the current directory
git add -A                         # everything in the repository, including deletions
git add '*.conf'                   # by pattern
git add -u                         # only files Git already tracks
git add -p                         # interactively, hunk by hunk - the reviewer's habit
git restore --staged nginx.conf    # unstage (keep the edit)   [older: git reset HEAD file]
```

## Committing

```bash
git commit -m "Increase nginx worker_connections to 4096"
git commit                          # opens $EDITOR for a longer message
git commit -a -m "message"          # stage all TRACKED modifications and commit (skips untracked)
git commit --amend -m "better message"      # replace the last commit (message and/or content)
git commit --amend --no-edit                # add staged changes to the last commit, keep the message
```

A good message: a short imperative subject line (under ~50 characters),
a blank line, then why - not what, which the diff already shows.

```
Raise nginx worker_connections to 4096

The 512 default was capping concurrent uploads during the evening
peak; ss showed the accept queue filling. 4096 fits the file
descriptor limit set in the systemd unit.
```

## Undoing, at each stage

| Situation | Command |
|---|---|
| discard an unstaged edit | `git restore file` (older: `git checkout -- file`) |
| unstage, keep the edit | `git restore --staged file` |
| discard everything uncommitted | `git restore .` then `git clean -fd` (untracked) |
| fix the last commit | `git commit --amend` |
| undo the last commit, keep changes staged | `git reset --soft HEAD~1` |
| undo the last commit, keep changes unstaged | `git reset HEAD~1` (mixed, the default) |
| undo the last commit and **throw away** the changes | `git reset --hard HEAD~1` |
| undo a commit that others already have | `git revert a1b2c3d` (makes a new, opposite commit) |
| get a file back as it was at a commit | `git checkout a1b2c3d -- file` / `git restore --source=a1b2c3d file` |

:::warning
`git reset --hard` and `git clean -fd` delete work permanently - there is
no undo for changes that were never committed. Commit first (even a
throwaway "wip" commit); a committed mistake is always recoverable with
`git reflog`.
:::

## Ignoring files

```bash
cat > .gitignore <<'EOF'
*.log
*.swp
secrets.env
.cache/
EOF
git add .gitignore && git commit -m "Add gitignore"
git check-ignore -v somefile        # which rule ignores it
git rm --cached secrets.env         # stop tracking a file already committed (keeps it on disk)
```

`.gitignore` only affects **untracked** files; a file already committed
keeps being tracked until you `git rm --cached` it. And a secret once
committed stays in the history - rotate it rather than trying to erase it.

## Moving and deleting

```bash
git mv old.conf new.conf           # rename and stage it
git rm old.conf                    # delete and stage the deletion
git rm -r olddir/
git rm --cached file               # untrack, keep on disk
```

## Seeing what a commit will be

```bash
git diff --staged                  # exactly what `git commit` would record
git status -sb
git commit --dry-run -a
```

:::exam-tip
The LFCS Git tasks are small: initialise a repository, add files, commit
with a given message, show the log. `git init`, `git add .`, `git commit -m
"..."`, `git log --oneline`. Remember `git config user.email` first on a
fresh machine - without it the commit fails and the failure is easy to
misread as a repository problem.
:::

## Check yourself

1. What are the three states a file can be in, and which command moves it
   between the first two?
2. How do you unstage a file without losing the edit?
3. Why is `git revert` the right tool for a commit others have already
   pulled?
