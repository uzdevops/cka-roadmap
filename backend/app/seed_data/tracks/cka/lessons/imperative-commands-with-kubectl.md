## The cheat sheet that wins the exam

Every minute you spend hand-typing YAML in the exam is a minute you do not
have for the 30 % of marks that are troubleshooting. The commands on this page
generate correct objects in one line. Learn them until they are reflexes.

### Set up the shell first

```bash
alias k=kubectl
export do="--dry-run=client -o yaml"      # k run x --image=nginx $do > x.yaml
export now="--force --grace-period 0"     # k delete pod x $now
source <(kubectl completion bash); complete -o default -F __start_kubectl k
```

### Pods

```bash
k run nginx --image=nginx                                    # a Pod, not a Deployment
k run nginx --image=nginx --port=80 --expose                 # Pod + ClusterIP Service
k run redis --image=redis:alpine -l tier=db                  # with labels
k run busy --image=busybox --command -- sleep 3600           # override the command
k run busy --image=busybox -- --color=green                  # pass args only
k run tmp --rm -it --image=busybox -- sh                     # throwaway shell, deleted on exit
k run tmp --rm -it --image=busybox --restart=Never -- wget -qO- http://web   # one-shot test
k run nginx --image=nginx $do > pod.yaml                     # generate, then edit
```

### Deployments

```bash
k create deployment web --image=nginx --replicas=3
k create deployment web --image=nginx --replicas=3 --port=80 $do > deploy.yaml
k scale deployment web --replicas=5
k set image deployment/web nginx=nginx:1.27
k rollout status deployment/web
k rollout history deployment/web
k rollout undo deployment/web
k rollout undo deployment/web --to-revision=2
```

### Services

```bash
k expose deployment web --port=80 --target-port=8080                       # ClusterIP
k expose deployment web --name=web-np --type=NodePort --port=80            # NodePort, random port
k expose pod redis --name=redis-service --port=6379                        # from a Pod
k create service clusterip web --tcp=80:8080 $do                           # without a target object
k create service nodeport web --tcp=80:8080 --node-port=30080 $do          # the only way to set nodePort from a flag
```

### Namespaces, ConfigMaps, Secrets, ServiceAccounts

```bash
k create namespace dev
k create configmap app-cfg --from-literal=COLOR=blue --from-literal=MODE=prod
k create configmap app-cfg --from-file=config.properties
k create secret generic db --from-literal=password=hunter2
k create secret docker-registry regcred --docker-server=reg.io --docker-username=u --docker-password=p
k create secret tls web-tls --cert=tls.crt --key=tls.key
k create serviceaccount builder
k create token builder
```

### RBAC

```bash
k create role dev --verb=get,list,create --resource=pods,deployments -n dev
k create rolebinding dev-binding --role=dev --user=ahmad -n dev
k create clusterrole node-reader --verb=get,list,watch --resource=nodes
k create clusterrolebinding node-reader-b --clusterrole=node-reader --user=ahmad
k auth can-i create pods --as ahmad -n dev
```

### Jobs, CronJobs, Ingress, quotas

```bash
k create job hello --image=busybox -- echo hello
k create cronjob hello --image=busybox --schedule="*/5 * * * *" -- echo hello
k create ingress web --rule="shop.example.com/=web:80" --rule="/api=api:8080"
k create quota dev-quota --hard=pods=10,requests.cpu=4 -n dev
k create priorityclass high --value=100000
```

### Namespaces and contexts

```bash
k config get-contexts
k config use-context cluster2
k config set-context --current --namespace=dev        # stop typing -n
k get pods -A                                         # every namespace
```

### Getting information out fast

```bash
k get pods -o wide
k get pod web -o yaml
k get pods --show-labels
k get pods -l app=web,tier=frontend
k get pods --field-selector=status.phase=Pending
k get events --sort-by=.lastTimestamp | tail
k describe pod web | tail -20
k explain pod.spec.containers.livenessProbe
k api-resources | grep -i netpol
k get pods -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName
k get pods --sort-by=.metadata.creationTimestamp
```

:::exam-tip
Things `kubectl create/run/expose` **cannot** do from flags - set a nodePort
on `expose`, add a volume, a probe, resources, a toleration, a second
container, an init container. For all of those: generate with `$do`, edit the
file, apply. Knowing which side of that line a task is on saves the decision
time.
:::

:::tip
`k create <kind> --help` shows every flag with an example. It is faster than
the docs for the imperative commands and it is always there.
:::

## Check yourself

1. Write, from memory, the one-liner that creates a Pod **and** a ClusterIP
   Service for it.
2. Which command creates a NodePort Service with a *specific* node port
   without editing YAML?
3. Name three things `kubectl run` cannot set from a flag, and say what you do
   instead.
