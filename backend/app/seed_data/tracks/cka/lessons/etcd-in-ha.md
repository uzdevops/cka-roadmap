## Consistency across several machines

One etcd member is a database. Three are a **distributed** database that
must agree, on every write, in order, even when one of them is down or slow.
The protocol that makes them agree is **RAFT**, and knowing its shape lets
you reason about every "how many can I lose" question.

## Leader, followers, and a write

At any moment one member is the **leader**; the rest are **followers**.
Every write goes to the leader (followers forward it). The leader:

1. appends the entry to its own log,
2. sends it to the followers,
3. waits until a **majority** of members (itself included) have written it,
4. commits it, applies it, and acknowledges the client,
5. tells the followers to commit.

Reads, by default, also go through the leader (linearizable) so that a read
never returns something an earlier acknowledged write does not show. That is
the consistency Kubernetes relies on: if the API server was told "Pod
created", every later read sees it.

## Quorum

| Members (N) | Quorum (N/2 + 1) | Tolerated failures |
|---|---|---|
| 1 | 1 | 0 |
| 2 | 2 | 0 - worse than 1 |
| 3 | 2 | 1 |
| 4 | 3 | 1 - no better than 3 |
| 5 | 3 | 2 |
| 7 | 4 | 3 |

Why "majority" and not "everyone": waiting for everyone means one slow or
dead member stops the world. Why "majority" and not "anyone": two halves of a
split network could each accept writes and diverge. Majority means at most
one side can have it.

Odd numbers, because an even number raises the quorum without raising the
failures tolerated. **Three is the standard, five for critical clusters,
more than seven is never recommended** - every write waits on more
replication.

## Leader election

Followers expect heartbeats from the leader. If one stops hearing them (the
**election timeout**, ~1 s by default), it becomes a **candidate**, bumps the
term number, and asks for votes; a majority of votes makes it leader. Ties
and near-ties resolve with randomised timeouts. During an election - a
second or so - writes fail and the API server logs errors; Kubernetes
clients retry. A cluster with no quorum (two of three down) **cannot elect a
leader and cannot serve writes**; it serves stale reads at best. That is the
state to recognise: `kubectl get` sometimes works, `kubectl create` hangs,
etcd logs full of "no leader".

```bash
etcdctl endpoint status --cluster --write-out=table     # IS LEADER column, raft term and index
etcdctl endpoint health --cluster
etcdctl member list --write-out=table
```

## Topology

**Stacked** (kubeadm default): each control plane node runs an etcd member
as a static Pod; `--initial-cluster` in each `etcd.yaml` lists all peers;
`kubeadm join --control-plane` adds the new member for you.

**External**: etcd on dedicated hosts, each a systemd service; the API
servers get `--etcd-servers=https://etcd1:2379,https://etcd2:2379,https://etcd3:2379`
and client certificates signed by the etcd CA. Failures are independent of
the control plane, and you can size etcd's hosts (fast SSD - etcd is
latency-sensitive) separately.

```bash
# external: the API server's view
grep etcd-servers /etc/kubernetes/manifests/kube-apiserver.yaml
# stacked: the member's view
grep initial-cluster /etc/kubernetes/manifests/etcd.yaml
# --initial-cluster=cp1=https://192.168.1.10:2380,cp2=https://192.168.1.11:2380,cp3=https://192.168.1.12:2380
```

## Operations that change with HA

- **Backup**: `snapshot save` from any healthy member; one snapshot is the
  whole cluster's state.
- **Restore**: restore the snapshot on **each** member with its own
  `--name`, `--initial-cluster`, `--initial-advertise-peer-urls` and a new
  `--initial-cluster-token`, then start them together - the docs'
  "Restoring an etcd cluster" page has the exact flags. In the exam the
  single-member restore from the cluster-maintenance phase is what is asked.
- **Replacing a member**: `etcdctl member remove <id>`, then `member add`
  with the new peer URL, then start the new member with
  `--initial-cluster-state=existing`. Never let the cluster drop below
  quorum while you do it.
- **Adding a control plane node** (stacked): `kubeadm join --control-plane`
  does the member add.

:::exam-tip
The numbers: 3 → lose 1, 5 → lose 2. The behaviour: below quorum, no writes,
no leader, API server errors, existing Pods unaffected. The flag on the API
server that names the members: `--etcd-servers`. The command that shows the
leader: `etcdctl endpoint status --cluster -w table`.
:::

## Check yourself

1. Walk a write through a 3-member etcd: who does what, and when is the
   client answered?
2. Five members; three are down. Reads? Writes? Why?
3. Why is a 4-member cluster not more available than a 3-member one?
