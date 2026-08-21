## An environment per merge request

Reviewers read diffs badly and click buttons well. A **review app** deploys
the MR's branch to a throw-away environment with its own URL, puts a
**View app** button on the MR, and tears the environment down when the MR
is merged or closed. The whole mechanism is three keywords on a deploy job
and a matching stop job.

```yaml
deploy-review:
  stage: deploy
  extends: .deploy
  variables:
    IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
  script:
    - ./deploy-review.sh up "$CI_ENVIRONMENT_SLUG" "$IMAGE"
  environment:
    name: review/$CI_COMMIT_REF_SLUG            # dynamic: one environment per branch
    url: https://$CI_ENVIRONMENT_SLUG.review.xyz.example.com
    on_stop: stop-review                        # which job tears it down
    auto_stop_in: 2 days                        # even if nobody closes the MR
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

stop-review:
  stage: deploy
  extends: .deploy
  script:
    - ./deploy-review.sh down "$CI_ENVIRONMENT_SLUG"
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: manual                              # also triggered automatically on merge/close
  variables:
    GIT_STRATEGY: none                          # the branch may be gone by the time this runs
```

Notes that save an afternoon:

- `$CI_COMMIT_REF_SLUG` is the DNS-safe branch name; `$CI_ENVIRONMENT_SLUG`
  is the DNS-safe environment name (max 24 chars, unique) - use the latter
  in hostnames.
- The stop job needs `GIT_STRATEGY: none` because it may run after the
  branch was deleted; it must not need a checkout.
- `on_stop` jobs run automatically when the MR merges/closes or the
  environment's `auto_stop_in` expires.
- Build the image **before** deploy-review (the MR pipeline needs a
  `publish-image` job too - with `rules:` for `merge_request_event` and a
  tag that includes the ref slug so branches do not overwrite each other).

## What `deploy-review.sh` does

The script is whatever your platform needs: a `docker run -p` on a
shared review host with a wildcard DNS record and a reverse proxy routing
by hostname; a `helm upgrade --install review-$SLUG` into a `review`
namespace on Kubernetes; a `kubectl apply` of a templated manifest. The
pipeline does not care - it cares that `up` makes `$CI_ENVIRONMENT_URL`
answer and `down` removes it.

```bash
#!/usr/bin/env sh
set -eu
cmd="$1"; slug="$2"; image="${3:-}"
case "$cmd" in
  up)   ssh review-host "docker rm -f $slug 2>/dev/null; docker run -d --name $slug --network web \
          -l traefik.http.routers.$slug.rule=Host\(\`$slug.review.xyz.example.com\`\) $image" ;;
  down) ssh review-host "docker rm -f $slug || true" ;;
esac
```

## What you get

- MR widget: **View app** → the branch, running.
- *Operate → Environments* → folder `review/` with one row per open MR,
  each with Stop.
- Zero-cost cleanup: closed MRs clean themselves up; forgotten ones expire.

## Self-check

- Why is `GIT_STRATEGY: none` set on the stop job?
- What does `auto_stop_in` protect against?
- Which variable should form the review hostname, and why not the branch name directly?
