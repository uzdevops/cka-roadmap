## Merge requests in thirty seconds

A **merge request** (MR) proposes merging one branch into another and is
where review happens: diff, discussion, approvals, and - for us - a
pipeline whose result blocks or allows the merge. *Settings → Merge
requests → "Pipelines must succeed"* turns a green pipeline into a
requirement, which is the minimum bar for continuous integration.

```bash
git switch -c feature/healthcheck
git commit -am "add /healthz endpoint"
git push -u origin feature/healthcheck     # GitLab prints a "create merge request" link
```

Pushing a branch runs a **branch pipeline**. Opening an MR can run a
**merge request pipeline** (`CI_PIPELINE_SOURCE == "merge_request_event"`).
You decide which exists with `rules:` - and if you decide nothing, you get
both, doubled up. That is the first thing `rules:` fixes.

## `rules:` - when a job is created

`rules:` is evaluated **when the pipeline is created**, top to bottom; the
first matching rule decides whether the job exists and with what
attributes. No match → job is not created.

```yaml
unit-tests:
  script: npm test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"     # on MR pipelines
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH          # and on main
    # any other push → no job
```

Each rule may carry:

| Key | Meaning |
|---|---|
| `if:` | a CI/CD variable expression |
| `changes:` | the rule matches only if these paths changed in the commit/MR |
| `exists:` | …only if such files exist in the repo |
| `when:` | `on_success` (default), `manual`, `delayed`, `always`, `never` |
| `allow_failure:` | red job, green pipeline |
| `variables:` | set variables only when this rule matched |

```yaml
build-docs:
  script: make docs
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes: [ "docs/**/*", "mkdocs.yml" ]
    - when: never

deploy-prod:
  script: ./deploy.sh prod
  rules:
    - if: $CI_COMMIT_TAG                  # only on tags…
      when: manual                        # …and only when a human clicks
      allow_failure: false                # the pipeline is "blocked" until then

nightly-cleanup:
  script: ./cleanup.sh
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

## Reading rules like the runner does

- Rules are **or**-ed top to bottom; conditions inside one rule are **and**-ed.
- A bare `- when: never` at the end is a readability habit: it says "I
  thought about the fallthrough", although no match already means no job.
- `when: manual` without `allow_failure: false` means the later stages run
  **without** waiting for the click (manual jobs are allowed to fail by
  default). With it, the pipeline stops at that job - a real gate.
- `rules:` and the older `only:`/`except:` cannot be mixed in one job.
  Everything new uses `rules:`.

## A complete MR-aware skeleton

```yaml
workflow:                      # next lesson - but here is the shape
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_COMMIT_TAG

stages: [test, build, deploy]

test:
  stage: test
  script: npm test            # runs on MRs, main and tags (inherits workflow)

build:
  stage: build
  script: docker build .
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_COMMIT_TAG

deploy:
  stage: deploy
  script: ./deploy.sh
  rules:
    - if: $CI_COMMIT_TAG
      when: manual
      allow_failure: false
```

## Self-check

- Two rules in a job: `if: A` then `if: B`. The pipeline matches both.
  Which one applies?
- What does `when: manual` do to the *next* stage if `allow_failure` is
  left at its default?
- You push a branch that has an open MR. How many pipelines run if there
  are no `rules:` anywhere?
