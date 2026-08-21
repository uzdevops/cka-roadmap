## What an image name really says

```
image: nginx
```

is short for

```
image: docker.io/library/nginx:latest
       └──┬───┘ └──┬──┘ └─┬─┘ └──┬──┘
       registry  user/org image   tag
```

| Part | Default when omitted |
|---|---|
| registry | `docker.io` (Docker Hub) |
| user / organisation | `library` (Docker's official images) |
| tag | `latest` |

So `nginx` pulls `docker.io/library/nginx:latest`; `kodekloud/webapp-color`
pulls `docker.io/kodekloud/webapp-color:latest`; `registry.k8s.io/kube-apiserver:v1.30.2`
is fully qualified. A private registry is just a different first segment:
`myregistry.io:5000/apps/web:1.4`.

:::warning
`latest` is not "newest" - it is a tag like any other, whatever was pushed
under that name. Production manifests pin a tag (or a digest:
`nginx@sha256:abc...`), and `imagePullPolicy` decides whether the kubelet
re-pulls: `Always` (default for `latest`), `IfNotPresent` (default for other
tags), `Never`.
:::

## Pulling from a private registry

The node's container runtime pulls the image, so it needs credentials. In
Kubernetes you hand them over as a Secret of type
`kubernetes.io/dockerconfigjson` and reference it from the Pod:

```bash
kubectl create secret docker-registry private-reg-cred \
  --docker-server=myregistry.io:5000 \
  --docker-username=dock_user \
  --docker-password=dock_password \
  --docker-email=dock_user@myregistry.io
```

```yaml
spec:
  imagePullSecrets:
    - name: private-reg-cred
  containers:
    - name: web
      image: myregistry.io:5000/apps/web:1.4
```

```bash
kubectl set image deployment/web web=myregistry.io:5000/apps/web:1.4
kubectl patch deployment web -p '{"spec":{"template":{"spec":{"imagePullSecrets":[{"name":"private-reg-cred"}]}}}}'
# or kubectl edit deployment web and add the block under template.spec
```

Or attach it to the ServiceAccount, and every Pod using that account inherits
it:

```bash
kubectl patch serviceaccount default -p '{"imagePullSecrets":[{"name":"private-reg-cred"}]}'
```

The Secret is just `~/.docker/config.json` in a different wrapper:

```bash
kubectl get secret private-reg-cred -o jsonpath='{.data.\.dockerconfigjson}' | base64 -d
# {"auths":{"myregistry.io:5000":{"username":"dock_user","password":"dock_password","auth":"..."}}}
```

## Reading pull failures

```bash
kubectl get pods
# web-7c6f   0/1   ErrImagePull      -> then ImagePullBackOff
kubectl describe pod web-7c6f | tail -8
```

| Event says | Cause |
|---|---|
| `... not found` / `manifest unknown` | wrong name or tag |
| `unauthorized` / `authentication required` | private image, no or wrong `imagePullSecrets` |
| `dial tcp ... i/o timeout` / `no such host` | registry unreachable from the node, or a typo in the registry name |
| `x509: certificate signed by unknown authority` | registry with a private CA; the **node's** runtime needs to trust it (containerd `hosts.toml`), not Kubernetes |

:::exam-tip
A task that says "the image is in a private registry at X with these
credentials" is exactly two steps: `kubectl create secret docker-registry`
and `imagePullSecrets` on the Pod template. Watch the `--docker-server`
value - it must match the registry in the image name, port included.
:::

## Beyond pulling: trusting what you run

The CKA stops at pulling; the CKS goes further, but the shape is worth a
paragraph:

- **Pin digests** so an image cannot change under a tag.
- **Restrict registries** with an admission policy (a validating webhook or
  `ValidatingAdmissionPolicy` that rejects images not from `myregistry.io`).
- **Scan images** in CI; **sign** them and verify signatures at admission.
- Run containers as non-root with a **securityContext** - the next lessons.

## Check yourself

1. Expand `kodekloud/webapp-color` to its fully qualified form.
2. Which Secret type holds registry credentials, and where in a Pod spec is
   it referenced?
3. `ErrImagePull` with `unauthorized` - which two things do you check?
