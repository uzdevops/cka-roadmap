## The problem: sending a secret to someone you have never met

You type a password into a website. It travels through a dozen networks you
do not control. Two things have to be true for that to be safe: nobody on
the way can read it, and the site at the other end is really the bank and
not someone pretending. TLS solves both, and the pieces it uses are exactly
the pieces Kubernetes uses between its components.

## Symmetric encryption

One key, used to both lock and unlock. Fast, and fine - **if** both sides
already have the key. The catch: how do you get the key to the other side
without sending it in the clear, where an eavesdropper picks it up?

## Asymmetric encryption: a pair of keys

A key pair: a **private key** you keep, and a **public key** you hand out.
Anything encrypted with the public key can only be decrypted with the
private key.

```bash
openssl genrsa -out my.key 2048            # private key
openssl rsa -in my.key -pubout > my.pem    # public key derived from it
```

Now the secret-exchange problem is solved: the server publishes its public
key; the client makes up a symmetric key, encrypts it with the server's
public key, sends it; only the server can decrypt it; both now share a
symmetric key for the rest of the conversation. (This is the shape; modern
TLS uses a key-agreement variant, but the roles are the same.)

The same pair works the other way round for **signing**: something
encrypted with the private key can be decrypted by anyone with the public
key - proving it came from the private key's owner. That is what SSH keys
do, and it is what a certificate signature is.

## The gap: whose public key is it?

An attacker can publish *their* public key and claim to be the bank. The
client needs to know the public key really belongs to `bank.com`. A
**certificate** is a public key plus a name plus a **signature from someone
the client already trusts** saying "this key belongs to this name".

```
certificate = { public key, subject (name), valid dates, issuer } signed by a CA's private key
```

The "someone the client already trusts" is a **Certificate Authority**. Its
own certificate (its public key) is pre-installed in the client - your
browser ships with hundreds; a Kubernetes component is given the cluster CA's
`ca.crt` in its kubeconfig. The client checks the signature on the server's
certificate with the CA's public key, checks the name matches what it meant
to reach, checks the dates, and only then trusts the public key inside.

```bash
openssl req -new -key my.key -subj "/CN=my-server" -out my.csr     # CSR: "please sign this public key for this name"
openssl x509 -req -in my.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out my.crt -days 365
```

A CA that signs its own certificate is a **root CA**; kubeadm's cluster CA is
one. Real-world CAs sign intermediates that sign servers - a chain - but the
check is the same at each link.

## The handshake, in order

1. Client connects; says which TLS versions and ciphers it supports.
2. Server sends its **certificate**.
3. Client verifies the certificate: signed by a trusted CA, name matches,
   not expired.
4. Key exchange using the server's public key; both sides derive the
   **symmetric session key**.
5. Everything after this is symmetrically encrypted.

Optionally, at step 2-3 the server asks the client for a certificate too and
verifies it the same way - **mutual TLS**. Kubernetes does this everywhere:
the API server checks the kubelet's client cert, the kubelet checks the API
server's server cert.

## File names you will see

| Extension / name | Usually |
|---|---|
| `.key`, `-key.pem` | a private key - never share, never commit |
| `.crt`, `.pem`, `.cer` | a certificate (public) |
| `.csr` | a certificate signing request |
| `ca.crt` | a CA's certificate - what clients trust |
| `ca.key` | the CA's private key - the most sensitive file on the control plane |

:::exam-tip
You will not be asked to explain TLS. You will be asked to generate a key
and CSR (`openssl genrsa`, `openssl req -new`), to read a certificate
(`openssl x509 -text -noout`), and to recognise `x509: certificate signed by
unknown authority` (wrong CA in a kubeconfig or component flag) and `certificate
has expired`. The three openssl commands on this page are the whole toolbox.
:::

## Check yourself

1. What problem does asymmetric encryption solve that symmetric cannot?
2. What three things does a certificate bind together, and who vouches for
   the binding?
3. In mutual TLS between the API server and a kubelet, which certificates
   are checked, and by whom?
