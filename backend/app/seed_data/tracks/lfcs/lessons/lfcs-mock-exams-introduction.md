## What the mocks are for

Four mocks, each a set of hands-on tasks on a live machine, each followed
by a review quiz on this platform. They do not test whether you have
learned Linux - twelve weeks did that. They test whether you can do it
**in two hours, on someone else's machine, with `man` as your only
reference**. That is a separate skill and it is trainable.

## The exam, in numbers

| | |
|---|---|
| Format | performance-based: tasks on a live Ubuntu LTS system in a browser terminal |
| Duration | **2 hours** |
| Pass | **66%** |
| Reference | **`man`, `info`, `--help` on the exam system** - no browser, no notes |
| Domains | Operations Deployment 25%, Networking 25%, Storage 20%, Essential Commands 20%, Users and Groups 10% |
| Retake | one free retake included |
| Validity | 3 years |

Confirm the current numbers in the Linux Foundation's handbook when you
book - they are revised.

## How to run a mock

1. **Two hours, one sitting, no browser.** Only `man`. If you find
   yourself reaching for a search engine, that is a finding - write it
   down and use `man -k` instead.
2. **Snapshot the VM first** (`virsh snapshot-create-as lab01 pre-mock`).
   Several tasks change partitions, firewalls and users; you want to
   roll back and re-run.
3. **Work in order, skip freely.** Anything not moving in five minutes:
   note it and move on.
4. **Verify every task before leaving it.** `systemctl is-active`,
   `findmnt`, `getent`, `ss -tulpn`, `curl` - the grader checks the end
   state, not your intentions.
5. **Stop at two hours**, even mid-task. The point is to learn what two
   hours buys you.

## Scoring

Each mock lists its tasks with a weight totalling 100. Score a task only
if the end state is **exactly** what was asked: right name, right path,
right options, and **persistent** when the task says persistent. A mount
that works now but is not in fstab is zero, and that is the most common
way people lose marks.

## What to do with a wrong answer

| Why it went wrong | Fix |
|---|---|
| did not know the command | re-read that lesson, redo its lab |
| knew it, could not find it in `man` fast enough | practise `man -k`, and learn which section (5 for config files, 8 for admin commands) |
| knew it, typed it, did not verify - and it was wrong | add the check to your habit: every task ends with a verification command |
| forgot to make it persistent | fstab, `systemctl enable`, `sysctl --system`, `--permanent` - build the reflex |
| ran out of time | drill the long tasks (LVM, bonding, firewall) until they are mechanical |
| misread the task | read twice, underline names, paths, sizes and the word "persistent" |

Keep the list. Four mocks produce perhaps twenty rows, and they are your
study plan for the remaining days.

## Between the mocks

Do not take them back to back. Mock 1, then a day closing its gaps; mock 2,
same; mocks 3 and 4 in the last week, the final one two or three days
before the exam. Re-doing a mock a week later is worth less than the first
run but still worth something - the task shapes repeat on the real exam.

## The persistence checklist

Before you call any task finished, ask which of these it needed:

| Change | Persist with |
|---|---|
| mount | `/etc/fstab` + `mount -a` |
| swap | `/etc/fstab` + `swapon --show` |
| service | `systemctl enable --now` |
| sysctl | `/etc/sysctl.d/*.conf` + `sysctl --system` |
| firewall | `ufw enable` / `--permanent` + `--reload` |
| network address | nmcli profile or netplan, not `ip addr add` |
| user limits | `/etc/security/limits.d/` |
| SELinux label/port/boolean | `semanage`, `setsebool -P` |
| cron | a crontab, not a shell loop |

:::tip
The exam gives you a scratchpad in the terminal environment. During the
mocks, keep a text file open the same way: task numbers you skipped and
commands you want to reuse. It is the only "notes" you are allowed,
because you write them during the exam.
:::

## Check yourself

1. What is the duration, pass mark and reference material of the LFCS?
2. What is the most common reason a completed task still scores zero?
3. Name the five categories of wrong answer and the fix for each.
