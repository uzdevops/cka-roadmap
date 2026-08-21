## Every project has a registry

*Deploy → Container Registry*. The address is predictable -
`registry.gitlab.com/<group>/<project>` - and the pipeline already knows it
and how to log in:

| Variable | Value |
|---|---|
| `CI_REGISTRY` | `registry.gitlab.com` |
| `CI_REGISTRY_IMAGE` | `registry.gitlab.com/xyz-team/nodejs-app` |
| `CI_REGISTRY_USER` | `gitlab-ci-token` |
| `CI_REGISTRY_PASSWORD` | the job's `CI_JOB_TOKEN` - valid only while the job runs |

```yaml
publish-image:
  stage: publish
  image: docker:27
  services: [ docker:27-dind ]
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
    IMAGE_SHA: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
  before_script:
    - echo "$CI_REGISTRY_PASSWORD" | docker login -u "$CI_REGISTRY_USER" --password-stdin "$CI_REGISTRY"
  script:
    - docker build --pull -t "$IMAGE_SHA" .
    - docker push "$IMAGE_SHA"
    # a moving tag for humans, only where it means something
    - |
      if [ "$CI_COMMIT_BRANCH" = "$CI_DEFAULT_BRANCH" ]; then
        docker tag "$IMAGE_SHA" "$CI_REGISTRY_IMAGE:latest" && docker push "$CI_REGISTRY_IMAGE:latest"
      fi
    - |
      if [ -n "$CI_COMMIT_TAG" ]; then
        docker tag "$IMAGE_SHA" "$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG" && docker push "$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG"
      fi
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_COMMIT_TAG
```

No token was created, stored or rotated: `CI_JOB_TOKEN` is minted per job
and dies with it. That is the pattern for *everything* a job does against
GitLab itself - registry, package registry, API, downloading another
project's artifacts.

## Tagging strategy

| Tag | Moves? | Who uses it |
|---|---|---|
| `:<short-sha>` | never | deploy jobs - exact, traceable to a commit |
| `:<git tag>` (`v1.4.0`) | never | release notes, rollback to a version |
| `:latest` / `:main` | yes | humans trying things; **not** deploy jobs |

Deploy by immutable tag. A `:latest` that moved under a running
deployment is a debugging session nobody enjoys.

## Build once, promote many

Build and push in `publish`, then every deploy job **pulls the same
image** by SHA. Never rebuild per environment - a rebuild on the deploy
job is a different artifact from the one you tested.

```yaml
deploy-staging:
  stage: deploy
  image: alpine:3.20
  script:
    - ./deploy.sh staging "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
```

## Pulling from another project or from outside

- Another GitLab project's image: `CI_JOB_TOKEN` works if that project
  allows it (*Settings → CI/CD → Job token permissions*).
- Docker Hub or a private registry: a project variable with a token, used
  in `docker login`; or `DOCKER_AUTH_CONFIG` (a JSON `config.json`) so the
  **runner** can pull private `image:`/`services:` too.

## Housekeeping

*Settings → Packages and registries → Cleanup policies*: keep N tags per
image, delete tags older than X matching a regex, protect `v.*`. Without a
policy a busy project's registry grows by every SHA forever.

## Self-check

- Which variables log a job into the project registry, and how long is the password valid?
- Why deploy by SHA rather than `:latest`?
- What is wrong with rebuilding the image in the production deploy job?
