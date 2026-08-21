## The Docker knobs, in a Pod spec

Everything from the previous lesson - which user, which capabilities,
privileged or not - lives under `securityContext`. It exists at **two
levels**, and that is the part to get right:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ubuntu-sleeper
spec:
  securityContext:                 # POD level: applies to every container, and to volumes
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000                  # group ownership of mounted volumes
  containers:
    - name: ubuntu
      image: ubuntu
      command: ["sleep", "3600"]
      securityContext:             # CONTAINER level: overrides the Pod level for this container
        runAsUser: 1010
        capabilities:              # capabilities exist ONLY at container level
          add: ["SYS_TIME", "NET_ADMIN"]
          drop: ["ALL"]
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        privileged: false
```

| Field | Pod level | Container level |
|---|---|---|
| `runAsUser`, `runAsGroup`, `runAsNonRoot` | yes | yes (wins) |
| `fsGroup`, `supplementalGroups`, `seccompProfile`, `sysctls` | yes | (seccomp also per container) |
| `capabilities` | **no** | yes |
| `privileged`, `allowPrivilegeEscalation`, `readOnlyRootFilesystem` | **no** | yes |

Container-level settings override Pod-level ones for that container. The
common exam mistake is putting `capabilities` under the Pod's
`securityContext` - it is simply not a valid field there, and the API server
says so.

```bash
kubectl explain pod.spec.securityContext --recursive
kubectl explain pod.spec.containers.securityContext --recursive
```

## The fields you will use

```yaml
securityContext:
  runAsUser: 1010               # UID the process runs as
  runAsNonRoot: true            # refuse to start if the image would run as root
  capabilities:
    add: ["NET_ADMIN"]
    drop: ["ALL"]               # then add back only what is needed
  privileged: true              # everything - CNI/storage plugins only
  allowPrivilegeEscalation: false   # no setuid binaries gaining root
  readOnlyRootFilesystem: true      # mount emptyDirs for anything that must write
```

```bash
kubectl exec ubuntu-sleeper -- whoami            # root? or 1010?
kubectl exec ubuntu-sleeper -- id
kubectl exec ubuntu-sleeper -- date -s "19 APR 2012 11:14:00"   # works only with SYS_TIME
kubectl get pod ubuntu-sleeper -o jsonpath='{.spec.containers[0].securityContext}'
```

:::exam-tip
`securityContext` is immutable on a running Pod. The sequence is `kubectl get
pod X -o yaml > x.yaml`, edit, `kubectl replace --force -f x.yaml`. Check the
level: user → either level; capabilities → container level, under the
container, not under the Pod. Then `kubectl exec X -- whoami` to prove it.
:::

## Why it matters, in two lines

A web server does not need to be root, and it does not need `SYS_ADMIN`. If
it is compromised, `runAsNonRoot` plus dropped capabilities plus a read-only
root filesystem turn "attacker owns the node" into "attacker owns a process
that cannot write, cannot escalate, and cannot bind below 1024".

## Pod Security admission: the cluster enforcing it

You can set this per Pod forever, or tell the cluster to **refuse** Pods that
do not meet a standard. The built-in `PodSecurity` admission plugin applies
one of three profiles per namespace, via labels:

```bash
kubectl label namespace dev pod-security.kubernetes.io/enforce=restricted
kubectl label namespace dev pod-security.kubernetes.io/warn=restricted
```

| Profile | Allows |
|---|---|
| `privileged` | anything |
| `baseline` | no privileged, no hostPath/hostNetwork/hostPID, limited capabilities |
| `restricted` | baseline plus: must run as non-root, drop ALL capabilities, seccomp set, no privilege escalation |

`enforce` rejects, `warn` prints a warning, `audit` logs. A Pod that fails
`restricted` is refused with a message listing every field it needs -
`allowPrivilegeEscalation != false`, `unrestricted capabilities`, `runAsNonRoot
!= true` - which is also a handy checklist for writing a compliant spec.

:::tip
`restricted` is strict enough to break many images (anything that insists on
root). Start with `warn=restricted` on a namespace, read the warnings for a
day, then enforce.
:::

## Check yourself

1. `runAsUser` at both Pod and container level with different values - which
   wins, for that container?
2. Where may `capabilities` be set, and what is the error if you put it at
   the other level?
3. What does labelling a namespace `pod-security.kubernetes.io/enforce=restricted`
   do to a Pod that runs as root?
