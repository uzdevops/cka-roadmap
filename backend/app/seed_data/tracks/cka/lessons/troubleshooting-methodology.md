## Troubleshooting is a third of the exam

The CKA weights it at 30% - more than any other domain - because it is
what the job is. Nobody hires an administrator to create Deployments;
they hire one for the 3 a.m. page. The good news: troubleshooting is not
inspiration, it is a loop, and the loop is the same every time.

```
  symptom ──▶ WHERE does it live? ──▶ describe ──▶ events ──▶ logs ──▶ exec/ssh ──▶ fix ──▶ VERIFY
                  ▲                                                                         │
                  └──────────────────────── not fixed? next layer ◀─────────────────────────┘
```

## Step 0: where does the failure live?

Before any command, place the symptom in a layer. Each layer has its own
first command, and working the wrong layer is how an hour disappears.

| Symptom | Layer | First command |
|---|---|---|
| app returns errors / wrong page / cannot reach its DB | **application** | `kubectl get pods,svc,ep -n <ns>` |
| Pod not Running, restarts, Pending | **Pod / scheduling** | `kubectl describe pod` → Events |
| Pods fine, Service unreachable | **networking** | `kubectl get ep <svc>`; selector vs labels |
| `kubectl` itself slow/erroring, nothing schedules, Deployments do not scale | **control plane** | `kubectl get pods -n kube-system`; `crictl ps` on the control-plane node |
| a node NotReady, Pods on it Unknown | **node** | `kubectl describe node`; `systemctl status kubelet` on the node |
| DNS names do not resolve | **cluster DNS** | `kubectl get pods,svc -n kube-system -l k8s-app=kube-dns` |
| volume will not mount, PVC Pending | **storage** | `kubectl describe pvc`; `kubectl get pv,sc` |

The lessons of this week take the layers one by one.

## The loop, one layer at a time

**1. describe** - `kubectl describe <kind> <name>` is the richest single
screen: spec, status, conditions, and at the bottom **Events**. Read the
Events first; they are the cluster telling you what it tried and why it
stopped.

```bash
kubectl describe pod web-7d9f -n shop | tail -20
kubectl get events -n shop --sort-by=.lastTimestamp | tail -20      # the namespace's events, newest last
```

**2. status / conditions** - `STATUS` in `kubectl get pods` is a summary;
`describe` shows the container **State**, **Last State**, **Reason**,
**Exit Code**. `Exit Code 1` is the app; `137` is OOMKilled or SIGKILL;
`CrashLoopBackOff` means it keeps dying - go to logs.

**3. logs** - `kubectl logs <pod> [-c container]`; `--previous` for the
container that just crashed (the current one may have no output yet);
`-f` to watch; `--since=5m`, `--tail=50` to cut noise.

**4. exec / ssh** - when the object looks right and the behaviour is wrong:
`kubectl exec -it <pod> -- sh` and look from inside (env, DNS, curl the
dependency); `ssh node` and `journalctl -u kubelet` when the Pod layer
points at the node.

**5. fix** - edit the object (`kubectl edit`), the manifest
(`/etc/kubernetes/manifests`), the config file, the unit; restart what
needs restarting (`systemctl restart kubelet`; static Pods restart
themselves on manifest change).

**6. verify** - **the step people skip**. Re-run the command that showed
the symptom. `kubectl get pods -w` until Running and Ready; `curl` the
Service; `kubectl get nodes` until Ready. A fix that is not verified is a
guess.

## Avoiding rabbit holes

- **Read the whole error.** `Back-off pulling image "nginx:1.99"` has the
  answer in it. So does `0/3 nodes are available: 3 node(s) had untolerated
  taint`. Most exam failures are a misspelling visible in one `describe`.
- **Change one thing, then verify.** Two changes and a fix teaches you
  nothing and may have broken something else.
- **Compare with a working one.** A sibling Pod, the other node, the
  control-plane manifest from a healthy cluster. `diff` beats reading.
- **Time-box.** On the exam, if a layer gives nothing in 3-4 minutes, flag
  the question and move on. Unanswered questions elsewhere cost more than
  this one.
- **Do not fix the symptom.** Deleting a CrashLoopBackOff Pod makes a new
  one that crashes the same way. Find the cause in logs/events first.
- **Undo what did not help.** A flag you added while guessing is a bug you
  left behind.

## The commands you will type most this week

```bash
kubectl get all -n <ns> -o wide
kubectl describe pod <p> -n <ns>
kubectl logs <p> -n <ns> [-c <c>] [--previous]
kubectl get events -n <ns> --sort-by=.lastTimestamp
kubectl get ep <svc> -n <ns>                     # does the Service have backends?
kubectl get nodes; kubectl describe node <n>
kubectl get pods -n kube-system
ssh <node>; systemctl status kubelet; journalctl -u kubelet -f
crictl ps -a; crictl logs <id>                   # when kubectl itself is down
```

:::exam-tip
Troubleshooting questions on the exam come with a context switch
(`kubectl config use-context ...`) and often a node you must `ssh` into.
Do both at the start, and `exit` back to the base node before the next
question - commands typed on the wrong node or cluster are the most
expensive mistake on the exam.
:::

## Check yourself

1. What is the first thing to decide before typing any command, and why?
2. Name the six steps of the loop and the one most often skipped.
3. A Pod is in CrashLoopBackOff. Why is deleting it not a fix, and what is
   the next command?
