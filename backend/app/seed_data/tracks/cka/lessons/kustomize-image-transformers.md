## Change an image without touching the manifest

The most common difference between environments is the image tag: `dev`
runs `main`, `prod` runs `2.1.0`. The `images` transformer changes image
references in every container and initContainer across all resources,
matching on the image **name**.

```yaml
# base/deployment.yaml
containers:
  - name: web
    image: nginx:1.25
```

```yaml
# overlays/prod/kustomization.yaml
resources: [../../base]
images:
  - name: nginx                 # matches `image: nginx:<anything>` - the name part, not the container name
    newTag: "1.27.1"
```

```bash
kubectl kustomize overlays/prod | grep image:
#   image: nginx:1.27.1
```

## The three fields

```yaml
images:
  - name: nginx
    newName: registry.example.com/mirror/nginx     # change the repository
    newTag: "1.27.1"                               # change the tag
  - name: myapp
    digest: sha256:4f3e2a...                       # pin by digest instead of tag
```

| Field | Effect on `image: nginx:1.25` |
|---|---|
| `newTag: "1.27.1"` | `nginx:1.27.1` |
| `newName: registry.example.com/nginx` | `registry.example.com/nginx:1.25` |
| both | `registry.example.com/nginx:1.27.1` |
| `digest: sha256:...` | `nginx@sha256:...` (tag dropped) |

`name` is the image name **as written in the manifests** (without tag). It
is easy to confuse with the container's `name:` field - they are unrelated.
`newTag` is a string; quote numeric-looking tags (`"1.27"`) or YAML reads a
number.

## Why it beats a patch for this

A patch would need the path to the container: `/spec/template/spec/containers/0/image`
- per Deployment, per container index. `images` finds every use of the image
name in every resource, including ones you add later. One line per image,
regardless of how many Deployments use it.

## With a registry mirror, or a different name entirely

```yaml
images:
  - name: docker.io/library/postgres
    newName: harbor.corp/cache/postgres
```

A `newName` with no `newTag` keeps the original tag - which is how a whole
overlay can be redirected to an internal mirror.

## In the pipeline

```bash
kustomize edit set image nginx=nginx:1.27.2                  # edits the kustomization.yaml in the current dir
kustomize edit set image myapp=registry.example.com/myapp:$GIT_SHA
git commit -am "deploy $GIT_SHA" && git push                 # GitOps picks it up
```

`kustomize edit set image` writes the `images` entry for you - the normal
way CI bumps a version without templating.

:::exam-tip
"Change the image of the Deployments in this overlay to X:Y" is an `images`
entry, not a patch. Confirm with `kubectl kustomize | grep image:`. If the
manifests reference the image with a registry prefix, the `name` must
include it exactly (`registry.k8s.io/nginx`, not `nginx`), or nothing
matches - and Kustomize does not warn about an `images` entry that matched
nothing.
:::

## Check yourself

1. In `images: [{name: nginx, newTag: "2"}]`, what does `name` match
   against - the container name or the image name?
2. Write the entry that moves `postgres:16` to `harbor.corp/postgres:16`.
3. Why is `images` better than a patch for changing a tag used by three
   Deployments?
