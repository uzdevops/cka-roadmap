## Turning knobs without forking the pipeline

Almost every Auto DevOps behaviour is a **CI/CD variable**. Set them at
project or group level and the generated pipeline adapts - no YAML.

| Variable | Effect |
|---|---|
| `STAGING_ENABLED=1` | add a `staging` environment; `production` becomes manual |
| `CANARY_ENABLED=1` | add a manual canary deploy before production |
| `INCREMENTAL_ROLLOUT_MODE=manual` / `timed` | production rolls out 10% → 25% → 50% → 100% with manual steps or 5-minute timers |
| `REPLICAS`, `PRODUCTION_REPLICAS`, `<ENV>_REPLICAS` | pod counts per environment |
| `ADDITIONAL_HOSTS`, `<ENV>_ADDITIONAL_HOSTS` | extra ingress hostnames |
| `AUTO_DEVOPS_DEPLOY_DEBUG=1` | print Helm values and commands |
| `TEST_DISABLED=1`, `CODE_QUALITY_DISABLED=1`, `SAST_DISABLED=1`, `DAST_DISABLED=1`, `CONTAINER_SCANNING_DISABLED=1`, `REVIEW_DISABLED=1`, `PERFORMANCE_DISABLED=1` | drop a job |
| `AUTO_DEVOPS_BUILD_IMAGE_EXTRA_ARGS` | `--build-arg`s for the build |
| `HELM_UPGRADE_EXTRA_ARGS`, `HELM_UPGRADE_VALUES_FILE` | pass values to the chart |
| `K8S_SECRET_<NAME>` | becomes an environment variable `<NAME>` in the deployed pods (a Kubernetes Secret) - the way to give the app its `DATABASE_URL` |

```text
# project variables
STAGING_ENABLED=1
INCREMENTAL_ROLLOUT_MODE=manual
K8S_SECRET_DATABASE_URL=postgres://…        (protected, scoped: production)
PRODUCTION_REPLICAS=3
```

## Include the templates and override jobs

When a variable is not enough, **keep Auto DevOps but write a
`.gitlab-ci.yml`** that includes it and overrides what you need:

```yaml
include:
  - template: Auto-DevOps.gitlab-ci.yml

variables:
  STAGING_ENABLED: "1"

# override one generated job: same name, your changes merge in
test:
  image: node:20-alpine
  script:
    - npm ci
    - npm test
  artifacts:
    reports: { junit: reports/junit.xml }

# add a job the template does not have
notify:
  stage: production
  needs: [production]
  script: ./notify-slack.sh "deployed $CI_COMMIT_SHORT_SHA"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

A job with the same name as a template job **replaces** the keys you set
and keeps the rest - the way `extends` merges. To remove a generated job
entirely, set its `*_DISABLED` variable or give it `rules: [ { when:
never } ]`.

You can also include **only parts** of Auto DevOps - `Jobs/Build.gitlab-ci.yml`,
`Jobs/Deploy.gitlab-ci.yml`, `Jobs/Test.gitlab-ci.yml` - and write the rest
yourself, which is often the sweet spot: their build and deploy, your
tests.

## Your own chart

`AUTO_DEVOPS_CHART=xyz-charts/web-app` with `AUTO_DEVOPS_CHART_REPOSITORY`
(and `_USERNAME`/`_PASSWORD`) swaps the bundled `auto-deploy-app` chart for
yours; `HELM_UPGRADE_VALUES_FILE=.gitlab/auto-deploy-values.yaml` is the
lighter option - keep the chart, ship a values file in the repo.

## The line where Auto DevOps stops paying

If you find yourself overriding `build`, `production` and three scanners,
and maintaining a values file and a chart, you have a custom pipeline
with a large include. That is fine - but then write it as *your*
`.gitlab-ci.yml` built from components (week 7), and take the templates'
jobs one by one as you understand them. Auto DevOps got you to production
on day one; the rest of this track is how you own it from there.

## Self-check

- How do you give the deployed app a secret environment variable without touching YAML?
- What happens when your `.gitlab-ci.yml` defines a job with the same name as a template's?
- Name a sign that you have outgrown Auto DevOps.
