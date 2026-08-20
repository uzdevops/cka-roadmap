## What the CKA actually is

The Certified Kubernetes Administrator is a **performance-based** exam: there
are no multiple-choice questions. You get a terminal, a handful of real
clusters, and a list of tasks - create this, fix that, find out why this is
broken - and you are scored on the state of the clusters when the clock stops.

| | |
|---|---|
| Format | Hands-on, in a browser-based remote desktop |
| Duration | 2 hours |
| Tasks | 15-20, each weighted differently |
| Pass mark | 66 % |
| Retakes | One free retake is included |
| Validity | 2 years |
| Allowed resources | kubernetes.io/docs, kubernetes.io/blog, helm.sh/docs, kubernetes.github.io/ingress-nginx, gateway-api.sigs.k8s.io |

The allowed-resources line matters more than it looks: you can - and should -
open the official documentation during the exam. What you cannot do is waste
ten minutes searching it. The skill the exam rewards is knowing *which page*
you need and going straight to it.

## The domains and their weights

| Domain | Weight |
|---|---|
| Troubleshooting | 30 % |
| Cluster Architecture, Installation & Configuration | 25 % |
| Services & Networking | 20 % |
| Workloads & Scheduling | 15 % |
| Storage | 10 % |

Read those weights as a study plan. Troubleshooting plus cluster
administration is more than half the marks - which is exactly why this track
spends its later phases there and why the mock exams lean that way too.

:::exam-tip
Every task tells you which cluster to use - `kubectl config use-context
<name>` is the first line of every answer. Skipping it is the single most
common way to lose a task you actually solved.
:::

## How the exam is scored

Each task is worth a stated percentage. Partial credit exists within a task:
if a question asks for a Deployment with three replicas exposed on port 80 and
you get the Deployment right but the Service wrong, you keep the Deployment's
share. Two consequences:

- **Do the easy parts of every task.** Never leave a task untouched because
  one sub-step looks hard.
- **Flag and move on.** The interface lets you mark a task; a question worth
  4 % is not worth twelve minutes while a 9 % question waits.

## What a good exam hour looks like

1. First pass - read every task, do the ones you can finish in under three
   minutes, flag the rest. Many candidates clear 40 % of the marks here.
2. Second pass - the flagged tasks, hardest last.
3. Last ten minutes - re-check that every object you created actually exists
   in the right namespace on the right cluster. `kubectl get all -A` in each
   context is cheap insurance.

:::tip
Set up the terminal in the first minute: `alias k=kubectl`, `export
do="--dry-run=client -o yaml"`, and `export now="--force --grace-period 0"`
are the three that pay for themselves. The exam environment allows `.bashrc`
edits.
:::

## How this track maps to it

Twenty weeks, eleven phases, following the course order you would get from a
structured video curriculum - but with the platform's own rhythm: lessons
Monday to Friday, a lab on Saturday, a review quiz on Sunday. The readiness
score on your dashboard is weighted by the table above, so it answers "could I
book the exam" rather than "how much have I read".

## Check yourself

1. A task is worth 7 % and asks for three things; you can only do two. What do
   you do, and why?
2. Which two domains together make up more than half the marks?
3. What is the first command you type for every single task?
