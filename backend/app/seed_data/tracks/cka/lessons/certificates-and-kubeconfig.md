## One file, three lists

Every `kubectl` command needs to know three things: which **cluster** to talk
to (address and CA), which **user** to be (certificate or token), and which
combination of the two - plus a default namespace - to use right now, the
**context**. A kubeconfig is those three lists and a pointer to the current
context.

```yaml
apiVersion: v1
kind: Config
clusters:
  - name: kubernetes
    cluster:
      server: https://192.168.1.10:6443
      certificate-authority-data: LS0tLS1CRUdJTi...      # the cluster CA, base64; or certificate-authority: /path/ca.crt
  - name: staging
    cluster:
      server: https://staging.example.com:6443
      certificate-authority: /home/me/staging-ca.crt
users:
  - name: kubernetes-admin
    user:
      client-certificate-data: LS0tLS1CRUdJTi...
      client-key-data: LS0tLS1CRUdJTi...
  - name: ci-bot
    user:
      token: eyJhbGciOiJSUzI1NiIs...
contexts:
  - name: kubernetes-admin@kubernetes
    context:
      cluster: kubernetes
      user: kubernetes-admin
      namespace: default
  - name: ci@staging
    context:
      cluster: staging
      user: ci-bot
current-context: kubernetes-admin@kubernetes
```

`-data` fields hold the file's contents base64-encoded (what `--embed-certs`
produces); the non-`-data` forms point at files. A context is a
(cluster, user, namespace) triple; `current-context` names one of them.

## Where kubectl looks

1. `--kubeconfig=/path` on the command line
2. `$KUBECONFIG` (colon-separated list; merged)
3. `~/.kube/config`

On a kubeadm control plane the admin file is `/etc/kubernetes/admin.conf`;
`kubeadm init` tells you to copy it to `~/.kube/config`.

## Managing it with kubectl config

```bash
kubectl config view                          # merged, secrets redacted
kubectl config view --minify                 # only the current context
kubectl config view --raw                    # include the certificate data
kubectl config get-contexts                  # * marks current
kubectl config current-context
kubectl config use-context ci@staging
kubectl config set-context --current --namespace=dev       # change the default namespace
kubectl config set-context dev@kubernetes --cluster=kubernetes --user=kubernetes-admin --namespace=dev
kubectl config set-cluster staging --server=https://staging.example.com:6443 --certificate-authority=ca.crt --embed-certs=true
kubectl config set-credentials akshay --client-certificate=akshay.crt --client-key=akshay.key --embed-certs=true
kubectl config delete-context old@cluster
kubectl --kubeconfig=/root/my-kube-config config use-context research   # act on a different file
```

:::exam-tip
Two kubeconfig tasks recur. **"Use context X in file F for the rest"**:
either `export KUBECONFIG=/path/F` then `use-context`, or
`kubectl config --kubeconfig=F use-context X` and pass `--kubeconfig=F` each
time; the cleanest is `cp F ~/.kube/config` if the task allows. **"The file
is broken, fix it"**: run one command with it and read the error - it names
the problem.
:::

## Reading the errors

```bash
kubectl --kubeconfig=my-kube-config get pods
```

| Error | Wrong field |
|---|---|
| `unable to read client-cert /etc/kubernetes/pki/users/dev-user/developer-user.crt ... no such file` | `client-certificate` path - typo or wrong file name |
| `x509: certificate signed by unknown authority` | `certificate-authority` is not the cluster's CA (or the cluster's cert changed) |
| `dial tcp ... connection refused` / `i/o timeout` | `server:` wrong address or port (`6443`) |
| `error: context "research" does not exist` | the context name, or it is in a different file |
| `The connection to the server localhost:8080 was refused` | no kubeconfig found at all - `KUBECONFIG` unset and no `~/.kube/config` |
| `error: You must be logged in to the server (Unauthorized)` | the user's cert/token is not accepted - expired, wrong CA signed it |

That last one is worth a second look: the file is *valid* (kubectl loaded
it, connected, presented the credential) and the **server** rejected the
identity. The fix is on the credential, not the file layout.

## Certificates inside the file

```bash
kubectl config view --raw -o jsonpath='{.users[?(@.name=="kubernetes-admin")].user.client-certificate-data}' | base64 -d | openssl x509 -noout -subject -dates
```

- that is how you check *who* a kubeconfig makes you and until when. Expired
client certificate = `Unauthorized`.

:::tip
`kubectl config view` hides `-data` fields as `DATA+OMITTED`; add `--raw` to
see them. And `--minify` is the one to use when a merged config is long and
you only care about the context in use.
:::

## Check yourself

1. Name the three lists in a kubeconfig and what a context ties together.
2. Which command switches the default namespace of the current context?
3. `kubectl --kubeconfig=F get pods` says `Unauthorized`. Is the file broken
   or the credential? What do you look at?
