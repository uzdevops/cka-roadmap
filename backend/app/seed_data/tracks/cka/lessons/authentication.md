## Users are not objects

Kubernetes has **no User object**. There is no `kubectl create user`. A
"user" is just a name that arrives attached to a request, proven by one of
the authenticators the API server is configured with. ServiceAccounts, by
contrast, *are* objects - they are the identities for Pods, and the next
lessons give them their own treatment.

```
request ──▶ [authenticator 1] ──▶ [authenticator 2] ──▶ ... ──▶ identity (user, groups) or 401
```

The API server tries each enabled authenticator in turn; the first to
succeed sets the identity. None succeed → `401 Unauthorized` (before any
authorization happens - a 401 is "who are you", a 403 is "you may not").

## The authenticators

| Method | How | Used for |
|---|---|---|
| **X.509 client certificates** | a cert signed by the cluster CA; CN = user, O = groups | admins, components (kubelet, scheduler...) - the kubeadm default |
| **ServiceAccount tokens** | JWTs issued by the API server for a ServiceAccount | Pods |
| **OIDC** | tokens from an identity provider (Keycloak, Google, Entra) | humans in real organisations |
| **Webhook token** | ask an external service whether a bearer token is valid | custom integrations |
| **Bootstrap tokens** | short-lived tokens for `kubeadm join` | joining nodes |
| Static token file / static password file | `--token-auth-file` | legacy; basic auth is **removed** |

The static files deserve a word because older material still shows them: a
CSV of `token,user,uid,"group1,group2"` passed to the API server with
`--token-auth-file`. It works, it is insecure (plain text, no rotation, needs
an API server restart to change), and it is not what you should build on.

## What a certificate says about you

```bash
openssl x509 -in /etc/kubernetes/pki/apiserver-kubelet-client.crt -noout -subject
# subject=O = kubeadm:cluster-admins, CN = kube-apiserver-kubelet-client
openssl x509 -in admin.crt -noout -subject
# subject=O = system:masters, CN = kubernetes-admin
```

- **CN** (Common Name) → the username.
- **O** (Organization, repeatable) → the groups.

`system:masters` is the group that every RBAC check lets through - the
admin kubeconfig kubeadm writes has it, which is why that kubeconfig is the
keys to the kingdom. The certificates lessons show how to issue one for a
real user with a sensible group.

## Where kubectl keeps its identity

```bash
kubectl config view --minify --raw | grep -A3 "user:"
#   client-certificate-data: LS0t...   (or client-certificate: /path)
#   client-key-data: LS0t...
# or
#   token: eyJhbGciOi...
```

A kubeconfig entry is the proof; the API server's `--client-ca-file` is what
checks certificate proofs. If they do not match you get
`x509: certificate signed by unknown authority` - a 401 in TLS clothing.

:::exam-tip
"Create a user" in a task means: generate a key and CSR for them, get it
signed by the cluster (CertificateSigningRequest, lesson after next), put the
cert in a kubeconfig, and grant RBAC. Four steps, no User object. If a task
hands you a token instead, `kubectl config set-credentials <name> --token=...`
is the kubeconfig half.
:::

## Groups that exist without you

| Group | Who |
|---|---|
| `system:authenticated` | every request that passed authentication |
| `system:unauthenticated` | anonymous requests (if allowed at all) |
| `system:masters` | cluster superusers - bypasses RBAC |
| `system:serviceaccounts` / `system:serviceaccounts:<ns>` | all ServiceAccounts / those in a namespace |
| `system:nodes` | kubelets (CN `system:node:<name>`) |

These matter for RBAC: binding a ClusterRole to `system:authenticated` grants
it to *everyone with a valid credential* - rarely what you meant.

## Check yourself

1. A request gets a 401. Did authorization run? What does 401 mean versus
   403?
2. In a client certificate, which fields become the username and the groups?
3. Why is binding a Role to `system:authenticated` dangerous?
