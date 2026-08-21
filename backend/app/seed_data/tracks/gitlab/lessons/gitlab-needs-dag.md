## Breaking out of the stage lock-step

Stages make every job wait for the slowest job of the previous stage. With
`needs:` a job declares *exactly* which jobs it depends on and starts the
moment those finish - regardless of stage. The pipeline becomes a
**directed acyclic graph** (DAG).

```yaml
stages: [build, test, deploy]

build-api:   { stage: build, script: [ "sleep 5;  echo api" ] }
build-web:   { stage: build, script: [ "sleep 60; echo web" ] }

test-api:
  stage: test
  needs: [build-api]              # starts after 5 s, not after 60
  script: echo testing api

test-web:
  stage: test
  needs: [build-web]
  script: echo testing web

deploy:
  stage: deploy
  needs: [test-api, test-web]
  script: echo deploy
```

Without `needs`, `test-api` would idle for a minute waiting for `build-web`.
With it, the API half of the pipeline is done before the web build has
finished compiling.

## `needs` also controls artifacts

A job with `needs:` downloads artifacts **only from the jobs it needs**
(not from every earlier stage). Turn that off per dependency:

```yaml
deploy:
  needs:
    - job: build-api
      artifacts: true         # default
    - job: lint
      artifacts: false        # ordering only, no download
```

## Optional needs

If a needed job does not exist in a particular pipeline (because its
`rules:` excluded it), the pipeline is **invalid** - unless you say the
dependency is optional:

```yaml
deploy:
  needs:
    - job: integration-tests
      optional: true           # fine if the job was not created this time
```

## Reading the DAG

The pipeline page has a **Needs** view next to the stage view; it draws
the real dependency graph. Two signs of a healthy DAG:

- no job waits on something it does not read from;
- the critical path (longest chain) is as short as your slowest job chain
  genuinely needs to be.

## When *not* to use `needs`

- When the ordering really is "everything in stage N before anything in
  stage N+1" - a deploy that must see every test pass. Stages say that in
  one line; `needs` would need every job listed.
- When jobs are created dynamically (matrix, child pipelines) and the list
  would go stale.

Mixing is normal: stages for the release phases, `needs:` inside them to
let fast things go first.

## Self-check

- `test-api` has `needs: [build-api]`. Does it still wait for the *stage*
  `build` to finish?
- A job with `needs:` - whose artifacts does it download by default?
- Why can a `needs:` on a rules-excluded job break the whole pipeline, and
  how do you prevent it?
