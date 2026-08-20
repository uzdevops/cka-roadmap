## Where etcd lives on a kubeadm cluster

kubeadm runs etcd as a **static Pod** on every control plane node. Its manifest
is `/etc/kubernetes/manifests/etcd.yaml`, the kubelet starts it without the
API server being involved, and its data lives on the node's disk:

```bash
kubectl get pods -n kube-system | grep etcd
# etcd-controlplane   1/1   Running

cat /etc/kubernetes/manifests/etcd.yaml
```

The flags in that manifest are the ones you keep coming back to:

```yaml
- command:
    - etcd
    - --advertise-client-urls=https://192.168.1.10:2379
    - --listen-client-urls=https://127.0.0.1:2379,https://192.168.1.10:2379
    - --listen-peer-urls=https://192.168.1.10:2380
    - --data-dir=/var/lib/etcd
    - --cert-file=/etc/kubernetes/pki/etcd/server.crt
    - --key-file=/etc/kubernetes/pki/etcd/server.key
    - --trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
    - --peer-cert-file=/etc/kubernetes/pki/etcd/peer.crt
    - --peer-key-file=/etc/kubernetes/pki/etcd/peer.key
    - --peer-trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
    - --initial-cluster=controlplane=https://192.168.1.10:2380
```

| Port | Who talks on it |
|---|---|
| **2379** | clients - the API server, and you with `etcdctl` |
| **2380** | peers - etcd members talking to each other |

And the data directory `/var/lib/etcd` is a `hostPath` volume, which is why a
restore is "restore to a new directory, point the manifest at it".

## How the API server reaches it

The API server is an etcd *client*. Its own static Pod manifest names the
endpoints and the client certificate it presents:

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
- --etcd-servers=https://127.0.0.1:2379
- --etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt
- --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt
- --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key
```

:::warning
A wrong path in any of those three `--etcd-*` flags makes the API server
crash-loop. Because kubectl is then dead, you diagnose it with `crictl logs`
on the control plane node. This exact fault is a favourite troubleshooting
task.
:::

## Talking to it yourself

Because etcd only accepts TLS client connections, every `etcdctl` command on a
kubeadm cluster needs the CA and a client certificate. The etcd server's own
cert/key pair is the easiest valid client identity on the box:

```bash
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health
```

Type that block often enough that your hands know it - it is the prefix of the
backup command you will write in the exam. Two ways to make it shorter:

```bash
# 1. exec into the etcd Pod - the certificates are mounted at the same paths
kubectl exec -n kube-system etcd-controlplane -- sh -c \
  "ETCDCTL_API=3 etcdctl --cacert=/etc/kubernetes/pki/etcd/ca.crt \
   --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key \
   endpoint health"

# 2. on the node, export them once per shell
export ETCDCTL_API=3 ETCDCTL_CACERT=/etc/kubernetes/pki/etcd/ca.crt \
       ETCDCTL_CERT=/etc/kubernetes/pki/etcd/server.crt ETCDCTL_KEY=/etc/kubernetes/pki/etcd/server.key
etcdctl --endpoints=https://127.0.0.1:2379 member list --write-out=table
```

:::exam-tip
Where do the paths come from if you forget them? `kubectl describe pod
etcd-controlplane -n kube-system` (or `cat /etc/kubernetes/manifests/etcd.yaml`)
shows every flag. Never guess a certificate path - read it off the manifest.
:::

## Stacked vs external etcd

kubeadm's default puts etcd **on** the control plane nodes ("stacked"): simple,
one node less to manage, and losing a control plane node loses an etcd member
with it. An **external** topology runs etcd on its own machines, so the control
plane and the data store fail independently. You will meet both in the HA
lesson; for now know that the static-Pod setup above is the stacked one.

## Check yourself

1. Which port does the API server use to reach etcd, and which do etcd members
   use to reach each other?
2. You need the etcd CA path for a backup command and cannot remember it. Where
   on the node is the authoritative answer?
3. The API server is crash-looping after someone edited its manifest. Which
   three flags would you check first, and what tool shows you the crash reason?
