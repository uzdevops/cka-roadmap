## Signing through the cluster, not on it

Handing people certificates signed with `ca.key` on the control plane does
not scale, and nobody should be logging into the control plane to run
openssl with the CA key. The **Certificates API** turns signing into a
Kubernetes workflow: a user submits a CSR object, an administrator approves
it with kubectl, and the controller manager - which holds the CA key - signs
it and writes the certificate back into the object.

```
user: openssl key + CSR ──▶ CertificateSigningRequest object ──▶ admin approves ──▶ controller-manager signs ──▶ .status.certificate
```

## Step by step

**The user makes a key and a CSR** (their machine; the private key never
moves):

```bash
openssl genrsa -out akshay.key 2048
openssl req -new -key akshay.key -subj "/CN=akshay/O=developers" -out akshay.csr
```

**Wrap the CSR in an object:**

```bash
cat akshay.csr | base64 -w 0          # one line, for the request field
```

```yaml
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: akshay
spec:
  request: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURSBSRVFVRVNULS0tLS0K...   # the base64 CSR
  signerName: kubernetes.io/kube-apiserver-client                # "a client cert for talking to the API server"
  expirationSeconds: 86400                                        # optional, min 600
  usages:
    - client auth
```

```bash
kubectl apply -f akshay-csr.yaml
kubectl get csr
# NAME     AGE   SIGNERNAME                            REQUESTOR          REQUESTEDDURATION   CONDITION
# akshay   5s    kubernetes.io/kube-apiserver-client   kubernetes-admin   24h                 Pending
```

**An admin approves (or denies):**

```bash
kubectl certificate approve akshay
kubectl certificate deny agent-smith          # anything you do not recognise
kubectl get csr akshay -o yaml | grep -A3 conditions
```

**Extract the signed certificate:**

```bash
kubectl get csr akshay -o jsonpath='{.status.certificate}' | base64 -d > akshay.crt
openssl x509 -in akshay.crt -noout -subject -issuer -dates
# subject=O = developers, CN = akshay
# issuer=CN = kubernetes
```

**Put it to use:**

```bash
kubectl config set-credentials akshay --client-certificate=akshay.crt --client-key=akshay.key --embed-certs=true
kubectl config set-context akshay@kubernetes --cluster=kubernetes --user=akshay
kubectl --context=akshay@kubernetes get pods        # 403 until RBAC says otherwise - that is correct
```

## signerName

| Signer | Issues |
|---|---|
| `kubernetes.io/kube-apiserver-client` | client certs for users; **needs manual approval** |
| `kubernetes.io/kube-apiserver-client-kubelet` | kubelet client certs; auto-approved for bootstrapping nodes |
| `kubernetes.io/kubelet-serving` | kubelet **server** certs (port 10250); needs approval unless you enable the auto-approver |
| `kubernetes.io/legacy-unknown` | not auto-signed by the controller manager |

A CSR with the wrong signer sits `Pending` forever, or is approved but never
gets a certificate. If `approve` succeeds and `.status.certificate` stays
empty, check the signer - and check the controller manager is running with
`--cluster-signing-cert-file` and `--cluster-signing-key-file` pointing at the
CA, because it is the component that does the signing.

:::exam-tip
The three lines that cost marks: `request` must be base64 of the CSR **on
one line** (`base64 -w 0`); `usages` must include `client auth`; `signerName`
must be `kubernetes.io/kube-apiserver-client`. The documentation page
"Certificate Signing Requests" has a copy-paste manifest - use it.
:::

## Reading a suspicious CSR

```bash
kubectl get csr agent-smith -o jsonpath='{.spec.request}' | base64 -d | openssl req -noout -subject
# subject=CN = agent-x, O = system:masters
```

A request for `system:masters` from an unknown requestor is a request for
cluster-admin. Deny it. Reading the subject out of the request before
approving is the habit.

## Kubelets use this too

When a node joins, its kubelet submits a CSR for its own client certificate
(auto-approved via the bootstrap token), and optionally for its serving
certificate. `kubectl get csr` on a cluster with rotation shows a steady
trickle of `system:node:*` requests - that is normal. A node whose
`kubelet-serving` CSR sits Pending cannot serve `kubectl logs` over a trusted
cert; `kubectl certificate approve` it.

## Check yourself

1. Who signs an approved CSR, and which two files does that component need
   to do it?
2. A CSR is Approved but `.status.certificate` is empty. What do you check?
3. Before approving a CSR, what is the one thing you should read out of it,
   and how?
