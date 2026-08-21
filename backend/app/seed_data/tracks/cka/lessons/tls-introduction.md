## Why every arrow is encrypted

Kubernetes is a set of processes on different machines sending each other
instructions: "start this Pod", "here is a Secret", "delete that namespace".
Without TLS any machine on the network could read those instructions, or -
worse - send its own. So every connection between components is TLS, and
both sides prove who they are with certificates.

```
kubectl ──TLS──▶ kube-apiserver ──TLS──▶ etcd
                    ▲    │
        TLS ────────┘    └──TLS──▶ kubelet
   (scheduler, controller-manager, kubelets)
```

Two things TLS gives each arrow:

1. **Encryption** - nobody in the middle reads it.
2. **Identity** - each side knows who the other is, because the certificate
   it presents was signed by a CA both trust.

The second is the one that makes Kubernetes security work: the API server
does not just *encrypt* the kubelet's traffic, it *knows* that is node01's
kubelet, because node01's certificate says `CN=system:node:node01` and the
cluster CA signed it.

## What this phase builds up to

| Lesson | Answers |
|---|---|
| TLS basics | what a key, a certificate, a CA and a handshake are - from scratch |
| TLS in Kubernetes | which certificates exist in a cluster and who signed them |
| Certificate creation | how to make a CA, a server cert and a client cert with openssl |
| View certificate details | how to read any certificate and check a cluster's whole set |
| Certificates API | how to issue a certificate *through* the cluster, with approval |

The practical payoff comes in two exam tasks: **"a component cannot reach
another, fix it"** (almost always a certificate path or an expired cert) and
**"create credentials for user X"** (a CSR, approved and signed by the
cluster CA).

## Three words you will hear constantly

- **Server certificate** - what a *server* presents to prove it is who the
  client meant to reach. The API server has one (CN=kube-apiserver, with
  every name and IP it answers on); etcd has one; each kubelet has one.
- **Client certificate** - what a *client* presents to prove who it is. The
  admin kubeconfig holds one; the API server holds one for talking to etcd
  and another for talking to kubelets; every kubelet holds one for talking
  to the API server.
- **CA (certificate authority)** - the key pair that signs the others. A
  certificate is trusted if it was signed by a CA you trust. kubeadm makes a
  cluster CA (`ca.crt`/`ca.key`), an etcd CA, and a front-proxy CA.

That is most of what the next lesson will explain in full; if these three
definitions already make sense, you are ahead.

:::tip
Everything lives in `/etc/kubernetes/pki` on a kubeadm control plane. `ls`
that directory once now and look at the names - `apiserver.crt`,
`apiserver-kubelet-client.crt`, `etcd/server.crt`, `ca.crt` - and the next
lessons will be filling in a table you have already seen.
:::

## Check yourself

1. What two guarantees does TLS give a connection between two components?
2. What is the difference between a server certificate and a client
   certificate?
3. Where are a kubeadm cluster's certificates stored?
