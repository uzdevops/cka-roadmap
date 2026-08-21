## A ConfigMap for things you would not print

A Secret has the same shape as a ConfigMap - namespaced keys and values - and
is consumed the same three ways. The differences are in handling: values are
base64-encoded in the API, `kubectl describe` hides them, they can be
encrypted at rest, RBAC usually treats them separately, and the kubelet only
sends a Secret to nodes that run a Pod needing it.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  DB_User: cm9vdA==              # base64("root")
  DB_Password: cGFzc3dvcmQxMjM=  # base64("password123")
```

```yaml
stringData:                      # plain text in the file; the API stores it base64
  DB_Password: password123
```

`stringData` is write-only convenience: you write plain text, the API server
encodes it into `data`, and reading the object back shows only `data`.

## base64 is not encryption

```bash
echo -n 'password123' | base64        # cGFzc3dvcmQxMjM=
echo 'cGFzc3dvcmQxMjM=' | base64 -d   # password123
kubectl get secret db-secret -o jsonpath='{.data.DB_Password}' | base64 -d
```

Anyone who can `get` the Secret can read it. Anyone with the etcd disk can
read it too, because by default it sits there in the clear (the etcd lessons
showed that). What actually protects Secrets:

1. **RBAC** - do not grant `get`/`list` on secrets to roles that do not need it;
   `list` alone reveals every value.
2. **Encryption at rest** - an `EncryptionConfiguration` on the API server so
   etcd stores ciphertext. Next lesson.
3. **Not putting them in Git** - a Secret manifest with `data` in a repo is a
   leak. Sealed Secrets, SOPS or an external secrets operator fill that gap,
   outside the exam.

:::warning
`kubectl create secret ... --from-literal=password=x` leaves the password in
your shell history. In the exam it does not matter; in life, `--from-file`
or a `stringData` manifest you delete afterwards.
:::

## Creating

```bash
kubectl create secret generic db-secret --from-literal=DB_User=root --from-literal=DB_Password=password123
kubectl create secret generic tls-files --from-file=tls.crt --from-file=tls.key
kubectl create secret tls web-tls --cert=tls.crt --key=tls.key                      # type kubernetes.io/tls
kubectl create secret docker-registry regcred --docker-server=reg.io --docker-username=u --docker-password=p --docker-email=e@x.io
kubectl get secrets
kubectl describe secret db-secret        # keys and sizes, no values
```

| Type | For |
|---|---|
| `Opaque` | anything (the default) |
| `kubernetes.io/tls` | a certificate and key - Ingress TLS |
| `kubernetes.io/dockerconfigjson` | registry credentials - `imagePullSecrets` |
| `kubernetes.io/service-account-token` | legacy SA tokens |
| `kubernetes.io/basic-auth`, `ssh-auth` | conventions with required keys |

## Consuming - the same three shapes

```yaml
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-secret
        key: DB_Password
envFrom:
  - secretRef:
      name: db-secret
volumes:
  - name: creds
    secret:
      secretName: db-secret
      defaultMode: 0400
containers:
  - volumeMounts:
      - name: creds
        mountPath: /etc/creds
        readOnly: true
```

Mounted Secrets are **tmpfs** on the node - never written to disk - and
update in place like ConfigMaps (except with `subPath`). Env vars are read
once at start, and environment variables leak easily (child processes, crash
dumps, `kubectl describe`-style tooling); prefer the volume when you can.

```bash
kubectl exec app -- cat /etc/creds/DB_Password
kubectl exec app -- env | grep DB_
```

## Pulling from a private registry

```yaml
spec:
  imagePullSecrets:
    - name: regcred
  containers:
    - image: myregistry.io:5000/app:1.0
```

The `docker-registry` Secret plus `imagePullSecrets` on the Pod (or on the
ServiceAccount, so every Pod using it inherits it). `ErrImagePull` with
`unauthorized` in the event is the symptom you are fixing.

:::exam-tip
`kubectl describe secret` will not show you a value and `kubectl get secret -o
yaml` shows base64. The one-liner to read a value is
`kubectl get secret <name> -o jsonpath='{.data.<key>}' | base64 -d`. Keys with
dots need `{.data.tls\.crt}`.
:::

## Check yourself

1. What does base64 protect a Secret against? What protects it from someone
   with the etcd disk?
2. Write the command to read key `DB_Password` of Secret `db-secret` in plain
   text.
3. A Pod fails with `ErrImagePull ... unauthorized`. Which two objects fix it,
   and where does the reference go?
