## The XYZ team's pipeline, on a whiteboard

Before YAML, the shape. The team agreed on this:

```text
 push / MR
    │
    ▼
┌─────────┐   ┌──────────────────────┐   ┌────────────┐   ┌───────────────┐
│  test   │ → │  build               │ → │  publish   │ → │  deploy       │
│ lint    │   │  docker build        │   │  push image│   │  dev (auto)   │
│ unit    │   │                      │   │  to GitLab │   │  staging      │
│ coverage│   │                      │   │  registry  │   │  prod (manual)│
└─────────┘   └──────────────────────┘   └────────────┘   └───────────────┘
  weeks 4        week 5                     week 5            week 6
```

Decisions worth writing down, because each one is a `rules:` line later:

| Question | Answer | Why |
|---|---|---|
| Where does `test` run? | MRs, `main`, tags | every change verified, nothing else wasted |
| Where does `build`/`publish` run? | `main` and tags | feature branches do not need images |
| Where does `deploy` run? | `main` → dev automatically; tags → staging, then prod on a button | continuous *delivery*, with a human before prod |
| What blocks a merge? | a red `test` stage | "Pipelines must succeed" |
| What is the image tag? | `$CI_COMMIT_SHORT_SHA`, plus `latest` on `main` and the tag name on tags | traceable and human-friendly |

## Import the repository

The application lives in the course resources; bring it under your group
so pushes trigger *your* pipelines:

**New project → Import project → Repository by URL** →
`https://gitlab.com/<course-namespace>/nodejs-app.git` → name it
`nodejs-app` in `xyz-team`. Then clone, and confirm the shared runners are
enabled under *Settings → CI/CD → Runners*.

## The skeleton to fill in this week

```yaml
# .gitlab-ci.yml - XYZ nodejs-app
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS
      when: never
    - if: $CI_COMMIT_BRANCH
    - if: $CI_COMMIT_TAG

default:
  image: node:20-alpine

variables:
  npm_config_cache: "$CI_PROJECT_DIR/.npm"     # for the cache, week 5

stages:
  - test
  - build
  - publish
  - deploy

lint:
  stage: test
  script: [ "npm ci", "npm run lint" ]

unit-tests:
  stage: test
  script: [ "npm ci", "npm test" ]
```

Two jobs in `test`, both installing dependencies - slow and duplicated on
purpose for now. Week 5's cache lesson removes the duplication; this week
is about getting **correct** results and **reports** out of these jobs.

## A habit: commit the pipeline in small steps

Each lesson this week adds one job or one keyword and pushes. Forty
small, green commits teach more than one large one that fails in four
places at once - and `git blame` on `.gitlab-ci.yml` becomes a changelog
of decisions.

## Self-check

- Why do `build` and `publish` not run on feature branches?
- What does `workflow:rules` above do to a branch that has an open MR?
- Where will the duplication of `npm ci` be solved, and with what?
