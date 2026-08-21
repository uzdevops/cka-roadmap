## Attaching storage to a Pod

A container's filesystem dies with the container. A **volume** is a
directory made available to the containers of a Pod, with a lifetime and a
backing store defined by its **type**. Two halves in the spec:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: random-number
spec:
  containers:
    - name: alpine
      image: alpine
      command: ["sh", "-c", "shuf -i 0-100 -n 1 >> /opt/number.out"]
      volumeMounts:                  # 2. where in THIS container it appears
        - name: data
          mountPath: /opt
  volumes:                           # 1. the volume, at Pod level
    - name: data
      hostPath:
        path: /data
        type: DirectoryOrCreate
```

`volumes` declares it once for the Pod; each container that wants it adds a
`volumeMounts` entry by name. Several containers may mount the same volume -
that is the multi-container pattern.

## The types you will meet

| Type | Backed by | Lifetime | Use |
|---|---|---|---|
| `emptyDir` | a directory on the node (or RAM with `medium: Memory`) | the Pod | scratch space, hand-off between containers |
| `hostPath` | a path on the node | the node's disk | node agents that need `/var/log` or the Docker socket; **not** application data |
| `configMap`, `secret`, `downwardAPI`, `projected` | API objects | the Pod | configuration as files |
| `persistentVolumeClaim` | whatever PV the claim is bound to | beyond the Pod | real data - the next three lessons |
| `nfs` | an NFS export | the server | shared filesystem, the simplest "network storage" that works anywhere |
| `local` | a disk on a specific node, via a PV | the node | fast local disks with node affinity |
| `csi` | a CSI driver | the driver's | what a PVC usually resolves to |

`emptyDir` and `hostPath` are the two to know by heart.

```yaml
volumes:
  - name: cache
    emptyDir: {}
  - name: cache-in-memory
    emptyDir:
      medium: Memory
      sizeLimit: 256Mi
```

```yaml
volumes:
  - name: node-logs
    hostPath:
      path: /var/log
      type: Directory          # "" | DirectoryOrCreate | Directory | FileOrCreate | File | Socket
```

## Why hostPath does not scale

`hostPath` mounts a directory of **whatever node the Pod lands on**. On a
single-node lab that is indistinguishable from persistent storage; on a
three-node cluster the Pod is rescheduled to node02 and finds an empty
directory. It also lets a Pod read and write the node's filesystem, which is
why `baseline` Pod Security forbids it. Legitimate uses: DaemonSets that
genuinely need the node (log shippers, monitoring agents, CSI node plugins),
and the control plane's own static Pods mounting `/etc/kubernetes/pki`.

:::warning
A task that says "data must survive the Pod being rescheduled to another
node" is **not** a hostPath task, however tempting the short YAML. It is a
PVC task.
:::

## Reading what a Pod mounts

```bash
kubectl get pod random-number -o jsonpath='{.spec.volumes}'
kubectl describe pod random-number | grep -A6 "Mounts:\|Volumes:"
kubectl exec random-number -- df -h /opt
kubectl exec random-number -- ls -la /opt
```

:::exam-tip
Volumes and mounts are **immutable** on a running Pod, like most of the spec.
"Add a volume to Pod X" is get-yaml, edit, `replace --force`. Two things
graders check: the `volumeMounts` entry is under the right **container**, and
its `name` matches an entry in `volumes` exactly.
:::

## Check yourself

1. Where does `volumes` go in a Pod spec, and where does `volumeMounts` go?
2. When does an `emptyDir` disappear, and when does a `hostPath` directory?
3. Why is `hostPath` the wrong answer for a database's data on a
   multi-node cluster?
