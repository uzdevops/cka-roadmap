## What there is to back up

A kubeadm cluster's state is in three places:

| What | Where | How to save it |
|---|---|---|
| every object (the cluster's memory) | etcd | `etcdctl snapshot save` |
| the control plane's own definition | `/etc/kubernetes/manifests`, `/etc/kubernetes/pki`, `/etc/kubernetes/*.conf` | copy the directory |
| your declared intent | the manifests in Git | Git |

Some teams skip etcd backups on the theory that "everything is in Git and
`kubectl apply` would rebuild it". It would not: Secrets created by hand,
certificates issued by the cluster, Leases, everything an operator wrote -
none of that is in Git. **Back up etcd.**

## Taking a snapshot

```bash
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /opt/snapshot-pre-boot.db

# Snapshot saved at /opt/snapshot-pre-boot.db
etcdutl snapshot status /opt/snapshot-pre-boot.db --write-out=table    # hash, revision, keys, size
```

Four flags, every time: the endpoint and the three TLS files. You read them
off `/etc/kubernetes/manifests/etcd.yaml` (`--listen-client-urls`,
`--trusted-ca-file`, `--cert-file`, `--key-file`). The snapshot is one file;
it is the whole cluster, Secrets included, so treat it like one.

:::exam-tip
The task gives you the paths - *use them*. It may also give you an endpoint
that is not 127.0.0.1 (an external etcd host). Do not type the flags from
memory if the task text has them; copy. The most common snapshot failure in
the exam is a certificate path typed from a different cluster's habit.
:::

## Restoring

A restore does not "load the snapshot into etcd". It **writes a brand-new data
directory** from the snapshot, and you then tell etcd to start from that
directory instead of the old one.

```bash
etcdutl snapshot restore /opt/snapshot-pre-boot.db --data-dir /var/lib/etcd-from-backup
# (etcdctl snapshot restore still works on 3.5 with a deprecation warning)
```

No endpoint, no certificates: it is a file-to-directory operation, etcd does
not need to be running, and it must not already own the target directory.

Then point the etcd static Pod at the new directory:

```yaml
# /etc/kubernetes/manifests/etcd.yaml
volumes:
  - hostPath:
      path: /var/lib/etcd-from-backup     # <- was /var/lib/etcd
      type: DirectoryOrCreate
    name: etcd-data
```

The container's `--data-dir=/var/lib/etcd` flag and its mount path can stay as
they are: the hostPath is what changed, so the same in-container path now maps
to the restored data. (Changing `--data-dir` too is also fine, as long as the
volumeMount matches.)

Save the file; the kubelet restarts etcd from the new directory; ~30 s later
the API server reconnects and the objects from the snapshot are back.

```bash
kubectl get pods -n kube-system | grep etcd       # Running
kubectl get deploy,svc -A                          # the things you lost are back
```

:::warning
Restoring replaces the cluster's state with the snapshot's. Anything created
after the snapshot is gone. Controllers will then reconcile reality to match:
Pods that exist on nodes but not in the restored etcd get cleaned up, Pods
that are in the snapshot but not on nodes get recreated. Restore to the
snapshot you mean.
:::

## External etcd

If etcd is not a static Pod but runs on its own host(s):

```bash
# find out: is there an etcd Pod?
kubectl get pods -n kube-system | grep etcd             # nothing -> external
ps -ef | grep etcd                                       # on the etcd host
cat /etc/systemd/system/etcd.service                     # flags and data dir live here
```

Same snapshot command (with that host's endpoint and certificates); for the
restore, change `--data-dir` in the systemd unit (and `chown etcd:etcd` the
new directory), then `systemctl daemon-reload && systemctl restart etcd`.

## The checklist

```
save:     endpoint + 3 certs + snapshot save <file>
restore:  snapshot restore <file> --data-dir <new dir>
          edit etcd.yaml hostPath -> <new dir>       (or the systemd unit for external etcd)
          wait, kubectl get pods -n kube-system, verify the objects
```

## Check yourself

1. Which of `snapshot save` and `snapshot restore` needs the TLS flags, and
   why?
2. After a restore, what single edit makes the cluster actually use the
   restored data, and what restarts etcd?
3. Why is "we have everything in Git" not a substitute for an etcd backup?
