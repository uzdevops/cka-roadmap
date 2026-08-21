## Your first `.gitlab-ci.yml`

In `pipeline-basics`, create the file through the **Pipeline editor** so
you get validation for free:

```yaml
stages:
  - build
  - test

build-job:
  stage: build
  script:
    - echo "Compiling the code..."
    - echo "Compile complete."

unit-test-job:
  stage: test
  script:
    - echo "Running unit tests... This will take about 10 seconds."
    - sleep 10
    - echo "Code coverage is 90%"

lint-test-job:
  stage: test
  script:
    - echo "Linting code... This will take about 5 seconds."
    - sleep 5
    - echo "No lint issues found."
```

Commit to `main`. Within seconds **Build → Pipelines** shows a running
pipeline: `build-job` first, then `unit-test-job` and `lint-test-job`
together. Click a job. The log shows the shared runner picking the job up,
pulling the default image (`ruby:3.1` on gitlab.com unless you set one -
which is why the next thing you will do is set one), cloning the
repository and echoing each command before running it.

## Make a job fail on purpose

Pipelines teach best when they break. Change `lint-test-job`:

```yaml
lint-test-job:
  stage: test
  script:
    - echo "Linting..."
    - exit 1
```

The job turns red, the *pipeline* turns red, `unit-test-job` still passes
(same stage, independent), and nothing would run in a later stage. Open
the failed job: the log ends with `ERROR: Job failed: exit code 1`. Press
**Retry** - same commit, new job, same result - because a retry re-runs
the job, it does not re-read the file. Fix the file and push: a *new*
pipeline.

## Commands you will use on every job

```yaml
explore:
  image: alpine:3.20
  script:
    - pwd                      # /builds/<group>/<project>
    - ls -la                   # a clean clone of the repo
    - git log -1 --oneline     # the commit that triggered this pipeline
    - env | grep ^CI_ | sort   # the predefined variables (week 3)
    - cat /etc/os-release      # the image you are really running in
```

Paste this into any pipeline you do not understand. It answers *where am
I, what do I have, who triggered me* in five lines.

## Self-check

- You press Retry on a failed job after fixing the YAML. Why does it still fail?
- In the three-job pipeline above, what happens to `unit-test-job` when
  `lint-test-job` fails?
