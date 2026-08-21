## The cost of `npm ci` four times

Week 4's pipeline installs dependencies in `lint`, `unit-tests`,
`integration-tests` and `build` - four downloads of the same
`node_modules`. **Cache** keeps files between jobs and pipelines so the
second install is a copy, not a download.

```yaml
variables:
  npm_config_cache: "$CI_PROJECT_DIR/.npm"

default:
  cache:
    key:
      files: [package-lock.json]          # one cache per lock-file content
    paths:
      - .npm/                             # npm's download cache, not node_modules
    policy: pull-push

unit-tests:
  script:
    - npm ci --prefer-offline             # hits .npm/ first
    - npm test
```

Why `.npm/` and not `node_modules/`: `npm ci` deletes `node_modules`
before installing anyway, so caching it gains nothing; caching npm's
*download* cache makes `npm ci` fast and still exact.

## The keywords that matter

| Key | Meaning |
|---|---|
| `key:` | a string, or `files:` (hash of those files) - caches are looked up by key |
| `key:prefix:` | `prefix: $CI_JOB_NAME` + files → per-job caches that still bust on lock change |
| `paths:` | what to save; must be inside the project dir |
| `policy:` | `pull-push` (default), `pull` (read-only - use on jobs that only consume), `push` (write-only) |
| `fallback_keys:` | try these if the main key is missing (e.g. `main-cache`) |
| `untracked: true` | cache all git-untracked files |
| `when:` | `on_success` / `on_failure` / `always` - whether to save after a failed job |

```yaml
install:
  stage: .pre
  script: npm ci
  cache:
    key: { files: [package-lock.json] }
    paths: [.npm/]
    policy: push                 # this job fills the cache…

unit-tests:
  cache:
    key: { files: [package-lock.json] }
    paths: [.npm/]
    policy: pull                 # …these only read it, and never upload it back
```

## Cache is best effort

Cache lives **on the runner** (or in a shared object store if the runner
is configured for it - gitlab.com's SaaS runners are). Different runner,
different cache; a new autoscaled VM may have none. Your job must work
with an **empty** cache - slower, not broken. The rule:

- **artifacts** - correctness: results that later jobs *need*;
- **cache** - speed: things a job can rebuild if missing.

If a missing cache breaks a job, you have an artifact pretending to be a
cache.

## Clearing a bad cache

*Build → Pipelines → Clear runner caches* bumps an internal index so every
key is treated as new. Use it when a cache was poisoned (a half-written
`node_modules`, a tool upgrade) - cheaper than renaming keys in YAML.

## Self-check

- Why cache `.npm/` instead of `node_modules/` with `npm ci`?
- A job sets `policy: pull`. Does it upload its cache at the end?
- A required file is in cache and the job fails when the cache is empty. What is the design error?
