## The five components

A GitLab pipeline is made of five things. Every later lesson is one of
these five, looked at more closely.

```text
.gitlab-ci.yml ──► pipeline ──► stages ──► jobs ──► runner (executor)
   the file        one run      ordering   work     the machine
```

### 1. `.gitlab-ci.yml`

YAML in the repository root. Top-level keys are either **global keywords**
(`stages`, `default`, `variables`, `workflow`, `include`) or **job names**.
Anything that has a `script` is a job.

```yaml
default:
  image: alpine:3.20        # applies to every job that does not set its own

variables:
  APP_NAME: xyz-web         # available to every job

stages: [prepare, build]
```

### 2. Pipeline

One execution of the file for one commit. A pipeline has a **source** -
`push`, `merge_request_event`, `schedule`, `web`, `api`, `trigger` - that
`rules:` can read as `$CI_PIPELINE_SOURCE`. A commit can produce more than
one pipeline (a branch pipeline *and* a merge request pipeline) - lesson
"Merge request pipelines" sorts that out.

### 3. Stages

The order. Default stages if you declare none: `.pre`, `build`, `test`,
`deploy`, `.post`. Declaring your own replaces the middle three; `.pre`
and `.post` always exist and bracket the rest.

### 4. Jobs

```yaml
build-app:
  stage: build
  image: node:20-alpine
  before_script:
    - npm ci
  script:
    - npm run build
  after_script:
    - echo "done, exit code was $CI_JOB_STATUS"
  artifacts:
    paths: [dist/]
```

`before_script` and `after_script` run in the same shell as `script`
(`after_script` runs even when `script` fails). The job's **status** is
decided by `script` alone.

### 5. Runners and executors

A **runner** is the `gitlab-runner` process that polls GitLab for jobs.
Its **executor** decides *how* a job is isolated: `shell` (directly on the
host), `docker` (each job in a fresh container - the common choice),
`kubernetes` (each job a Pod), and a few more. On gitlab.com the shared
runners use `docker` on autoscaled VMs, which is why `image:` matters so
much: it is the container your `script` runs in.

## Reading a job log through these five

```text
Running with gitlab-runner 17.x (abc123)         ← the runner
  on blue-1.saas-linux-small-amd64.runners ...   ← runner name / executor
Preparing the "docker+machine" executor          ← executor
Using Docker executor with image node:20-alpine  ← the image
Getting source from Git repository               ← fresh clone
$ npm ci                                         ← before_script
$ npm run build                                  ← script
Uploading artifacts for successful job           ← artifacts
Job succeeded
```

## Self-check

- Which two keys can never be removed from a pipeline's stage list?
- A job fails in `script` but `after_script` runs fine. What is the job's status?
- Name three executors and say where each job runs for them.
