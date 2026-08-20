## What etcd is

etcd is a **distributed, consistent key-value store**. Strip the adjectives and
it is a dictionary: you put a value under a key, you get it back by the key.
Add them back and you get the reason Kubernetes chose it:

- **Distributed** - it runs as a cluster of members and stays available if a
  minority of them die.
- **Consistent** - every member agrees on every value, in order. A read never
  returns a stale answer from a lagging member. This is the property that makes
  it safe to store *the* truth about a cluster in it.

Kubernetes stores everything in etcd - every Pod, Service, Secret, Node,
ConfigMap, every RBAC rule. The API server is, at heart, a validating front
door in front of etcd. If etcd is gone, the cluster has no memory; if it is
slow, everything is slow.

## Keys, values and the tree

etcd keys are flat strings, but by convention they look like paths, and
Kubernetes uses that convention heavily:

```
/registry/pods/default/web
/registry/deployments/kube-system/coredns
/registry/secrets/payroll/db-creds
```

Values are the serialised objects (protobuf, not JSON, which is why you cannot
just read them with your eyes).

## The etcdctl basics

`etcdctl` is the client. Three things to set up every time:

```bash
export ETCDCTL_API=3          # v3 API - the only one Kubernetes uses
# and the endpoint plus TLS client credentials, covered in the next lesson
```

The verbs you need:

```bash
etcdctl put name "ahmad"           # write
etcdctl get name                   # read -> prints key and value
etcdctl get name --print-value-only
etcdctl get / --prefix --keys-only # list every key under /
etcdctl del name                   # delete

etcdctl endpoint health            # is this member healthy?
etcdctl endpoint status --write-out=table   # version, DB size, leader, raft index
etcdctl member list                # who is in the cluster
```

```bash
# The Kubernetes-specific habit: count objects of one kind straight from etcd
etcdctl get /registry/pods --prefix --keys-only | wc -l
```

:::tip
`--write-out=table` on `endpoint status` and `member list` turns an unreadable
line into a table with the leader marked. Use it every time.
:::

## How it stays consistent: RAFT in one paragraph

Members elect a **leader**. Every write goes to the leader, which appends it to
its log and sends it to the followers; once a **majority** (quorum) has written
it, the write is committed and acknowledged. If the leader dies, the followers
elect a new one from among those with the most complete log. Because a write
needs a majority, a cluster of N members tolerates the loss of
`(N-1)/2` members:

| Members | Quorum | Can lose |
|---|---|---|
| 1 | 1 | 0 |
| 3 | 2 | 1 |
| 5 | 3 | 2 |
| 4 | 3 | 1 - no better than 3, so never do this |

Odd numbers only. Three for most clusters, five if you can afford it.

:::exam-tip
The exam does not ask you to tune RAFT. It asks you to **back up and restore
etcd** (a task in the cluster-maintenance phase) and to recognise when etcd is
the reason the API server is failing. Understanding quorum is what lets you
reason about "two of three etcd members are down - is the cluster writable?"
(No.)
:::

## Two things beginners get wrong

1. **"It's a database, I'll query it."** You do not write to etcd by hand on a
   Kubernetes cluster. Every write goes through the API server, which
   validates, admits and versions it. `etcdctl put` on a Kubernetes key is how
   you corrupt a cluster.
2. **"Backups are the API server's job."** They are yours. etcd does not back
   itself up; `etcdctl snapshot save` does, and it has to be scheduled.

## Check yourself

1. Why does Kubernetes need etcd to be *consistent*, not just available?
2. You have five etcd members; two are down. Can the cluster accept writes?
   Why?
3. Which environment variable and which three flags does almost every
   `etcdctl` command on a kubeadm cluster need? (You will confirm this in the
   next lesson.)
