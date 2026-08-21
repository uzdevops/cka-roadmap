## Ordering work: stages

Stages are the coarse ordering tool. Jobs in one stage run together; the
next stage starts when all of them have succeeded (or are allowed to fail).

```yaml
stages:
  - build
  - test
  - package
  - deploy

build:     { stage: build,   script: [ "echo build" ] }
unit:      { stage: test,    script: [ "echo unit" ] }
integ:     { stage: test,    script: [ "echo integration" ] }
package:   { stage: package, script: [ "echo package" ] }
deploy:    { stage: deploy,  script: [ "echo deploy" ] }
```

Pipeline graph: `build` → (`unit` ‖ `integ`) → `package` → `deploy`. If
`integ` fails, `package` and `deploy` are never started and the pipeline
is red - a later stage is a promise that the earlier ones held.

## `stage` vs `stages`

Two keywords that are confused constantly:

- `stages:` (plural, top level) **declares the order**. It is a list.
- `stage:` (singular, inside a job) **places the job** in one of them.

A job whose `stage:` names something not in `stages:` is a configuration
error, and the pipeline editor tells you so. A job with no `stage:` goes to
`test` - which exists by default, but only if you did not redefine
`stages:` without it.

```yaml
stages: [build, deploy]     # no "test" any more

lint:
  script: echo lint         # ERROR: stage "test" does not exist
```

## Dependent jobs and what "dependent" means

"Job B depends on job A" can mean two different things:

1. **Ordering** - B must not start before A has finished. Stages give you
   this for free when A is in an earlier stage.
2. **Data** - B needs files that A produced. Stages do *not* give you
   this: every job starts from a clean clone. You need **artifacts**
   (next lesson).

```yaml
compile:
  stage: build
  script:
    - mkdir -p out && echo "binary" > out/app
  artifacts:
    paths: [out/]          # hand the file forward

test-binary:
  stage: test
  script:
    - test -f out/app      # present, because artifacts from earlier stages are downloaded
```

Remove the `artifacts:` block and `test-binary` fails with "No such
file": the ordering is still right, the data is gone.

## Stages are not free

Every stage boundary is a synchronisation point: the pipeline waits for
the *slowest* job in the stage before the next one can start. Five stages
with one job each is a serial pipeline that wastes every parallel runner
you have. Rule of thumb: stages for **phases of a release** (build, test,
deploy), `needs:` (two lessons on) for **fine-grained dependencies** inside
them.

## Self-check

- A job has no `stage:`. Where does it run, and when can that break?
- Why does a job in a later stage *not* see a file created in an earlier one?
- Name a cost of having many stages.
