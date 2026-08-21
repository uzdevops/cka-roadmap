## Deployments GitLab can see

A deploy job is just a job - unless you tell GitLab *what* it deployed
*where*. `environment:` does that, and in return GitLab tracks every
deployment: which commit is live where, who deployed it, when, with a
link to the running thing and a one-click **re-deploy** of any earlier
version.

```yaml
deploy-dev:
  stage: deploy
  image: alpine:3.20
  script:
    - ./deploy.sh dev "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
  environment:
    name: dev
    url: https://dev.xyz.example.com
    deployment_tier: development      # production | staging | testing | development | other
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

*Operate → Environments* lists `dev` with its latest deployment, the
**Open** button (the `url:`), and the history. Every later deploy job in
this track carries an `environment:` block; a deploy without one is
invisible to the platform.

## Inside the job

`environment:` sets `CI_ENVIRONMENT_NAME`, `CI_ENVIRONMENT_SLUG`,
`CI_ENVIRONMENT_URL` and `CI_ENVIRONMENT_TIER` - so one deploy script can
serve every environment:

```bash
#!/usr/bin/env sh
# deploy.sh <env> <image>
set -eu
env="$1"; image="$2"
echo "deploying $image to $env ($CI_ENVIRONMENT_URL)"
```

## Environment-scoped variables

Week 3's variables have an **environment scope**. Define `DEPLOY_HOST`
three times - scope `dev`, `staging`, `production` - and every deploy job
reads the right one through the same `$DEPLOY_HOST`. Wildcards work:
`review/*` matches every review app (next lessons).

## Tiers, and why they matter

`deployment_tier` is how GitLab tells a toy environment from the one that
pages you: production environments get protection rules (lesson
"Staging and production"), dashboards group by tier, and `environment:
name: production` is inferred as tier production automatically. Name
environments plainly - `dev`, `staging`, `production` - and set the tier
when the name is not one of those.

## A deploy job's shape, complete

```yaml
.deploy:
  stage: deploy
  image: alpine:3.20
  before_script:
    - apk add --no-cache openssh-client curl
  script:
    - ./deploy.sh "$CI_ENVIRONMENT_NAME" "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
    - curl -fsS "$CI_ENVIRONMENT_URL/healthz"      # the deploy is not done until it answers
  resource_group: $CI_ENVIRONMENT_NAME              # one deploy per environment at a time

deploy-dev:
  extends: .deploy
  environment: { name: dev, url: https://dev.xyz.example.com }
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

The health check line is the difference between "the script exited 0" and
"the service is up". Make it part of every deploy.

## Self-check

- What do you gain by adding `environment:` to a deploy job?
- A variable must have different values in staging and production, with
  one name. Which mechanism?
- Why does the deploy job `curl` the health endpoint at the end?
