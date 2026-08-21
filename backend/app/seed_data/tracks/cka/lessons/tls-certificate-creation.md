## Making the three kinds by hand

kubeadm does all of this for you. Doing it once by hand is how the flags in
the previous lesson stop being magic, and it is the same openssl you use in
the exam to build a user's credentials.

### 1. A CA

```bash
openssl genrsa -out ca.key 2048
openssl req -new -key ca.key -subj "/CN=KUBERNETES-CA" -out ca.csr
openssl x509 -req -in ca.csr -signkey ca.key -CAcreateserial -days 3650 -out ca.crt
```

`-signkey ca.key` signs the request with its own key: a self-signed root.
`ca.crt` is what every component will be told to trust; `ca.key` is what
signs everything else and must never leave the control plane.

### 2. A client certificate - the admin

```bash
openssl genrsa -out admin.key 2048
openssl req -new -key admin.key -subj "/CN=kube-admin/O=system:masters" -out admin.csr
openssl x509 -req -in admin.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 365 -out admin.crt
```

`CN` becomes the username, `O` the group. `system:masters` makes this an
all-powerful admin; a real user would get `O=developers` and an RBAC binding.

Use it:

```bash
curl https://<apiserver>:6443/api/v1/pods --cacert ca.crt --cert admin.crt --key admin.key
# or put it in a kubeconfig:
kubectl config set-credentials kube-admin --client-certificate=admin.crt --client-key=admin.key --embed-certs=true
```

The same recipe, with different subjects, makes the scheduler's
(`CN=system:kube-scheduler`), controller manager's
(`CN=system:kube-controller-manager`) and each kubelet's
(`CN=system:node:node01`, `O=system:nodes`) client certificates.

### 3. A server certificate - the API server

A server certificate has to list **every name and address** clients will use
to reach it, or the client's name check fails. For the API server that is a
lot:

```bash
cat > apiserver.cnf <<EOF
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name
[req_distinguished_name]
[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names
[alt_names]
DNS.1 = kubernetes
DNS.2 = kubernetes.default
DNS.3 = kubernetes.default.svc
DNS.4 = kubernetes.default.svc.cluster.local
DNS.5 = controlplane
IP.1 = 10.96.0.1            # the kubernetes Service ClusterIP
IP.2 = 192.168.1.10         # the node's IP
IP.3 = 127.0.0.1
EOF

openssl genrsa -out apiserver.key 2048
openssl req -new -key apiserver.key -subj "/CN=kube-apiserver" -config apiserver.cnf -out apiserver.csr
openssl x509 -req -in apiserver.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -days 365 -extensions v3_req -extfile apiserver.cnf -out apiserver.crt
```

The `subjectAltName` list is the part kubeadm gets right and humans get
wrong. `kubeadm init --apiserver-cert-extra-sans=lb.example.com` is how you
add a load balancer name at install; after the fact it is "regenerate the
apiserver cert" - `kubeadm init phase certs apiserver --apiserver-cert-extra-sans=...`
after moving the old one aside.

:::warning
Connecting to the API server by an IP or name that is **not** in its SANs
fails with `x509: certificate is valid for kubernetes, ..., not lb.example.com`.
That error names the SANs it *does* have - read it; it tells you exactly
what to add.
:::

### 4. Where they go

| File | Goes to |
|---|---|
| `ca.crt` | every kubeconfig (`certificate-authority-data`), API server `--client-ca-file`, kubelet `clientCAFile` |
| `ca.key` | the API server node only; controller manager `--cluster-signing-key-file` so it can sign CSRs |
| `apiserver.crt/.key` | API server `--tls-cert-file` / `--tls-private-key-file` |
| `admin.crt/.key` | the admin's kubeconfig |

## Reading what you made

```bash
openssl x509 -in apiserver.crt -text -noout | grep -E "Subject:|Issuer:|Not After|DNS:|IP Address"
```

Subject is who it is, Issuer is who signed it, Not After is when it stops
working, and the SAN line is every name it is valid for. The next lesson
makes a habit of this.

:::exam-tip
For a user in the exam you do **not** run `openssl x509 -CA ca.key` yourself
- you do not have `ca.key` in a sane cluster. You generate the key and CSR
with openssl, and hand the CSR to the **Certificates API** to sign (two
lessons on). The openssl half is steps 2's first two commands.
:::

## Check yourself

1. Which two openssl commands produce a user's private key and CSR, and which
   subject fields set the username and group?
2. Why does the API server's certificate need a SAN list, and what happens if
   a name is missing?
3. Which file must never be copied off the control plane, and which file goes
   into every kubeconfig?
