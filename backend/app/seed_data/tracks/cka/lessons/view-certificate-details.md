## One command to read any certificate

```bash
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout
```

```
Certificate:
    Data:
        Serial Number: ...
        Issuer: CN = kubernetes                        <- who signed it: the cluster CA
        Validity
            Not Before: Aug 20 10:00:00 2026 GMT
            Not After : Aug 20 10:00:00 2027 GMT       <- expiry
        Subject: CN = kube-apiserver                   <- who it is
        X509v3 extensions:
            X509v3 Subject Alternative Name:
                DNS:controlplane, DNS:kubernetes, DNS:kubernetes.default, DNS:kubernetes.default.svc,
                DNS:kubernetes.default.svc.cluster.local, IP Address:10.96.0.1, IP Address:192.168.1.10
```

Four lines answer every certificate question you will be asked:

```bash
openssl x509 -in cert.crt -noout -subject      # who
openssl x509 -in cert.crt -noout -issuer       # signed by whom
openssl x509 -in cert.crt -noout -dates        # valid from / to
openssl x509 -in cert.crt -noout -ext subjectAltName   # every name and IP it is valid for
```

## Auditing a whole cluster

When you inherit a cluster - or when the exam says "find out what is wrong
with the certificates" - walk the set with a table in mind:

| Certificate | Path | Expect CN | Expect O / SANs | Signed by |
|---|---|---|---|---|
| API server | `pki/apiserver.crt` | `kube-apiserver` | all the cluster names + IPs | `kubernetes` (cluster CA) |
| API server → kubelet | `pki/apiserver-kubelet-client.crt` | `kube-apiserver-kubelet-client` | `O=kubeadm:cluster-admins` | cluster CA |
| API server → etcd | `pki/apiserver-etcd-client.crt` | `kube-apiserver-etcd-client` | - | **etcd CA** |
| etcd server | `pki/etcd/server.crt` | the node name | node name, IP, localhost | etcd CA |
| etcd peer | `pki/etcd/peer.crt` | the node name | node name, IP | etcd CA |
| admin | inside `admin.conf` | `kubernetes-admin` | `O=kubeadm:cluster-admins` | cluster CA |
| kubelet client | inside `kubelet.conf` | `system:node:<name>` | `O=system:nodes` | cluster CA |

```bash
# certificates embedded in kubeconfigs: decode then read
grep client-certificate-data /etc/kubernetes/admin.conf | awk '{print $2}' | base64 -d | openssl x509 -noout -subject -dates
```

:::tip
The documentation ships a **Certificate health check spreadsheet** - a
table with exactly these columns - for working through a cluster
methodically. You do not need the file; you need the habit: for each cert,
write down subject, issuer, SANs, expiry, and the flag that references it,
and the inconsistency will stand out.
:::

## kubeadm does the walk for you

```bash
kubeadm certs check-expiration
```

```
CERTIFICATE                EXPIRES                  RESIDUAL TIME   CERTIFICATE AUTHORITY   EXTERNALLY MANAGED
admin.conf                 Aug 20, 2027 10:00 UTC   364d            ca                      no
apiserver                  Aug 20, 2027 10:00 UTC   364d            ca                      no
apiserver-etcd-client      Aug 20, 2027 10:00 UTC   364d            etcd-ca                 no
apiserver-kubelet-client   Aug 20, 2027 10:00 UTC   364d            ca                      no
...
CERTIFICATE AUTHORITY   EXPIRES                  RESIDUAL TIME
ca                      Aug 18, 2036 10:00 UTC   9y
etcd-ca                 Aug 18, 2036 10:00 UTC   9y
```

One screen: every certificate kubeadm knows about, which CA signed it, and
how long it has left. Run this first on any cluster that behaves strangely
after a long quiet period.

## Finding the problem when kubectl is dead

If the API server will not start, kubectl cannot tell you why. On the
control plane node:

```bash
crictl ps -a | grep kube-apiserver               # is it crash-looping?
crictl logs <container-id> 2>&1 | tail -20
# ... open /etc/kubernetes/pki/etcd/ca.crt: no such file or directory
# ... x509: certificate has expired or is not yet valid
# ... tls: failed to find any PEM data in certificate input
journalctl -u kubelet | grep -i cert              # the kubelet's side of the same story
```

Each of those lines points at one file: a wrong path (fix the flag in the
manifest), an expired cert (`kubeadm certs renew`), or a file that is not
actually a certificate (someone overwrote it - restore from backup or
regenerate with `kubeadm init phase certs <name>`).

:::exam-tip
A fast triage order for "certificate task": `kubeadm certs check-expiration`
for expiry → `grep -- --.*file /etc/kubernetes/manifests/kube-apiserver.yaml`
to list every path the API server uses and `ls -l` each one → `openssl x509
-noout -subject -issuer -dates` on the suspect. Three commands cover nearly
every variant.
:::

## Check yourself

1. Give the openssl one-liner that prints a certificate's subject, issuer and
   dates.
2. Which CA should have signed `apiserver-etcd-client.crt`, and how do you
   check?
3. The API server is down. Which two commands on the node show you a
   certificate error message, and what are the three kinds of error you
   expect to see?
