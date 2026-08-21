## Decide what to revisit, with data

You have three mock scores, three review quizzes, nineteen weeks of lesson
quizzes and labs, and a readiness breakdown on your dashboard. Together
they tell you where the remaining days go. This lesson is the method.

## The exam's weights

| Domain | Weight | Weeks on this track |
|---|---|---|
| **Troubleshooting** | **30%** | 19, plus the failure tables in 6-8, 14-16 |
| **Cluster Architecture, Installation & Configuration** | **25%** | 1, 9, 10-12 (RBAC, certs), 17, 18 (Helm/Kustomize) |
| **Services & Networking** | **20%** | 14-16 |
| **Workloads & Scheduling** | **15%** | 4-5, 6-8 |
| **Storage** | **10%** | 13 |

Multiply: a domain you score 50% on that weighs 30% costs you 15 points of
the exam; one you score 50% on that weighs 10% costs 5. The pass mark is
66%. Where you spend the days should follow the **product** of weakness
and weight, not weakness alone.

## Step 1: build the table

For each mock task and each quiz question you got wrong or slow, one row:

```
| # | what was asked | domain | why it went wrong (know/find/verify/speed/read) | lesson to revisit |
```

The five "why" categories are from the mock-intro lesson. Be honest about
**verify** - "I did it right but did not check and it was wrong" is the
most common and the easiest to fix.

## Step 2: read the dashboard

The readiness breakdown on your dashboard scores each phase from the
lesson quizzes, labs and review quizzes. Look for:

- a **phase below 70%** → re-do that phase's labs (not the lessons: the
  labs are the exam's shape);
- a **quiz you passed on the second attempt** → its lesson's Check
  yourself questions, out loud, without notes;
- a **lab you skipped** → do it now; skipped labs cluster in exactly the
  domains people fail.

## Step 3: the plan, by product

Rank the rows by `weight × how often it went wrong`. The top five are the
plan. Typical top fives:

| If this is weak | Do this |
|---|---|
| control-plane / node troubleshooting | break your own cluster five ways (scheduler flag, kubelet port, CA path, kube-proxy config path, CoreDNS loop) and fix each, timed |
| networking | NetworkPolicy lab twice; DNS-from-a-Pod drill; the ingress lab; Service endpoints checklist |
| RBAC / certs | the CSR-to-user flow end to end, three times; `auth can-i` as every identity |
| etcd backup/restore | backup, delete a Deployment, restore, confirm it returns - until it is boring |
| JSONPath | the ten asks in the JSONPath lesson, from memory |
| imperative speed | the ten drills, with a timer, daily |
| storage | PV/PVC binding mismatches (class, size, mode) created on purpose and fixed |

## Step 4: what not to do

- Do not re-read all twenty weeks. You have read them; reading again
  feels productive and changes nothing.
- Do not study what you already score 90% on because it is comfortable.
- Do not learn new material (operators, service meshes, eBPF) - it is not
  on the exam and it displaces what is.
- Do not take mock 3 twice in the last two days. One hard mock, then a
  light day, then the exam.

## A week-out schedule that works

| Day | Do |
|---|---|
| -7 | mock 2 (or re-do 1); build the table |
| -6, -5 | top two rows of the plan: labs, timed |
| -4 | mock 3; update the table |
| -3, -2 | next rows; speed drills each day for 20 minutes |
| -1 | light: the drills once, the imperative table once, the docs pages you will need (bookmark them in your head: etcd, CSR, NetworkPolicy, DNS, kubeadm upgrade); sleep |
| 0 | the exam |

:::tip
Readiness is not "I know everything". It is "nothing in the table is
unaddressed, and the last mock was above 66% with ten minutes to spare".
When you can say that, stop studying - the next lesson is about the day
itself.
:::

## Check yourself

1. Why rank weak domains by weight × weakness rather than weakness alone?
2. Which is the most common "why it went wrong" category, and what habit
   fixes it?
3. Name three things that feel like studying but are not worth the last
   week.
