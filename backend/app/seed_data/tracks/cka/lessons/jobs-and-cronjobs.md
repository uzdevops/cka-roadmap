## Work that finishes

Deployments keep Pods running forever. Some work is the opposite: run to
completion, report success or failure, stop. A database migration, a report,
a batch transform, a backup. That is a **Job**; a Job on a schedule is a
**CronJob**.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: report
spec:
  completions: 1           # how many successful Pods are needed
  parallelism: 1           # how many may run at once
  backoffLimit: 4          # how many failures before the Job is marked Failed
  activeDeadlineSeconds: 600
  ttlSecondsAfterFinished: 3600   # clean the Job and its Pods up an hour after it ends
  template:
    spec:
      restartPolicy: Never          # required: Never or OnFailure - never Always
      containers:
        - name: report
          image: reports:1.4
          command: ["python", "monthly.py"]
```

```bash
kubectl create job report --image=reports:1.4 -- python monthly.py
kubectl create job one-off --from=cronjob/backup          # run a CronJob's job now
kubectl get jobs
# NAME     COMPLETIONS   DURATION   AGE
# report   1/1           42s        2m
kubectl get pods -l job-name=report
kubectl logs job/report
kubectl delete job report                                 # deletes its Pods too
```

## restartPolicy and backoffLimit

`Always` is not allowed on a Job - a Pod that always restarts never
completes. The two legal values change what "retry" means:

| `restartPolicy` | On failure | What `backoffLimit` counts |
|---|---|---|
| `OnFailure` | the **container** is restarted inside the same Pod | container restarts (visible in RESTARTS) |
| `Never` | the Pod is left Failed and a **new Pod** is created | failed Pods (they pile up in `get pods` - useful for logs) |

Either way, once `backoffLimit` is hit the Job has `Failed` in its conditions
and stops trying.

## completions and parallelism

```yaml
completions: 5
parallelism: 2
```

"I need five successful runs; run at most two at a time." Fixed completion
count. For a work queue where each Pod pulls items until there are none,
leave `completions` unset and set `parallelism`; the Job completes when **any**
Pod succeeds and the rest have exited. Indexed Jobs (`completionMode:
Indexed`) hand each Pod a `JOB_COMPLETION_INDEX` so five Pods can each process
one fifth of the data.

:::exam-tip
Exam Job tasks are about the numbers: "run 5 times, 2 in parallel, give up
after 3 failures" is `completions: 5, parallelism: 2, backoffLimit: 3`. There
are no `kubectl create job --completions` flags - generate with `$do`, add the
three lines under `spec`, apply.
:::

## CronJobs

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup
spec:
  schedule: "30 2 * * *"            # 02:30 every day, cron syntax, in the controller's timezone (UTC on kubeadm)
  timeZone: "Asia/Tashkent"         # optional, since 1.27
  concurrencyPolicy: Forbid         # Allow | Forbid | Replace
  startingDeadlineSeconds: 300
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      backoffLimit: 2
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: backup
              image: backup-tool:3.1
              args: ["--target", "s3://bucket/nightly"]
```

```bash
kubectl create cronjob backup --image=backup-tool:3.1 --schedule="30 2 * * *" -- /backup.sh
kubectl get cronjobs
# NAME     SCHEDULE     SUSPEND   ACTIVE   LAST SCHEDULE   AGE
kubectl get jobs --watch                 # each run is a Job named backup-<timestamp>
kubectl patch cronjob backup -p '{"spec":{"suspend":true}}'   # pause it
```

The nesting is the part to get right: CronJob **spec** → `jobTemplate` → Job
**spec** → `template` → Pod **spec**. Three `spec:` keys, each at its own
level. `kubectl explain cronjob.spec.jobTemplate.spec.template.spec
--recursive` is your friend.

`concurrencyPolicy` decides what happens when a run is still going at the
next tick: `Allow` starts another, `Forbid` skips the new one, `Replace`
kills the old one. Backups want `Forbid`.

:::warning
Cron syntax is five fields - minute hour day-of-month month day-of-week -
and `*/5 * * * *` is "every five minutes". A schedule like `30 2 * * *` runs
at 02:30 in the **cluster's** timezone unless `timeZone` says otherwise; on
most clusters that is UTC, which is 5 hours behind Tashkent.
:::

## Check yourself

1. Why can a Job's Pod template not use `restartPolicy: Always`?
2. With `restartPolicy: Never` and `backoffLimit: 3`, how many Pods might you
   see for a Job that never succeeds?
3. Write the `schedule` for "every Monday at 06:00" and name the
   `concurrencyPolicy` you would set for a job that must not overlap itself.
