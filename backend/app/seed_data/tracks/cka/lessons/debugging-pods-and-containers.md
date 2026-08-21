## Working an application failure from the front

A two-tier app: a web Pod behind a Service, talking to a database Pod
behind its own Service. "The site is down." Start where the user starts and
walk **inward**, one hop at a time, checking each hop before the next.

```
 user ──▶ web-service (NodePort 30081) ──▶ web Pod :8080 ──▶ db-service :3306 ──▶ db Pod :3306
```

### Hop 1: the front door

```bash
curl -m 3 http://<node-ip>:30081                # what the user sees
kubectl get svc web-service -n shop
kubectl describe svc web-service -n shop
#   Selector: name=webapp-mysql      Port: 8080  TargetPort: 8080  NodePort: 30081
#   Endpoints: 10.244.1.5:8080       <- EMPTY here = the Service matches no Pod
```

The Service is a selector and ports. Check:

- **Endpoints non-empty?** `kubectl get ep web-service -n shop`. Empty
  means the selector matches no **ready** Pod: labels differ (`name=webapp`
  vs `name=webapp-mysql` - the classic), or the Pod is not Ready.
- **Ports right?** `port` is the Service's; `targetPort` must be the
  **container's** listening port; `nodePort` the one the user was told.

```bash
kubectl get pods -n shop --show-labels
kubectl get pods -n shop -l name=webapp-mysql      # what the selector actually matches
```

### Hop 2: the web Pod

```bash
kubectl get pods -n shop
kubectl describe pod webapp-mysql -n shop | tail -25
kubectl logs webapp-mysql -n shop
kubectl logs webapp-mysql -n shop --previous        # the crashed container's output
```

| STATUS | Meaning | Look at |
|---|---|---|
| `Pending` | not scheduled | Events: insufficient cpu/memory, taints, nodeSelector, PVC Pending |
| `ContainerCreating` | scheduled, not started | Events: volume mount failed, ConfigMap/Secret missing, image pulling |
| `ImagePullBackOff` / `ErrImagePull` | image | name/tag typo, private registry without imagePullSecret, no network |
| `CreateContainerConfigError` | config | a referenced ConfigMap/Secret key does not exist |
| `CrashLoopBackOff` | starts and dies | `logs --previous`; exit code; command/args; missing env/config |
| `OOMKilled` (in describe) | memory limit | raise `limits.memory` or fix the leak |
| `Error` / `Completed` | ran and exited | fine for a Job; wrong for a server - the process exited |
| `Running` but `0/1` READY | readiness probe failing | probe path/port; app not listening yet |
| `Running` `1/1` and still broken | the app itself | logs, env, exec in and curl the dependency |

Exit codes in `describe` under **Last State**: `1` application error,
`137` killed (OOM or eviction), `139` segfault, `143` SIGTERM, `126/127`
command not found or not executable (wrong `command:`).

### Hop 3: what the app was told

```bash
kubectl describe pod webapp-mysql -n shop | grep -A8 Environment
#   DB_Host:      mysql-service
#   DB_User:      root
#   DB_Password:  <set to the key 'password' in secret 'db-secret'>
kubectl exec -it webapp-mysql -n shop -- env | grep DB_
kubectl exec -it webapp-mysql -n shop -- nslookup mysql-service
kubectl exec -it webapp-mysql -n shop -- nc -zv mysql-service 3306
```

A wrong `DB_Host` (`mysql` where the Service is `mysql-service`), a wrong
password, a wrong port - the app's log says "connection refused" or "access
denied"; the env shows why.

### Hop 4: the database Service and Pod

Same two checks again, one hop in:

```bash
kubectl get svc,ep mysql-service -n shop        # endpoints non-empty? port 3306 → targetPort 3306?
kubectl get pods -n shop -l name=mysql          # matches the Service selector?
kubectl logs mysql -n shop                      # did MySQL start? password env set?
kubectl describe pod mysql -n shop | grep -A4 Environment
```

## Fixing

Most fixes are one field: a label, a port, an env value, an image tag.

```bash
kubectl edit svc web-service -n shop            # selector / ports - Services are editable in place
kubectl edit deployment web -n shop             # env, image, probes - rolls new Pods
kubectl edit pod webapp-mysql -n shop           # only image/a few fields; for anything else:
kubectl get pod webapp-mysql -n shop -o yaml > p.yaml   # edit, then `kubectl replace --force -f p.yaml`
```

Then **verify at the front door**: `curl` the NodePort again, or `kubectl
port-forward svc/web-service 8080:8080 -n shop` and curl localhost.

:::exam-tip
The exam's application-failure questions are exactly this walk, in a
namespace they name. Check in order - Service endpoints, selector vs
labels, ports, Pod status, logs, env, the next hop - and you will find it
in under five minutes. `kubectl get all -n <ns> -o wide --show-labels` on
one screen is the fastest first look.
:::

## Check yourself

1. A Service's Endpoints are empty. What are the two causes, and which
   command tells them apart?
2. A Pod is `Running` but `0/1` READY. What is failing, and what is not?
3. The web Pod's log says "cannot connect to mysql". List the next three
   checks, in order.
