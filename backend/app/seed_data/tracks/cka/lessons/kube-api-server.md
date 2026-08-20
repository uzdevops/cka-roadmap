## The only door

Every interaction with a Kubernetes cluster goes through the API server -
`kubectl`, the scheduler, the controller manager, every kubelet on every node,
the dashboard, your CI pipeline. Nothing else talks to etcd. That single fact
explains most of its design: it is the place where requests are authenticated,
authorised, admitted, validated and finally written.

```
kubectl ──▶ kube-apiserver ──▶ etcd
               ▲   ▲   ▲
    scheduler ─┘   │   └─ controller-manager
                kubelets
```

The request pipeline, in the order it runs:

1. **Authentication** - who are you? Certificates, bearer tokens, service
   account tokens, OIDC.
2. **Authorization** - may you do this? RBAC, Node, Webhook, ABAC.
3. **Admission** - should this object be allowed or changed? Mutating
   webhooks, then validating webhooks and built-in plugins.
4. **Schema validation** - is the object well-formed?
5. **Persist** - write to etcd, return the new resourceVersion.

Each of those stages is a whole lesson later in the track; this one is about
the component that hosts them.

## How it runs

On a kubeadm cluster the API server is a **static Pod** on each control plane
node, so it is configured by flags in a file, not by a ConfigMap:

```bash
cat /etc/kubernetes/manifests/kube-apiserver.yaml
kubectl get pods -n kube-system | grep apiserver
ps -ef | grep kube-apiserver | tr ' ' '\n' | grep -- --    # flags, one per line
```

On a cluster installed "the hard way" it is a systemd service instead, and the
same flags live in `/etc/systemd/system/kube-apiserver.service`. Same
component, different supervisor.

## The flags you will actually touch

```yaml
- kube-apiserver
- --advertise-address=192.168.1.10
- --secure-port=6443
- --etcd-servers=https://127.0.0.1:2379
- --etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt
- --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt
- --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key
- --client-ca-file=/etc/kubernetes/pki/ca.crt
- --tls-cert-file=/etc/kubernetes/pki/apiserver.crt
- --tls-private-key-file=/etc/kubernetes/pki/apiserver.key
- --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt
- --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key
- --service-cluster-ip-range=10.96.0.0/12
- --authorization-mode=Node,RBAC
- --enable-admission-plugins=NodeRestriction
- --encryption-provider-config=/etc/kubernetes/enc/enc.yaml   # only once you add it
```

| Flag group | Used in which lesson |
|---|---|
| `--etcd-*` | etcd in Kubernetes, backup and restore |
| `--client-ca-file`, `--tls-*` | TLS and certificates |
| `--kubelet-client-*` | what lets `kubectl logs` and `exec` work |
| `--service-cluster-ip-range` | Service networking |
| `--authorization-mode` | authorization |
| `--enable-admission-plugins` | admission controllers |
| `--encryption-provider-config` | encrypting Secrets at rest |

:::exam-tip
When you edit the static Pod manifest, the kubelet notices the file change and
recreates the Pod. There is no `systemctl restart`. Give it 20-30 seconds; if
`kubectl` does not come back, you made a typo - `crictl ps -a` and `crictl
logs` on the node will show you which one.
:::

## What breaks, and how it looks

| Symptom | Likely cause |
|---|---|
| `The connection to the server ... was refused` | API server not running: manifest error, or kubelet down on the control plane |
| `Unable to connect to the server: x509: certificate ...` | your kubeconfig's CA or client cert does not match |
| API server crash-loops, logs mention etcd | wrong `--etcd-*` path or etcd itself down |
| `kubectl logs` / `exec` fail with 401 or timeout, but `get` works | `--kubelet-client-*` certificates, or the kubelet port blocked |

```bash
# the debugging sequence on the control plane node
systemctl status kubelet
crictl ps -a | grep kube-apiserver
crictl logs <container-id> 2>&1 | tail -30
cat /etc/kubernetes/manifests/kube-apiserver.yaml   # look for the typo
```

:::tip
`kubectl get --raw /healthz`, `/livez` and `/readyz` are cheap ways to ask the
API server how it feels - `/readyz?verbose` lists every check it runs.
:::

## Check yourself

1. In which order do authentication, admission and authorization run, and why
   does the order matter?
2. You change a flag in `kube-apiserver.yaml`. What restarts the API server?
3. `kubectl get pods` works but `kubectl logs` returns an error. Which API
   server flags are involved, and which component is on the other end?
