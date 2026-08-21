## Two tools, split on purpose

Until etcd 3.5, `etcdctl` did everything. Since 3.5 the project split the
commands that operate on **files** - restore a snapshot, inspect it,
defragment a data directory offline - into a second binary, **`etcdutl`**,
and left `etcdctl` with the commands that talk to a **running server**. The
reasoning: a restore must never accidentally be pointed at a live cluster,
and a tool that cannot open a network connection cannot do that.

| Task | Tool | Talks to a server? |
|---|---|---|
| `snapshot save` | `etcdctl` | yes - needs endpoint + TLS |
| `endpoint health` / `endpoint status` / `member list` | `etcdctl` | yes |
| `get` / `put` / `del` | `etcdctl` | yes |
| `snapshot restore` | **`etcdutl`** | no - reads a file, writes a directory |
| `snapshot status` | **`etcdutl`** | no |
| `defrag` (offline, on a data dir) | **`etcdutl`** | no |

`etcdctl snapshot restore` and `etcdctl snapshot status` still exist in 3.5 as
deprecated aliases and print a warning. They are removed in 3.6. Write
`etcdutl` for both and the habit is future-proof.

## Where the binaries are

On a kubeadm control plane they are **inside the etcd container**, not on
the host by default:

```bash
kubectl exec -n kube-system etcd-controlplane -- etcdctl version
kubectl exec -n kube-system etcd-controlplane -- etcdutl version
```

For a snapshot that is fine - exec in, run it, the file lands inside the
container's filesystem; write it to a path that is a hostPath mount
(`/var/lib/etcd` is one, or add `/opt`) to get it onto the node. For a
restore you want the binary on the **host**, because you are writing a new
directory on the host and editing a host file:

```bash
# copy the binaries out of the image once
kubectl cp -n kube-system etcd-controlplane:/usr/local/bin/etcdutl /usr/local/bin/etcdutl
chmod +x /usr/local/bin/etcdutl
# or: download the matching release tarball from github.com/etcd-io/etcd
```

Exam environments generally have both on the control plane node already;
`which etcdctl etcdutl` is the first thing to check.

## Version matters

Use the tool version that matches the etcd server:

```bash
kubectl exec -n kube-system etcd-controlplane -- etcd --version
etcdctl version
```

A snapshot taken by a 3.5 server restores cleanly with a 3.5 `etcdutl`. Mixing
a 3.4 `etcdctl` against a 3.5 server mostly works for `get`/`save`, but the
error messages get confusing; matching them removes one variable.

## The commands side by side

```bash
# --- etcdctl: everything that needs the live server ---------------------
export ETCDCTL_API=3
export ETCDCTL_ENDPOINTS=https://127.0.0.1:2379
export ETCDCTL_CACERT=/etc/kubernetes/pki/etcd/ca.crt
export ETCDCTL_CERT=/etc/kubernetes/pki/etcd/server.crt
export ETCDCTL_KEY=/etc/kubernetes/pki/etcd/server.key

etcdctl endpoint health
etcdctl endpoint status --write-out=table
etcdctl member list --write-out=table
etcdctl snapshot save /opt/snap.db

# --- etcdutl: everything that works on files ---------------------------
etcdutl snapshot status /opt/snap.db --write-out=table
etcdutl snapshot restore /opt/snap.db --data-dir /var/lib/etcd-from-backup
etcdutl defrag --data-dir /var/lib/etcd            # only with etcd stopped
```

Note the environment variables: `etcdctl` reads `ETCDCTL_*` for every flag,
so exporting them once per shell means every later command is short. They
have no effect on `etcdutl`, which does not need them.

:::exam-tip
If a task says "use etcdctl to restore" - do it, it works with a warning. If
it says nothing, use `etcdutl`. Either way the restore takes **no** endpoint
and **no** certificate flags; adding them is harmless with `etcdctl` and an
error with `etcdutl`. Keep the two mental columns: network → etcdctl, file →
etcdutl.
:::

## Check yourself

1. Why did the etcd project move `snapshot restore` out of `etcdctl`?
2. You exported the `ETCDCTL_*` variables. Does `etcdutl snapshot restore`
   use them?
3. Where do you find `etcdutl` on a kubeadm control plane if it is not on the
   host PATH?
