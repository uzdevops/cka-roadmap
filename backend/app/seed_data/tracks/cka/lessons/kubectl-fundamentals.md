## The command you will type a thousand times

`kubectl` follows a consistent grammar. Learn the grammar, not a list of commands.

```text
kubectl <verb> <resource-type> <name> [flags]
        get     pods            web    -n prod -o wide
```

## Reading state

```bash
kubectl get pods                          # current namespace
kubectl get pods -A                       # every namespace
kubectl get pods -o wide                  # + node, pod IP, nominated node
kubectl get pods -w                       # watch changes live
kubectl get pods --show-labels
kubectl get pods -l app=web,tier!=cache   # label selector
kubectl get pods --field-selector status.phase=Running
kubectl get all -n kube-system            # common workload types at once
```

Sorting and custom columns turn `get` into a reporting tool:

```bash
kubectl get pods --sort-by=.status.startTime
kubectl get nodes --sort-by=.metadata.name

kubectl get pods -o custom-columns=\
'NAME:.metadata.name,NODE:.spec.nodeName,IMAGE:.spec.containers[*].image'

# JSONPath for scripting
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.podIP}{"\n"}{end}'
```

:::exam-tip
Questions often say "write the result to `/opt/answer.txt`". Build the command,
check the output on screen, *then* append `> /opt/answer.txt`. Marks are lost to
files containing an error message far more often than to wrong commands.
:::

## Describe: the first debugging step

`kubectl get` shows you fields. `kubectl describe` shows you fields **plus
events**, which is where the reason for a failure lives.

```bash
kubectl describe pod web-5d4f8b6c9-abcde
kubectl describe node cka-worker
kubectl describe svc web
```

The bottom of the output is the part that matters:

```text
Events:
  Type     Reason     Age   From               Message
  ----     ------     ----  ----               -------
  Normal   Scheduled  2m    default-scheduler  Successfully assigned default/web to cka-worker
  Normal   Pulling    2m    kubelet            Pulling image "nginx:1.27"
  Warning  Failed     1m    kubelet            Failed to pull image: not found
  Warning  BackOff    30s   kubelet            Back-off pulling image "nginx:1.27"
```

## Logs

```bash
kubectl logs web-5d4f8b6c9-abcde
kubectl logs web-5d4f8b6c9-abcde -c sidecar      # a specific container
kubectl logs -f deployment/web                   # follow, via the Deployment
kubectl logs --previous web-5d4f8b6c9-abcde      # the container that just crashed
kubectl logs -l app=web --tail=50 --all-containers
kubectl logs --since=10m web-5d4f8b6c9-abcde
```

:::tip
`--previous` is the flag that solves CrashLoopBackOff. The current container has
just started and has no useful output; the *previous* one is the one that died
and printed the stack trace.
:::

## Exec and port-forward

```bash
kubectl exec -it web-5d4f8b6c9-abcde -- sh
kubectl exec web-5d4f8b6c9-abcde -- env
kubectl exec web-5d4f8b6c9-abcde -c sidecar -- cat /etc/config/app.conf

kubectl port-forward svc/web 8080:80
kubectl port-forward pod/web-5d4f8b6c9-abcde 8080:80
```

For images with no shell (distroless, scratch), use an ephemeral debug container:

```bash
kubectl debug -it web-5d4f8b6c9-abcde --image=busybox --target=web
```

## Creating things: imperative first

In the exam, imperative commands with `--dry-run=client -o yaml` are dramatically
faster than writing YAML from memory.

```bash
kubectl run nginx --image=nginx --restart=Never
kubectl create deployment web --image=nginx:1.27 --replicas=3
kubectl expose deployment web --port=80 --target-port=8080 --name=web-svc
kubectl create configmap app-config --from-literal=LOG_LEVEL=debug
kubectl create secret generic db-pass --from-literal=password=s3cret
kubectl create job backup --image=busybox -- /bin/sh -c 'echo backing up'
kubectl create cronjob nightly --image=busybox --schedule='0 2 * * *' -- /bin/sh -c 'echo hi'
kubectl create serviceaccount deploy-bot
kubectl create role reader --verb=get,list --resource=pods
kubectl create rolebinding reader-bind --role=reader --serviceaccount=default:deploy-bot
```

The pattern that scaffolds any manifest:

```bash
kubectl create deployment web --image=nginx --dry-run=client -o yaml > web.yaml
vim web.yaml          # add the fields the generator cannot produce
kubectl apply -f web.yaml
```

## Modifying things

```bash
kubectl apply -f manifest.yaml            # declarative, idempotent, preferred
kubectl edit deployment web               # opens $EDITOR, applies on save
kubectl scale deployment web --replicas=5
kubectl set image deployment/web nginx=nginx:1.28
kubectl label pod web env=prod
kubectl annotate deployment web kubernetes.io/change-cause="bump to 1.28"
kubectl patch deployment web -p '{"spec":{"replicas":4}}'
kubectl rollout status deployment/web
kubectl rollout undo deployment/web
```

## Deleting things

```bash
kubectl delete pod web-5d4f8b6c9-abcde
kubectl delete -f manifest.yaml
kubectl delete pods -l app=web
kubectl delete pod web --force --grace-period=0     # only when truly stuck
```

:::warning
Deleting a Pod that belongs to a Deployment does not remove it - the ReplicaSet
controller creates a replacement within seconds. To actually remove the workload,
delete the Deployment. This trips people up constantly.
:::

## kubectl explain: your in-exam documentation

You are allowed the official docs during the exam, but `explain` is faster than
searching a website.

```bash
kubectl explain pod.spec
kubectl explain pod.spec.containers.resources
kubectl explain deployment.spec.strategy --recursive | head -30
kubectl api-resources                    # every type, its short name and apiVersion
kubectl api-versions
```

:::exam-tip
`kubectl explain <type> --recursive` prints the entire field tree. When you
cannot remember whether it is `securityContext.runAsUser` or
`securityContext.runAsUserName`, this answers it in two seconds without leaving
the terminal.
:::

## Useful shorthands

| Long | Short |
| --- | --- |
| pods | po |
| deployments | deploy |
| services | svc |
| namespaces | ns |
| configmaps | cm |
| persistentvolumeclaims | pvc |
| statefulsets | sts |
| daemonsets | ds |
| replicasets | rs |
| serviceaccounts | sa |

## Check yourself

1. Which command shows *why* a Pod failed to schedule?
2. How do you read the logs of a container that has already crashed and restarted?
3. Generate the YAML for a 3-replica nginx Deployment without creating it.
