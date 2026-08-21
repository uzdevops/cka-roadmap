## Resource groups - one at a time, please

Two pipelines deploying to the same environment at the same moment is how
a staging server ends up half-old, half-new. A **resource group** is a
named mutex: jobs that share one run **one at a time**, across pipelines.

```yaml
deploy-staging:
  script: ./deploy.sh staging
  resource_group: staging          # any string; scope is the project

deploy-prod:
  script: ./deploy.sh production
  resource_group: production
```

The second `deploy-staging` waits (status *waiting for resource*) until the
first finishes. `process_mode` in the API (`unordered` default,
`oldest_first`, `newest_first`) decides the queue order; `newest_first`
is what you want for "only the latest commit should actually deploy".

## Timeouts

A hung job holds a runner hostage. Project default is 1 hour (*Settings →
CI/CD → General pipelines*); a job can shorten it, never exceed the
runner's own limit:

```yaml
integration:
  script: ./run-integration.sh
  timeout: 20 minutes              # 1h 30m, 2h, 90m - all valid
```

A job that hits the limit is **failed** with a clear message; that is
better than a pipeline nobody notices for an hour.

## `image:` and `services:`

`image:` is the container the job's shell runs in. `services:` are
**extra containers** started alongside it and reachable by hostname - the
standard way to give a test job a database:

```yaml
integration-tests:
  image: node:20-alpine
  services:
    - name: postgres:16-alpine
      alias: db                    # hostname inside the job network
  variables:
    POSTGRES_USER: app
    POSTGRES_PASSWORD: secret
    POSTGRES_DB: app_test
    DATABASE_URL: postgres://app:secret@db:5432/app_test
  script:
    - npm ci
    - npm run test:integration
```

The variables in the job are also passed to the service containers, which
is how `postgres` picks up its user and password. Without an `alias`, the
hostname is derived from the image name (`postgres`). Image pulls follow
the runner's pull policy - `if-not-present` on a self-managed docker
runner, always fresh on SaaS.

`image:` can also carry an `entrypoint:` override and a `pull_policy:`
(where the runner allows it). Useful when a tool image defaults to running
the tool instead of a shell:

```yaml
scan:
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]               # give me a shell, not `trivy` as PID 1
  script:
    - trivy image --exit-code 1 "$IMAGE"
```

## `parallel:` and `parallel:matrix`

Run the same job N times (`CI_NODE_INDEX` / `CI_NODE_TOTAL` let you shard
a test suite), or once per combination of variables:

```yaml
unit-shards:
  script: npm test -- --shard=$CI_NODE_INDEX/$CI_NODE_TOTAL
  parallel: 4

build:
  script: ./build.sh "$OS" "$ARCH"
  parallel:
    matrix:
      - OS: [linux, darwin]
        ARCH: [amd64, arm64]
      - OS: [windows]
        ARCH: [amd64]
```

That matrix creates five jobs named `build: [linux, amd64]` and so on,
each with its own `$OS`/`$ARCH`, running in parallel. A job that needs
one of them spells the name out: `needs: ["build: [linux, amd64]"]`.

## Self-check

- Two pipelines run `deploy-staging` within a minute. What guarantees the
  deployments do not overlap?
- A test job needs Redis. Which keyword, and how does the job reach it?
- How many jobs does a matrix of `OS: [a, b]` × `ARCH: [x, y, z]` create?
