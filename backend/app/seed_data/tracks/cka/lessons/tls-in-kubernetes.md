## Every certificate in a kubeadm cluster

```bash
ls /etc/kubernetes/pki /etc/kubernetes/pki/etcd
```

```
/etc/kubernetes/pki
├── ca.crt  ca.key                          the cluster CA
├── apiserver.crt  apiserver.key            API server's SERVER cert
├── apiserver-kubelet-client.crt/.key       API server as CLIENT to kubelets
├── apiserver-etcd-client.crt/.key          API server as CLIENT to etcd
├── front-proxy-ca.crt/.key                 CA for the aggregation layer
├── front-proxy-client.crt/.key             API server as CLIENT to aggregated APIs (metrics-server)
├── sa.key  sa.pub                          signs ServiceAccount tokens (not a certificate)
└── etcd/
    ├── ca.crt  ca.key                      the etcd CA (separate on purpose)
    ├── server.crt/.key                     etcd's SERVER cert
    ├── peer.crt/.key                       etcd member-to-member
    └── healthcheck-client.crt/.key         etcd's own probe
```

Plus the client certificates that live **inside kubeconfigs** rather than as
files:

| kubeconfig | Identity (CN) | Group (O) | Used by |
|---|---|---|---|
| `/etc/kubernetes/admin.conf` | `kubernetes-admin` | `kubeadm:cluster-admins` | you |
| `/etc/kubernetes/controller-manager.conf` | `system:kube-controller-manager` | - | controller manager |
| `/etc/kubernetes/scheduler.conf` | `system:kube-scheduler` | - | scheduler |
| `/etc/kubernetes/kubelet.conf` | `system:node:<name>` | `system:nodes` | this node's kubelet |

And on each node, the kubelet's own **server** certificate for port 10250
(`/var/lib/kubelet/pki/kubelet.crt`, or a `kubelet-server-current.pem` if
rotation is on), which the API server checks when it calls the kubelet for
logs and exec.

## Server certs, client certs, and who checks what

```
kubectl  ──(client: admin.conf cert)──▶ apiserver (server: apiserver.crt; checks client against ca.crt)
apiserver ──(client: apiserver-etcd-client)──▶ etcd (server: etcd/server.crt; checks client against etcd/ca.crt)
apiserver ──(client: apiserver-kubelet-client)──▶ kubelet (server: kubelet.crt; checks client against ca.crt)
kubelet  ──(client: kubelet.conf cert)──▶ apiserver
scheduler/controller-manager ──(client: their .conf certs)──▶ apiserver
```

Two CAs: the **cluster CA** signs everything on the Kubernetes side; the
**etcd CA** signs everything on the etcd side. That is why the API server's
etcd client certificate is signed by the etcd CA (`--etcd-cafile` points at
`etcd/ca.crt`), and why a restore task that moves etcd around has to keep
those files together.

## Flags that name them

```yaml
# kube-apiserver.yaml
- --client-ca-file=/etc/kubernetes/pki/ca.crt                       # who may call me
- --tls-cert-file=/etc/kubernetes/pki/apiserver.crt                 # what I present
- --tls-private-key-file=/etc/kubernetes/pki/apiserver.key
- --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt
- --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key
- --etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt
- --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt
- --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key
- --service-account-key-file=/etc/kubernetes/pki/sa.pub
- --service-account-signing-key-file=/etc/kubernetes/pki/sa.key
```

```yaml
# etcd.yaml
- --cert-file=/etc/kubernetes/pki/etcd/server.crt
- --key-file=/etc/kubernetes/pki/etcd/server.key
- --trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
- --peer-cert-file=/etc/kubernetes/pki/etcd/peer.crt
- --peer-key-file=/etc/kubernetes/pki/etcd/peer.key
- --peer-trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
```

:::exam-tip
When the exam says "the API server is not coming up" and you find a
`--etcd-cafile` pointing at `/etc/kubernetes/pki/ca.crt` (the cluster CA)
instead of `.../etcd/ca.crt`, that is the bug: the API server presents its
etcd client cert, etcd checks it against its own CA - fine - but the API
server checks etcd's server cert against the *wrong* CA and refuses. The
lesson: match each `*-cafile` to the CA that signed the *other* side.
:::

## Expiry and renewal

kubeadm issues most certificates for **one year** (the CAs for ten).

```bash
kubeadm certs check-expiration
kubeadm certs renew all            # renews everything it manages; then restart the control plane Pods
```

`kubeadm upgrade apply` also renews them, so a cluster upgraded at least once
a year never hits the cliff. A cluster that is not: one morning every
component says `certificate has expired` and kubectl stops working - the
renew command above (run with the node's root access) is the fix.

## Check yourself

1. Which CA signs the API server's etcd client certificate, and which flag
   tells the API server which CA to trust for etcd's server certificate?
2. Where is the admin user's client certificate stored?
3. How do you list the expiry of every kubeadm-managed certificate, and what
   renews them?
