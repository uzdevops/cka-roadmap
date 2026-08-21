## Branches: parallel lines of work

A branch is a movable pointer to a commit. Creating one costs nothing;
switching moves your working tree to that commit's content.

```bash
git branch                       # list local branches; * marks the current
git branch -a                    # + remote-tracking branches
git branch -vv                   # + last commit and which remote branch each tracks
git branch feature-tls           # create (does not switch)
git switch feature-tls           # switch      [older: git checkout feature-tls]
git switch -c feature-tls        # create and switch   [older: git checkout -b]
git switch -                     # back to the previous branch
git branch -m old new            # rename
git branch -d feature-tls        # delete (refuses if unmerged)
git branch -D feature-tls        # delete anyway
```

```
main      A───B───C───────F
                   \     /
feature-tls         D───E        (F is the merge commit)
```

## Merging

```bash
git switch main
git merge feature-tls            # bring the branch's commits into main
git merge --no-ff feature-tls    # always make a merge commit (keeps the branch visible in history)
git merge --abort                # get out of a conflicted merge
git branch -d feature-tls        # tidy up after merging
```

**Fast-forward**: if main has not moved, the pointer just slides forward -
no merge commit. Otherwise Git creates one combining both histories.

### Conflicts

When both branches changed the same lines, Git stops and marks the file:

```
<<<<<<< HEAD
worker_connections 1024;
=======
worker_connections 4096;
>>>>>>> feature-tls
```

```bash
git status                       # "both modified: nginx.conf"
vi nginx.conf                    # edit to the intended result, delete the <<< === >>> markers
git add nginx.conf               # marking it resolved
git commit                       # finishes the merge (default message is fine)
git merge --abort                # or: give up and go back
```

Nothing magic: choose the right content, remove the markers, `add`,
`commit`.

## Remotes

A **remote** is a named URL of another copy of the repository.

```bash
git remote -v
# origin  git@github.com:uzdevops/cka-roadmap.git (fetch)
# origin  git@github.com:uzdevops/cka-roadmap.git (push)
git remote add origin git@github.com:org/repo.git
git remote set-url origin https://github.com/org/repo.git
git remote rename origin upstream
git remote remove old
git remote show origin           # branches, tracking, what is out of date
```

## fetch, pull, push

```bash
git fetch origin                 # download new commits; change NOTHING in your working tree
git pull                         # fetch + merge into the current branch
git pull --rebase                # fetch + replay your commits on top (linear history)
git push                         # send the current branch to its tracked remote branch
git push -u origin feature-tls   # first push of a new branch: create it and set tracking
git push --all; git push --tags
git push --force-with-lease      # rewrite remote history - only for a branch that is yours
```

`fetch` is always safe; `pull` changes your files. When something looks
odd, `git fetch` then `git log --oneline HEAD..origin/main` shows exactly
what is incoming before you take it.

| Message | Means |
|---|---|
| `Updates were rejected because the remote contains work that you do not have locally` | someone pushed first - `git pull --rebase` then push |
| `fatal: The current branch X has no upstream branch` | first push - `git push -u origin X` |
| `Permission denied (publickey)` | your SSH key is not on the host, or the wrong key - `ssh -T git@github.com` |
| `Please tell me who you are` | `git config user.name/user.email` |
| `refusing to merge unrelated histories` | two independent repositories - `git pull --allow-unrelated-histories` if you mean it |

## Tags

```bash
git tag v1.0                          # lightweight
git tag -a v1.0 -m "Release 1.0"      # annotated (has author, date, message) - prefer this
git tag                               # list
git show v1.0
git push origin v1.0; git push --tags
git checkout v1.0                     # detached HEAD: look, do not commit here
```

## A workflow that fits a sysadmin

```bash
git switch -c fix-logrotate          # branch for the change
vi /etc/logrotate.d/nginx
git add -A && git commit -m "Rotate nginx logs daily, keep 14"
git switch main && git merge fix-logrotate && git branch -d fix-logrotate
git push
```

Small branch, one change, merge, push. On a server without a remote, the
same without the last line - the history is still yours.

:::exam-tip
LFCS Git tasks stay at this level: create a branch, make a commit on it,
merge it back, add a remote, push. `git switch -c`, `git merge`, `git
remote add`, `git push -u origin <branch>`. Know how to finish a conflict
(edit, `git add`, `git commit`) - that is the only step that stops people.
:::

## Check yourself

1. What is a branch, and what is the difference between a fast-forward
   and a merge commit?
2. What does `git fetch` do that `git pull` also does, and what does it
   not do?
3. You edit a conflicted file. What are the two commands that finish the
   merge?
