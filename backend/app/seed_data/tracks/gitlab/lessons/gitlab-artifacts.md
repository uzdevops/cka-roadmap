## Passing files forward

**Artifacts** are files a job uploads to GitLab when it finishes, kept for
a while, and downloaded into the workspace of later jobs. They are the
*only* sanctioned way for one job's output to become another job's input.

```yaml
build:
  stage: build
  image: node:20-alpine
  script:
    - npm ci
    - npm run build                 # writes dist/
  artifacts:
    paths:
      - dist/
    expire_in: 1 week

package:
  stage: package
  image: alpine:3.20
  script:
    - ls dist/                      # downloaded automatically
    - tar czf app.tgz dist/
  artifacts:
    paths: [app.tgz]
    expire_in: 30 days
```

What to know:

- `paths:` are relative to the project root and support globs
  (`logs/*.log`). `exclude:` removes matches.
- `expire_in:` - `1 hour`, `2 days`, `never`. The latest artifact of each
  job on a branch is **kept regardless** of expiry (*Settings → CI/CD →
  Artifacts* can turn that off). Set an expiry on everything; artifact
  storage is finite and billable.
- By default a job downloads the artifacts of **all jobs in earlier
  stages**. Restrict with `dependencies:` when that is wasteful:

```yaml
package:
  dependencies: [build]           # only build's artifacts, nothing else
```

`dependencies: []` downloads nothing.

## `when:` - artifacts from failed jobs

```yaml
test:
  script: npm test
  artifacts:
    when: always                    # on_success (default) | on_failure | always
    paths: [test-results/]
```

Test logs are most valuable when the tests failed, and `on_success` would
throw exactly those away. Use `always` for reports and logs.

## Downloading and browsing

Every job page has **Browse** and **Download** for its artifacts, and
they are addressable by URL - the pattern
`/-/jobs/artifacts/<ref>/download?job=<name>` gives a stable "latest build
of main" link for a README badge or a colleague.

```bash
curl --header "PRIVATE-TOKEN: $TOKEN" -L \
  "https://gitlab.com/api/v4/projects/<id>/jobs/artifacts/main/download?job=build" \
  -o dist.zip
```

## Artifacts are not cache

| | artifacts | cache |
|---|---|---|
| purpose | hand **results** to later jobs / humans | speed up **rebuilding** dependencies |
| guaranteed? | yes - stored on GitLab | no - best effort, per runner |
| scope | this pipeline (and downloads) | across pipelines, by key |
| example | `dist/`, test reports, a package | `node_modules/`, `.m2/` |

Putting `node_modules/` in artifacts "works" and uploads hundreds of
megabytes on every job. Week 5 covers cache properly; for now, artifacts
carry outputs, nothing else.

## Self-check

- A stage-2 job needs a file from stage 1. What two lines make it happen?
- Your test reports never appear when tests fail. Which keyword fixes it?
- Why is `node_modules/` the wrong thing to put in artifacts?
