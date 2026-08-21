## Seeing the problem

```bash
kubectl create secret generic demo --from-literal=password=hunter2
ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/default/demo | hexdump -C | grep -A1 hunter
```

There it is, readable on the control plane's disk and in every etcd snapshot
you ever take. **Encryption at rest** makes the API server encrypt selected
resources before writing them to etcd and decrypt on read; etcd and its
backups then hold ciphertext.

## The EncryptionConfiguration

```yaml
# /etc/kubernetes/enc/enc.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
      - configmaps            # optional, if you want them too
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <base64 of 32 random bytes>
      - identity: {}          # fall back to plaintext for READING old data
```

```bash
head -c 32 /dev/urandom | base64        # the key
```

Rules of the file:

- `resources` lists what to encrypt; `providers` lists *how*, **in order**.
- The **first provider is used to write**. Every provider is tried, in order,
  to read - which is how old plaintext objects stay readable while new writes
  are encrypted.
- `identity` means "no encryption". With it first, nothing is encrypted. With
  it last, it is the fallback for reading pre-existing plaintext.

| Provider | Notes |
|---|---|
| `identity` | none |
| `aescbc` | the one the docs walk through; fine |
| `aesgcm` | faster; must rotate keys every ~200k writes |
| `secretbox` | XSalsa20/Poly1305, strong |
| `kms` | envelope encryption with an external KMS - the production answer |

## Wiring it into the API server

The API server reads the file through a flag, so it must be **mounted** into
the static Pod:

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
    command:
      - kube-apiserver
      - --encryption-provider-config=/etc/kubernetes/enc/enc.yaml
    volumeMounts:
      - name: enc
        mountPath: /etc/kubernetes/enc
        readOnly: true
volumes:
  - name: enc
    hostPath:
      path: /etc/kubernetes/enc
      type: DirectoryOrCreate
```

Save; the kubelet restarts the API server; wait; `kubectl get --raw /healthz`.

:::warning
The encryption key is now the only thing standing between an etcd snapshot
and every Secret. **Back the key up separately** from the snapshots, and lock
down `/etc/kubernetes/enc` (`chmod 600`). Lose the key and every encrypted
object is gone for good.
:::

## Proving it, and encrypting what was already there

```bash
kubectl create secret generic demo2 --from-literal=password=hunter3
etcdctl ... get /registry/secrets/default/demo2 | hexdump -C | head -3
# 00000000  2f 72 65 67 69 73 74 72 79 2f 73 65 63 72 65 74  |/registry/secret|
# 00000010  ... 6b 38 73 3a 65 6e 63 3a 61 65 73 63 62 63 3a  |...k8s:enc:aescbc:|
```

`k8s:enc:aescbc:v1:key1:` followed by noise - encrypted. Objects written
*before* the change are still plaintext until they are rewritten:

```bash
kubectl get secrets -A -o json | kubectl replace -f -      # rewrite every Secret -> re-encrypted
```

Key rotation is the same idea: add the new key **first** in the list, keep
the old one second, restart, run the replace above, then remove the old key.

:::exam-tip
The documentation page "Encrypting Confidential Data at Rest" has the whole
sequence - config file, flag, volume mount, the `replace` one-liner. It is
one of the pages worth knowing the location of, because the task is almost
entirely "do the steps without a typo". The two typos that cost: forgetting
the volume mount (API server crash-loops, `no such file`), and putting
`identity` first (nothing gets encrypted, and the check fails).
:::

## Check yourself

1. In a `providers` list, which entry is used for writing and which for
   reading?
2. You configure encryption and check an *old* Secret in etcd - still
   plaintext. Why, and what command fixes it?
3. What must you back up, separately from etcd snapshots, once encryption at
   rest is on - and why separately?
