## Booking

- Buy the LFCS at training.linuxfoundation.org. The purchase includes one
  **free retake** and is valid for a year; the exam date is booked
  separately in the portal.
- Book for a time of day when you are sharp, two to three weeks out, so
  the date is real and the revision has a deadline.
- Read the **Candidate Handbook** and the **Important Instructions** page
  in the week before - allowed materials, ID requirements and room rules
  change.

## The day before

- Run the **system check** (browser, webcam, microphone, screen sharing)
  on the machine and network you will use.
- Government **ID** whose name matches the booking exactly.
- A **clean desk** in a quiet room: no paper, no phone, no second screen.
  The proctor will ask you to show the room and the desk.
- Skim the objectives list and your mock-error table. Do not learn
  anything new. Sleep.

## The day

- Check in **30 minutes early**; identity and room checks take time.
- The environment is a terminal on a live Ubuntu system. Your reference is
  `man`, `info` and `--help` - nothing else. Copy and paste work inside
  the environment.
- Minute zero: `whoami`, `hostname`, `lsblk`, `ip a`. Know what machine
  you are on before changing it.
- Every task: **read twice** (note the words "persistent", "all users",
  "without changing"), do it, **verify**, move on. Use the scratchpad for
  what you skip.
- A task not moving in five minutes: leave it, come back. Partial credit
  exists; an untouched easy task does not.
- Before the clock runs out, spend the last five minutes re-checking the
  persistence list: fstab, `systemctl is-enabled`, `sysctl`, firewall
  `--permanent`, crontab.
- Results arrive by email, usually within 24 hours. Pass is 66%.

## If it does not go well

One free retake. Book it two to three weeks later, not the next day. The
score report breaks down by domain; the mock-error method from week 13
applies directly. Most second attempts pass, and the first attempt is the
most accurate mock exam you will ever take.

## What you can do now

Thirteen weeks ago the objective list was a list of unfamiliar phrases.
You can now install, configure and repair a Linux system: partition and
grow storage, join it to a network, filter its traffic, run and write
services, manage the people who use it, and find out why any of it stopped
working. That is the job, and the certificate is only the receipt.

## After the LFCS

The certificate is valid for **three years**. Where next depends on what
you do all day:

| Direction | Next | On this platform |
|---|---|---|
| you run containers and clusters on these machines | **CKA** - the Kubernetes administrator exam; every "ssh to the node and read the kubelet log" task is an LFCS skill | CKA track |
| you build and ship applications on Kubernetes | **CKAD** | CKAD track |
| you secure clusters | **CKS** (requires a current CKA) | CKS track |
| you want the deeper Linux engineering exam | **LFCE** - Linux Foundation Certified Engineer | - |
| you automate all of the above | Ansible, Terraform, CI/CD, GitOps - no exam required to start | DevOps platform |

The natural next step from here is the **CKA**: it assumes exactly the
Linux you now have, and the two certificates together describe someone who
can run modern infrastructure end to end.

And the habits carry over regardless: read the error, change one thing,
verify it, and make it persistent.

:::tip
Book the next thing in the week you pass. A CKA voucher bought while the
momentum lasts is the cheapest way to make sure thirteen weeks of habit do
not fade.
:::

## Check yourself

1. What must be true of your room and your ID before the proctor lets you
   start?
2. What is your reference material during the exam, and what does that
   change about how you work?
3. Which certification will you take next, and when will you book it?
