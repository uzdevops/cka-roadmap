## The unit test job

```yaml
unit-tests:
  stage: test
  image: node:20-alpine
  before_script:
    - node --version && npm --version
    - npm ci --prefer-offline --no-audit --progress=false
  script:
    - npm test
```

Push, open the job log, and read it against the local run from two days
ago:

- `npm ci` installs exactly the lock-file tree. If it fails with *"npm ci
  can only install packages when your package.json and package-lock.json
  are in sync"*, somebody edited `package.json` without updating the lock -
  a real bug, caught before review.
- `jest --ci` prints the same `Tests: 6 passed` and the coverage table.
- The job is green because `npm test` exited 0.

## Pin the toolchain

`node:20-alpine` floats with every 20.x release, which is usually fine and
occasionally surprising. When a version matters, say so:

```yaml
default:
  image: node:20.17-alpine3.20
```

and keep `"engines": { "node": "20.x" }` in `package.json` so `npm` warns
when they drift apart.

## Tests that need a service

The XYZ app's unit tests mock the database. Integration tests do not - add
them as a **second** job with a service, rather than slowing every test
run down:

```yaml
integration-tests:
  stage: test
  image: node:20-alpine
  services:
    - name: postgres:16-alpine
      alias: db
  variables:
    POSTGRES_USER: app
    POSTGRES_PASSWORD: app
    POSTGRES_DB: app_test
    DATABASE_URL: postgres://app:app@db:5432/app_test
  before_script:
    - npm ci
    - npm run db:migrate
  script:
    - npm run test:integration
```

Both jobs sit in `stage: test` and run in parallel; a failure in either
blocks the merge.

## Make a test fail, watch what happens

Break an assertion in `tests/app.test.js`, push to a branch, open an MR:

- the pipeline turns red at `unit-tests`;
- the MR shows **"Pipeline failed"** and the **Merge** button is disabled
  (with "Pipelines must succeed" on);
- the job log shows the Jest failure - but you have to *open the log and
  scroll* to find which test. Tomorrow's lesson puts that failure into the
  MR itself.

Revert the break, push, and watch the MR go green without anyone touching
it. That loop - push, red, fix, green - is the product of this week.

## Exit codes are the contract

A job is green when the last command in `script` exits 0. Two traps:

```yaml
script:
  - npm test || true          # NEVER: hides failures
  - npm test; echo done       # the echo's exit code (0) becomes the job's
```

If you genuinely need to run something after a failing command, use
`after_script`, or `allow_failure` on the job - never a `|| true`.

## Self-check

- `npm ci` fails about `package.json` and the lock being out of sync. Is
  that a CI problem or an application problem?
- Why are integration tests a separate job rather than part of `unit-tests`?
- What is wrong with `npm test; echo done` as the last line of a script?
