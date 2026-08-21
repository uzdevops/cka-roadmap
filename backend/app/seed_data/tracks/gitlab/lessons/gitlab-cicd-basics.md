## The shape of every pipeline

Whatever the tool, a pipeline is the same idea: a sequence of **stages**,
each made of **jobs**, triggered by an **event** and executed somewhere by
an **agent**. GitLab's names for these are:

| Concept | GitLab term | Where it is defined |
|---|---|---|
| the definition | `.gitlab-ci.yml` | root of the repository |
| a group of jobs that run together | `stage` | `stages:` list |
| one unit of work with its own log | `job` | any top-level key with a `script` |
| the machine that executes a job | **runner** | registered to the project/group/instance |
| the trigger | push, merge request, schedule, API, manual | implicit, shaped by `rules:` |

```yaml
stages:
  - build
  - test
  - deploy

compile:
  stage: build
  script: echo "building"

unit:
  stage: test
  script: echo "testing"

lint:
  stage: test
  script: echo "linting"

release:
  stage: deploy
  script: echo "deploying"
```

Jobs in the **same stage run in parallel** (if enough runners are free);
a stage starts only when the previous one has finished. `unit` and `lint`
run side by side; `release` waits for both. The whole thing appears in
GitLab as a graph of coloured circles - the **pipeline view** - and each
circle opens the job's log.

## What a job actually does

A job is a shell session on a runner. Every line under `script:` is run
in order; the first non-zero exit code fails the job. Nothing survives
between jobs except what you explicitly hand over as an **artifact** (a
later lesson) - each job starts from a fresh checkout of the repository.

```yaml
hello:
  script:
    - echo "Running on $(hostname)"
    - ls -la
    - cat README.md | head -5
```

Three things to internalise now, because they explain most "but it worked
locally" moments later:

1. The job runs **on the runner**, not on your laptop and not on the
   GitLab server. Whatever the runner has installed is what you get.
2. The working directory is a **clean clone** of the repository at the
   commit that triggered the pipeline.
3. The job has **no memory** of previous jobs or pipelines unless you use
   artifacts or cache.

## Why GitLab CI/CD specifically

- One product: the repository, the pipeline, the registry, the issue
  tracker and the deploy environments share one permission model and one UI.
- The pipeline is **just YAML in Git** - reviewed in merge requests, tested
  on branches, diffable, revertable.
- SaaS runners are available on gitlab.com with zero setup, and the same
  YAML runs unchanged on runners you host yourself (week 8).

## Self-check

- Two jobs are in the same stage. Do they run one after another or together?
- A job creates a file in `/tmp`. Can the next stage read it? Why not?
