## The XYZ pipeline, assembled

Eight weeks ago the release was an afternoon in one engineer's head. This
is what `nodejs-app/.gitlab-ci.yml` looks like now - and every line of it
is something you have run:

```yaml
include:
  - component: gitlab.com/xyz-team/ci-components/node-test@1.1.0
    inputs: { node_version: "20" }
  - component: gitlab.com/xyz-team/ci-components/docker-build@2.0.1
  - template: Jobs/Secret-Detection.gitlab-ci.yml
  - template: Jobs/Dependency-Scanning.gitlab-ci.yml
  - template: Jobs/Container-Scanning.gitlab-ci.yml

workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS
      when: never
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_COMMIT_TAG

default:
  interruptible: true
  retry: { max: 1, when: [runner_system_failure, stuck_or_timeout_failure] }

stages: [test, build, publish, deploy]

lint:
  stage: test
  extends: .node
  script: npx eslint . --format gitlab --output-file gl-codequality.json
  artifacts: { when: always, reports: { codequality: gl-codequality.json } }
  allow_failure: { exit_codes: [1] }

container_scanning:
  needs: [publish-image]
  variables: { CS_IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA" }

.deploy:
  stage: deploy
  interruptible: false
  tags: [deploy]
  resource_group: $CI_ENVIRONMENT_NAME
  script:
    - ./deploy.sh "$CI_ENVIRONMENT_NAME" "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
    - curl -fsS "$CI_ENVIRONMENT_URL/healthz"

deploy-review:
  extends: .deploy
  environment: { name: review/$CI_COMMIT_REF_SLUG, url: https://$CI_ENVIRONMENT_SLUG.review.xyz.example.com, on_stop: stop-review, auto_stop_in: 2 days }
  rules: [ { if: $CI_PIPELINE_SOURCE == "merge_request_event" } ]

stop-review:
  extends: .deploy
  script: ./deploy.sh stop "$CI_ENVIRONMENT_SLUG"
  environment: { name: review/$CI_COMMIT_REF_SLUG, action: stop }
  variables: { GIT_STRATEGY: none }
  rules: [ { if: $CI_PIPELINE_SOURCE == "merge_request_event", when: manual } ]

deploy-dev:
  extends: .deploy
  environment: { name: dev, url: https://dev.xyz.example.com }
  rules: [ { if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH } ]

deploy-staging:
  extends: .deploy
  environment: { name: staging, url: https://staging.xyz.example.com }
  rules:
    - if: $CI_COMMIT_TAG
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
      allow_failure: false

deploy-prod:
  extends: .deploy
  environment: { name: production, url: https://xyz.example.com }
  rules: [ { if: $CI_COMMIT_TAG, when: manual, allow_failure: false } ]
```

Plus, outside the file: protected `main` and `v*`, protected
`production` with approvals, protected and scoped variables, a `deploy`
runner that only takes protected refs, `CODEOWNERS` on the pipeline,
group scan-execution and approval policies, cleanup policies on the
registry, and a README with pipeline and coverage badges.

## Reading it back as a checklist

| Week | What in the file proves it |
|---|---|
| 1-2 | stages, jobs, images, artifacts, `needs` inside the components |
| 3 | `workflow:rules`, every `rules:` block, `resource_group`, `interruptible` |
| 4 | JUnit + coverage + code quality reports, `allow_failure:exit_codes` |
| 5 | `.node`/cache via the component, docker-build component, registry, MR-aware workflow |
| 6 | environments, review apps, manual gates, tag-driven production |
| 7 | components with versions, scanners, protections around the file |
| 8 | `tags: [deploy]` on a self-managed protected runner; Auto DevOps as the reference you now beat |

## Where to go next

- **GitLab Certified CI/CD Associate** - the exam maps closely to this
  track; its hands-on portion is the XYZ pipeline in miniature.
- **GitOps** - let Flux or Argo CD pull from a manifests repo your
  pipeline writes to; the `deploy` stage becomes a commit.
- **Observability of the pipeline** - DORA metrics in *Analyze*, pipeline
  duration trends, and the deployment frequency chart the XYZ team can
  now show to the people who used to wait an afternoon.

## Self-check (the real one)

Take a repository you actually own and give it, from memory: a
workflow-filtered pipeline, a tested-and-reported `test` stage, an image
published by SHA, a dev environment deployed automatically and a
production one behind a protected manual gate. If you can do that without
opening this track again, you are done with it.
