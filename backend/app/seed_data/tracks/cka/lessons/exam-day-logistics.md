## What the mocks are for

Three full mocks, each a set of hands-on tasks on a cluster, each followed
by a step-by-step solutions lesson, each closed with a 15-question review
quiz on this platform. They are not a test of whether you have learned
Kubernetes - you have, over nineteen weeks. They are a test of whether you
can do it **under the clock, in someone else's cluster, with the
documentation site as your only reference**. That is a separate skill, and
it is trainable.

## The real exam, in numbers

| | |
|---|---|
| Format | performance-based: 15-20 tasks on live clusters, in a remote desktop with a terminal and a browser |
| Time | **2 hours** |
| Pass | **66%** |
| Clusters | several; each task starts with `kubectl config use-context <name>` |
| Allowed | one browser tab on **kubernetes.io/docs**, **kubernetes.io/blog**, **helm.sh/docs** (and kubernetes.io's sub-domains); nothing else, no notes |
| Retake | one free retake included with the purchase |
| Validity | certificate valid 2 years |

Tasks are weighted (2%-13%); partial credit exists per task. Check the
Linux Foundation's candidate handbook for the current rules before you
book - they change.

## How to run a mock

1. **Block 2 hours**. Phone away, one monitor, no notes - the same
   constraints as the real thing.
2. **Set up the terminal the way you will on the day** (next lessons):
   `alias k=kubectl`, `export do="--dry-run=client -o yaml"`, vim with
   `set ts=2 sw=2 et`.
3. **Work the tasks in order, but skip freely.** Anything not moving in 5
   minutes: note it, move on, come back.
4. **Verify every task before leaving it**: `get`, `describe`, `curl`. A
   task done but not checked is half a task.
5. **Stop at 2 hours.** Even mid-task. The point is to find out what
   2 hours buys you.

## Scoring yourself

Each mock lesson lists its tasks with a weight. Score a task only if the
**end state** is exactly what was asked - name, namespace, image, labels,
ports, file path. A Pod with the right image and the wrong name is 0.

```
score = sum of weights of fully-correct tasks
```

Then the solutions lesson: read every task's solution, **including the
ones you got right** - the fast path may be faster than yours.

## What to do with a wrong answer

A wrong answer is the most valuable thing a mock produces. Classify it:

| Why it went wrong | What it means | Fix |
|---|---|---|
| did not know the command / field | a **knowledge** gap | re-read that lesson; do its lab again |
| knew it, could not find it in the docs fast enough | a **navigation** gap | learn the docs page's location; practise the search term |
| knew it, typed it wrong, did not notice | a **verification** gap | add the check to your habit: `get` after every `create` |
| ran out of time | a **speed** gap | speed drills lesson; imperative commands; skip earlier |
| misread the task | a **reading** gap | read tasks twice; underline names, namespaces, numbers |

Write each one down in the weak-domain-review lesson's format. Three mocks
produce maybe fifteen of these, and they are your study plan for the
remaining days.

## Between the mocks

Do not take the three back to back. Mock 1, then a day or two closing its
gaps; mock 2 (harder), same; mock 3 (hardest) a few days before the exam,
followed by a light day. Re-doing a mock you have seen is worth less than
the first time but still worth something a week later - the tasks are
standard shapes and the shapes repeat on the exam.

:::tip
The exam gives you a scratchpad (notepad) in the remote desktop. In the
mocks, keep a text file open the same way: paste task names and numbers
you skip, and the commands you want to reuse. It is the one piece of
"notes" you are allowed, because you write it during the exam.
:::

## Check yourself

1. What are the time limit and pass mark of the CKA, and what may you have
   open besides the terminal?
2. Why should you read the solutions for tasks you got right?
3. Name the five kinds of wrong answer and which lesson or habit fixes
   each.
