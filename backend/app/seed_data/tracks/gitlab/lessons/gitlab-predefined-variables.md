## What the runner already knows

Every job starts with a few hundred **predefined variables** describing
the commit, the pipeline, the project and the runner. You never set them;
you read them. The ones you will use weekly:

| Variable | Example | Use |
|---|---|---|
| `CI_COMMIT_SHA` / `CI_COMMIT_SHORT_SHA` | `a1b2c3d4…` / `a1b2c3d4` | image tags, build IDs |
| `CI_COMMIT_BRANCH` | `feature/login` | branch pipelines only (empty on MR/tag pipelines) |
| `CI_COMMIT_TAG` | `v1.4.0` | tag pipelines only |
| `CI_COMMIT_REF_NAME` / `CI_COMMIT_REF_SLUG` | `feature/login` / `feature-login` | the ref, and a DNS/path-safe version of it |
| `CI_DEFAULT_BRANCH` | `main` | "am I on the default branch?" without hard-coding |
| `CI_PIPELINE_SOURCE` | `push`, `merge_request_event`, `schedule`, `web`, `api`, `trigger` | the single most useful input to `rules:` |
| `CI_PIPELINE_ID` / `CI_PIPELINE_IID` | `1842317` / `57` | global id / per-project counter |
| `CI_JOB_NAME`, `CI_JOB_ID`, `CI_JOB_STATUS` | | logging, `after_script` |
| `CI_PROJECT_PATH`, `CI_PROJECT_DIR` | `xyz-team/app`, `/builds/xyz-team/app` | paths |
| `CI_REGISTRY`, `CI_REGISTRY_IMAGE`, `CI_REGISTRY_USER`, `CI_REGISTRY_PASSWORD` | | container registry login (week 5) |
| `CI_JOB_TOKEN` | | short-lived token for API / registry / package access |
| `CI_MERGE_REQUEST_IID`, `CI_MERGE_REQUEST_SOURCE_BRANCH_NAME`, `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` | | MR pipelines only |
| `CI_ENVIRONMENT_NAME`, `CI_ENVIRONMENT_URL` | | in jobs with `environment:` (week 6) |
| `GITLAB_USER_LOGIN`, `GITLAB_USER_EMAIL` | | who triggered it |

```yaml
show:
  image: alpine:3.20
  script:
    - echo "pipeline $CI_PIPELINE_IID from $CI_PIPELINE_SOURCE"
    - echo "ref $CI_COMMIT_REF_NAME (slug $CI_COMMIT_REF_SLUG) commit $CI_COMMIT_SHORT_SHA"
    - echo "by $GITLAB_USER_LOGIN on runner $CI_RUNNER_DESCRIPTION"
    - env | grep -E '^(CI_|GITLAB_)' | sort     # the full list, for this pipeline type
```

Run that job from a push, from a merge request and from a schedule, and
compare the three logs. The variables that are *empty* in one case and
set in another are exactly the ones `rules:` will key on tomorrow.

## Patterns built on them

**Image tag that is unique and traceable:**

```yaml
variables:
  IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
```

**A branch-safe hostname** (`feature/login` → `feature-login`):

```yaml
environment:
  name: review/$CI_COMMIT_REF_SLUG
  url: https://$CI_COMMIT_REF_SLUG.review.example.com
```

**Only on the default branch, without writing "main" anywhere:**

```yaml
rules:
  - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

**Calling the GitLab API from a job, with no stored token:**

```yaml
script:
  - 'curl --header "JOB-TOKEN: $CI_JOB_TOKEN" "$CI_API_V4_URL/projects/$CI_PROJECT_ID/releases"'
```

## Self-check

- Which variable tells you whether a pipeline was started by a schedule?
- `CI_COMMIT_BRANCH` is empty in your job. Name two kinds of pipeline where that is expected.
- Why `CI_COMMIT_REF_SLUG` rather than `CI_COMMIT_REF_NAME` in a URL?
