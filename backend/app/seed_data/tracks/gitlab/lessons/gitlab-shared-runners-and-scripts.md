## Running on shared runners

With shared runners enabled the only thing a job needs is a `script`. The
runner chooses its default image when you set none - on gitlab.com that is
`ruby:3.1`. Always set an image explicitly; the default is a historical
accident, not a recommendation.

```yaml
default:
  image: alpine:3.20

check-tools:
  script:
    - apk add --no-cache curl jq
    - curl -s https://api.github.com/repos/git/git | jq .stargazers_count
```

That `apk add` line is the pattern for "my job needs a tool the image
lacks": install it at the top of the job. It works, it is slow (every job,
every time), and in week 5 you will replace most of it with a purpose-built
image or a cache.

## `before_script` and `after_script`

```yaml
default:
  before_script:
    - echo "== $CI_JOB_NAME on $(hostname) =="
    - apk add --no-cache bash
  after_script:
    - echo "== finished with status $CI_JOB_STATUS =="

build:
  script:
    - bash ./build.sh
```

- `before_script` lines are prepended to `script` **in the same shell** -
  variables you export there are visible in `script`.
- `after_script` runs in a **separate** shell, even after a failed
  `script`, with `$CI_JOB_STATUS` set to `success`/`failed`/`canceled`.
  Use it for cleanup and notifications; do not rely on variables from
  `script` being there.
- A job-level `before_script` **replaces** the default one; it does not
  add to it. If you want both, repeat the lines.

## Third-party libraries, the honest way

Installing dependencies in `before_script` keeps `script` readable:

```yaml
test:
  image: python:3.12-slim
  before_script:
    - pip install --quiet -r requirements.txt
  script:
    - pytest -q
```

Two rules: pin what you install (`requirements.txt`, `package-lock.json`,
`apk add curl=8.*`) so a pipeline that passed yesterday passes today, and
never `pip install` / `npm install` without the lock-file variant
(`pip install -r`, `npm ci`) - an unlocked install is a different
environment on every run.

## Scripts in files, not in YAML

Once a `script` grows past five lines, move it into the repository and
call it:

```yaml
deploy:
  image: alpine:3.20
  script:
    - chmod +x scripts/deploy.sh       # Git may not preserve the bit
    - ./scripts/deploy.sh "$CI_ENVIRONMENT_NAME"
```

```bash
#!/usr/bin/env sh
# scripts/deploy.sh - runs identically in CI and on a laptop
set -eu
target="${1:?environment name required}"
echo "deploying $CI_COMMIT_SHORT_SHA to $target"
```

`set -eu` makes the script fail on the first error and on unset variables
- the same contract the YAML `script` has. A script you can run locally is
a pipeline you can debug locally.

## Self-check

- A variable exported in `before_script` - is it visible in `script`? In `after_script`?
- Why `npm ci` rather than `npm install` in a pipeline?
- You set a job-level `before_script`. Does the `default:` one still run?
