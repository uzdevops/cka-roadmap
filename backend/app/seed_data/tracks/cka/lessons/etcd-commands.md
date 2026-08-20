## The API version, once and for all

etcd had two client APIs. Kubernetes uses **v3**, and modern `etcdctl`
binaries default to v3 - but older ones defaulted to v2, and the two are not
compatible. That is why you see `ETCDCTL_API=3` in front of every command in
every tutorial: it costs nothing and removes a whole class of "why does this
not work" moments.

```bash
etcdctl version
# etcdctl version: 3.5.x
# API version: 3.5
```

If `etcdctl` is not on your PATH, it is inside the etcd container:

```bash
kubectl exec -n kube-system etcd-controlplane -- etcdctl version
```

## The commands worth memorising

With the connection flags exported as in the previous lesson:

```bash
# --- health and membership -------------------------------------------
etcdctl endpoint health
etcdctl endpoint status --write-out=table
etcdctl member list --write-out=table

# --- read ------------------------------------------------------------
etcdctl get /registry/namespaces --prefix --keys-only
etcdctl get /registry/secrets/default/mysecret          # raw value (protobuf)
etcdctl get /registry/secrets/default/mysecret | hexdump -C | head
etcdctl get / --prefix --keys-only | wc -l               # how many objects the cluster holds

# --- snapshot --------------------------------------------------------
etcdctl snapshot save /opt/snapshot.db
etcdctl snapshot status /opt/snapshot.db --write-out=table   # etcdutl snapshot status on 3.5+

# --- the dangerous ones, for completeness ----------------------------
etcdctl put /some/key value
etcdctl del /some/key
etcdctl compact <revision> ; etcdctl defrag
```

:::warning
`put` and `del` on `/registry/...` keys bypass the API server - no validation,
no admission, no RBAC, no audit log. There is no legitimate reason to do it on
a Kubernetes cluster. Know the verbs exist; do not use them on cluster data.
:::

## Reading a Secret straight from etcd

This is the demonstration that makes "Secrets are only base64" land:

```bash
kubectl create secret generic demo --from-literal=password=hunter2
etcdctl get /registry/secrets/default/demo | hexdump -C | grep -A1 hunter
```

The password is right there, in the clear, on the disk of every control plane
node. The fix - encryption at rest - is a lesson of its own in the
application-lifecycle phase; for now, the takeaway is that **etcd's disk and
its snapshots are as sensitive as every Secret combined**.

## snapshot save vs snapshot restore

From etcd 3.5 the two halves of backup live in different binaries:

| Action | Tool | Needs a running etcd? |
|---|---|---|
| take a snapshot | `etcdctl snapshot save` | yes - it asks a live member |
| inspect a snapshot | `etcdutl snapshot status` | no |
| restore a snapshot | `etcdutl snapshot restore` | no - it writes a new data directory |

`etcdctl snapshot restore` still works in 3.5 with a deprecation warning, and
the exam accepts either. Use `etcdutl` for restore so the habit is the modern
one.

```bash
etcdutl snapshot restore /opt/snapshot.db --data-dir /var/lib/etcd-from-backup
```

What happens next - editing the static Pod manifest so etcd starts from the
new directory - is the backup-and-restore lesson in the cluster-maintenance
phase.

:::exam-tip
A snapshot **save** needs the endpoint and the three TLS flags (it talks to
the server). A **restore** does not - it only reads a file and writes a
directory. Candidates lose minutes adding certificate flags to a restore that
never needed them.
:::

## Check yourself

1. Why does every tutorial start with `ETCDCTL_API=3`, and when can you drop
   it?
2. Which of `snapshot save` and `snapshot restore` needs the `--cacert`,
   `--cert` and `--key` flags, and why?
3. What does reading a Secret with `etcdctl get` prove about how Kubernetes
   stores Secrets by default?
