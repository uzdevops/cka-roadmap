## Time is the resource

Two hours, fifteen to twenty tasks: six to eight minutes each, including
reading, context switching, verifying and the one task that goes wrong.
Every minute saved on a one-liner is a minute for the troubleshooting task
worth 13%. This lesson is the list of things that are faster than the way
you probably do them.

## Minute zero: the terminal

```bash
alias k=kubectl                                  # usually pre-set on the exam; check
export do="--dry-run=client -o yaml"             # k run x --image=nginx $do > x.yaml
export now="--force --grace-period=0"            # k delete pod x $now
source <(kubectl completion bash); complete -o default -F __start_kubectl k
```

```bash
printf 'set ts=2 sw=2 et ai nu\n' >> ~/.vimrc
```

(`et` expands tabs - a tab in YAML is a syntax error; `ai` autoindent; `nu`
line numbers for error messages.) In vim: `:set paste` before pasting from
the docs, `>>`/`<<` with a visual block to indent/dedent, `u` undo.

## The generators

Every object that has an imperative `create`/`run`, and the flags that
matter:

| Object | Command |
|---|---|
| Pod | `k run web --image=nginx --port=80 -l app=web --env=A=1 --command -- sleep 3600` |
| Pod, throwaway | `k run tmp --image=busybox:1.28 --rm -it --restart=Never -- sh` |
| Deployment | `k create deploy web --image=nginx --replicas=3 --port=80` |
| Service from Deployment/Pod | `k expose deploy web --name=web-svc --port=80 --target-port=8080 --type=NodePort` |
| Service standalone | `k create svc clusterip web --tcp=80:8080`; `k create svc nodeport web --tcp=80:8080 --node-port=30080` |
| Job | `k create job j --image=busybox -- sh -c "echo hi"` |
| CronJob | `k create cj cj --image=busybox --schedule="*/5 * * * *" -- sh -c "date"` |
| ConfigMap | `k create cm c --from-literal=K=V --from-file=app.conf --from-env-file=.env` |
| Secret | `k create secret generic s --from-literal=pass=x`; `... tls t --cert= --key=`; `... docker-registry r --docker-server= ...` |
| Namespace / SA | `k create ns x`; `k create sa x` |
| Role / ClusterRole | `k create role r --verb=get,list --resource=pods,pods/log`; `k create clusterrole cr --verb=get --resource=nodes` |
| RoleBinding / CRB | `k create rolebinding rb --role=r --user=u --serviceaccount=ns:sa`; `k create clusterrolebinding crb --clusterrole=cr --group=g` |
| Ingress | `k create ingress i --rule="host/path=svc:80" --class=nginx --annotation k=v` |
| Quota / limits | `k create quota q --hard=pods=10,cpu=4`; (LimitRange: YAML) |
| PriorityClass | `k create priorityclass high --value=1000` |
| Token | `k create token <sa>` |
| HPA | `k autoscale deploy web --min=2 --max=5 --cpu-percent=50` |
| Taint / label / annotate | `k taint node n k=v:NoSchedule`; `k label node n disk=ssd`; `k annotate deploy d kubernetes.io/change-cause="..."` |
| Scale / image / rollout | `k scale deploy web --replicas=5`; `k set image deploy web nginx=nginx:1.27`; `k rollout undo/status/history deploy web` |
| Node ops | `k cordon n`; `k drain n --ignore-daemonsets --delete-emptydir-data`; `k uncordon n` |

No generator exists for: PV, PVC, StorageClass, NetworkPolicy, DaemonSet,
StatefulSet, LimitRange, static Pods' placement, Pod fields beyond the
basics. For those: **generate the nearest thing, then edit** (`k run ...
$do > f.yaml`; `k create deploy ... $do` and change `kind`), or copy from
the docs.

## dry-run patterns

```bash
k run web --image=nginx $do > web.yaml; vi web.yaml; k apply -f web.yaml        # generate, add the field, apply
k create deploy web --image=nginx $do | sed 's/kind: Deployment/kind: DaemonSet/' > ds.yaml   # type swap
k get deploy web -o yaml > web.yaml                                              # export a live object to edit
k apply -f x.yaml --dry-run=server                                               # validate against the API without creating
k run web --image=nginx $do | k apply -f -                                       # the same as without $do, but composable
```

## Editing live

| Object | In place? |
|---|---|
| Deployment, Service, ConfigMap, Role, NetworkPolicy, PV... | `k edit` - yes |
| Pod | only image, activeDeadlineSeconds, tolerations (add). Else: `k edit` → rejected → `k replace --force -f /tmp/kubectl-edit-*.yaml` |
| Static Pod | edit the file in `/etc/kubernetes/manifests` |
| Immutable field | `k delete` + `k apply`, or `k replace --force` |

```bash
k edit pod web              # quick look-and-fix
k patch deploy web -p '{"spec":{"replicas":4}}'
k set env deploy web MODE=prod
k set resources deploy web -c nginx --limits=memory=256Mi
k set serviceaccount deploy web sa-name
```

## Looking things up faster than the docs

```bash
k explain pod.spec.tolerations             # every field, with types and descriptions
k explain deploy.spec.strategy --recursive
k create role --help | grep -A5 Examples   # every `create` has Examples
k api-resources | grep -i netpol           # short names and whether namespaced
k api-resources --namespaced=false
```

## Fast verification

```bash
k get all -n ns -o wide --show-labels       # one screen
k get pod x -o jsonpath='{.spec.containers[*].image}'
k get pod x -w                              # watch until Running, Ctrl-C
k describe pod x | tail -15                 # Events only
k logs x --tail=20
k rollout status deploy x
k auth can-i get pods --as user -n ns
```

## The drills

Time each, target in brackets. Repeat until you beat the target three
times running.

1. Pod `drill1` nginx:alpine with label `app=d1`, in new namespace `drill`,
   exposed on port 80 as ClusterIP, then NodePort 30085. **[90 s]**
2. Deployment `drill2` 3 replicas nginx:1.25 → set image to 1.26 → check
   rollout → undo → annotate change-cause. **[90 s]**
3. Role `pod-reader` (get, list, watch pods) + RoleBinding for
   ServiceAccount `drill/reader`, then `auth can-i` as it. **[60 s]**
4. Static Pod `drill4` busybox `sleep 1d` on the control plane. **[60 s]**
5. Pod `drill5` with emptyDir at `/cache` and a `requests.cpu: 100m`
   via `$do` + vi. **[90 s]**
6. NetworkPolicy default-deny ingress in `drill`, then allow 80 to
   `app=d1` from `role=fe`. **[120 s]**
7. Export every node's name and InternalIP to a file. **[45 s]**
8. etcd snapshot to `/opt/s.db` and `snapshot status`. **[90 s]**
9. `cordon`, `drain`, `uncordon` a worker; confirm Pods moved. **[60 s]**
10. Find a Deployment with a broken image tag (make one), fix it with
    `set image`, confirm Available. **[60 s]**

:::exam-tip
The single highest-value habit: **never write YAML from a blank file**.
`k run`/`k create ... $do`, `k get ... -o yaml`, or the docs - then edit
three lines. Blank-file YAML is slow and produces indentation bugs you
will not see under pressure.
:::

## Check yourself

1. Which objects have no imperative generator, and what do you do instead?
2. What is the fastest way to change an immutable field on a running Pod?
3. Write the one command that creates a NodePort Service on port 80,
   nodePort 30080, for a Deployment named `web`.
