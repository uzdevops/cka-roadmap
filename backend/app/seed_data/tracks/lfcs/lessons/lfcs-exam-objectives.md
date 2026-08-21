## Prerequisites

None formally. In practice, before week 1 you should be able to open a
terminal, move around with `cd` and `ls`, and edit a file with *some*
editor. If `vi` is new, the week-2 lesson covers enough to survive; if the
shell is entirely new, spend a day with any beginner tutorial first - this
track starts at "you can type a command" and moves quickly.

You need one machine to practise on: a virtual machine (VirtualBox, KVM,
a cloud instance) running a recent **Ubuntu LTS** - the exam's
distribution - where you have `sudo` and no fear of breaking it. Snapshot
it before week 11 (storage) and week 10 (firewall) especially.

## The exam, in numbers

| | |
|---|---|
| Format | performance-based, in a browser-based terminal on a remote Linux system; several tasks may involve a second host |
| Duration | **2 hours** |
| Tasks | roughly 15-20, weighted |
| Pass mark | **66%** |
| Distribution | Ubuntu LTS (check the current handbook for the exact release) |
| Reference material | **`man` pages and `--help` on the exam system only** - no browser, no docs site |
| Proctoring | remote, webcam, clean desk, ID |
| Retake | one free retake included |
| Validity | 3 years |

The "no documentation site" rule is the biggest difference from the
Kubernetes exams: `man` is all you get. Which is why every lesson here
shows you the `man` page to open, and why the system-documentation lesson
is this week.

## The objectives

The Linux Foundation publishes the domains as a list of one-line
competencies ("Create, delete, copy, and move files and directories";
"Configure packet filtering"). This track's lesson titles **are** those
lines, one per lesson, in the order the domains list them. When you can
read the official list and, for each line, say what commands you would
type, you are ready - and the list is what to re-read the night before.

## What is not on it

Not: desktop environments, programming beyond shell scripts, specific
cloud providers, Kubernetes, databases, mail servers, web application
stacks. If a lesson here goes further than the objective line, it says
so; the extra is context, not exam material.

## Booking and the day

The purchase includes the exam and one retake, valid for a year; you book
a date separately. Run the system check beforehand, have ID matching the
booking, clear the desk. The conclusion lesson in week 13 has the full
checklist; for now, note that the terminal is in a browser and copy/paste
works within it.

:::tip
Write the five domain names on a card and, as you finish each week, tick
the objective lines it covered. The visible progress keeps the thirteen
weeks moving, and the card is your review sheet.
:::

## Check yourself

1. What reference material is available during the exam, and what does
   that imply for how you study?
2. What is the exam's duration and pass mark?
3. Name two things that are **not** on the LFCS.
