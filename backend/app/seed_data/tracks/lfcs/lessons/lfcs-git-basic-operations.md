## Why a sysadmin needs Git

Configuration is text, and text under version control is text you can
diff, revert and explain. `/etc` in a repository answers "what changed
last Tuesday and who did it" without archaeology. The LFCS objectives ask
for the basics: create or clone a repository, look at its state, read its
history.

```bash
sudo apt install git          # or: dnf install git
git --version
```

## Tell Git who you are

```bash
git config --global user.name "Ahmad Maxmudov"
git config --global user.email "ahmad@example.com"
git config --global init.defaultBranch main
git config --global core.editor vim
git config --list --show-origin        # every setting and the file it came from
```

Three levels, each overriding the one before: system (`/etc/gitconfig`),
global (`~/.gitconfig`), local (`.git/config` in one repository). Without a
name and email, `git commit` refuses.

## A repository from nothing

```bash
mkdir /srv/configs && cd /srv/configs
git init
# Initialized empty Git repository in /srv/configs/.git/
ls -a          # .git/ holds everything: objects, refs, config, HEAD
```

The working tree is the files you see; `.git/` is the database beside
them. Delete `.git` and you have plain files again; copy the directory and
you copy the whole history with it.

## A repository from someone else's

```bash
git clone https://github.com/uzdevops/cka-roadmap.git
git clone git@github.com:uzdevops/cka-roadmap.git         # over SSH, with your key
git clone https://github.com/org/repo.git /opt/repo       # into a chosen directory
git clone --depth 1 https://github.com/org/repo.git       # shallow: latest commit only, fast
git clone --branch v2.1 https://github.com/org/repo.git   # a specific branch or tag
```

`clone` creates the directory, downloads the full history, checks out the
default branch, and records the source as the remote **origin**.

## Where am I? git status

```bash
git status
# On branch main
# Your branch is up to date with 'origin/main'.
# Changes not staged for commit:
#   modified:   nginx.conf
# Untracked files:
#   new-site.conf
git status -s          # short: ' M nginx.conf', '?? new-site.conf'
git status -sb         # short + branch line
```

`git status` is the command you run between every other command. It always
tells you the branch, what is modified, what is staged, and what Git does
not know about.

## What happened? git log

```bash
git log                                    # full entries, newest first
git log --oneline                          # one line per commit: short hash + subject
git log --oneline --graph --all --decorate # the shape of the branches
git log -5                                 # last five
git log --since="2 weeks ago" --until=yesterday
git log --author="Ahmad"
git log -p nginx.conf                      # every change to one file, with diffs
git log --stat                             # files changed and how much
git log --grep="fix"                       # search commit messages
git show HEAD                              # the newest commit in full
git show a1b2c3d:nginx.conf                # a file as it was at that commit
```

`HEAD` is where you are now; `HEAD~1` is one commit back, `HEAD~3` three.
A commit is identified by a SHA hash; the first 7-8 characters are enough.

## Looking at differences

```bash
git diff                     # working tree vs staged (unstaged changes)
git diff --staged            # staged vs last commit (what a commit would record)
git diff HEAD                # working tree vs last commit (everything)
git diff a1b2c3d..e4f5g6h    # between two commits
git diff main..feature       # between branches
git diff --stat
```

## Who wrote this line

```bash
git blame nginx.conf         # each line with its commit, author and date
git blame -L 20,40 nginx.conf
```

The single most useful command when a config line is a mystery.

:::tip
Put `/etc` under Git on a machine you administer (`etckeeper` automates
it) and you get a changelog of every package install and manual edit for
free. Even without it: any directory you edit by hand deserves a `git
init` and a commit before you start.
:::

## Check yourself

1. What is the difference between the working tree and the `.git`
   directory?
2. Which command shows what has changed and which files Git does not
   track?
3. How do you see every change ever made to a single file, with diffs?
