## A pipeline you did not write

**Auto DevOps** is a GitLab-maintained `.gitlab-ci.yml` that detects your
language, builds an image with Cloud Native Buildpacks, runs tests, code
quality and security scans, and deploys to Kubernetes with review apps,
staging and production - from a repository that contains **no pipeline
file at all**. Everything you did by hand in weeks 1-7, as defaults.

Enable: *Settings → CI/CD → Auto DevOps → Default to Auto DevOps
pipeline* (per project, group or instance). It applies only when the
project has no `.gitlab-ci.yml` of its own.

## What the generated pipeline contains

| Stage | Jobs (abridged) | Needs |
|---|---|---|
| build | `build` - buildpacks (or your Dockerfile if present) → `$CI_REGISTRY_IMAGE` | registry |
| test | `test` (language test via buildpack), `code_quality`, SAST, secret detection, dependency & container scanning, license scanning | - |
| review | `review` - review app per MR, `stop_review` | Kubernetes + agent |
| dast | DAST against the review app | review app |
| staging | `staging` (if `STAGING_ENABLED`) | Kubernetes |
| canary | `canary` (if `CANARY_ENABLED`) | Kubernetes |
| production | `production` - rolling or incremental rollout | Kubernetes + domain |
| performance | browser performance against production | - |
| cleanup | `stop_review` on MR close | - |

Without a cluster, only `build` and the `test` stage run; deploy jobs are
skipped, not failed. Connect a cluster with the **agent** (week 6) and set
`KUBE_CONTEXT` (or use the legacy certificate integration) and a
`KUBE_INGRESS_BASE_DOMAIN` (e.g. `apps.xyz.example.com` with a wildcard
DNS record to the cluster's ingress), and the deploy stages light up.

## Prerequisites, in order

1. **Registry** enabled (it is, on gitlab.com).
2. **Kubernetes** cluster with an ingress controller; agent connected with
   `ci_access` to the project.
3. **Base domain** variable `KUBE_INGRESS_BASE_DOMAIN` and wildcard DNS.
4. Optional: `POSTGRES_ENABLED=true` for a bundled PostgreSQL per env
   (fine for review apps, never for production), `AUTO_DEVOPS_CHART`/
   `AUTO_DEVOPS_CHART_REPOSITORY` to use your own Helm chart.

## Buildpacks vs Dockerfile

If the repo has a `Dockerfile`, Auto DevOps builds with it. Otherwise
Cloud Native Buildpacks (`heroku/builder` by default) detect Node/Python/
Java/Go/… and produce an image with no configuration - slow the first
time, reliable after. `AUTO_DEVOPS_BUILD_IMAGE_EXTRA_ARGS` passes
`--build-arg`s; `BUILDPACK_URL` pins a specific buildpack.

## Why it matters, and why not for everything

Auto DevOps is the fastest route from "empty repo" to "deployed with
scans" - excellent for internal tools, prototypes and teams without a
platform group. It is opinionated: its deployment is its Helm chart, its
stages are its stages, and customising beyond a point (next lesson) means
you are maintaining a pipeline again, just one you did not start. Knowing
what it generates is also the best reference for what a *complete*
pipeline contains.

## Self-check

- When does Auto DevOps apply to a project?
- Which two things must exist before the deploy stages run?
- What decides whether the image is built by buildpacks or a Dockerfile?
