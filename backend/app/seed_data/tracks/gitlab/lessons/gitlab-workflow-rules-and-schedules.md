## `workflow:rules` - when a pipeline is created

Job-level `rules:` decide which jobs exist. `workflow:rules` decides
whether the **pipeline** exists at all, before any job is considered. It is
the one place to stop the duplicated branch+MR pipelines for good:

```yaml
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"          # MR pipelines: yes
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS           # a branch push that has an MR: no
      when: never                                              #   (the MR pipeline covers it)
    - if: $CI_COMMIT_BRANCH                                    # other branch pushes: yes
    - if: $CI_COMMIT_TAG                                       # tags: yes
```

Same evaluation as job rules - first match wins, `when: never` or no match
means **no pipeline** and GitLab shows nothing, which is what you want for
a commit nobody asked to build.

`workflow:rules` can also set pipeline-wide variables and a name:

```yaml
workflow:
  name: "$PIPELINE_NAME · $CI_COMMIT_REF_SLUG"
  rules:
    - if: $CI_COMMIT_TAG
      variables: { PIPELINE_NAME: release, DEPLOY_TIER: production }
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      variables: { PIPELINE_NAME: main,    DEPLOY_TIER: staging }
    - when: always
      variables: { PIPELINE_NAME: ci }
```

## Pipeline schedules

*Build → Pipeline schedules → New schedule*: a cron expression, a target
branch or tag, and optional variables. The pipeline runs as the user who
owns the schedule, with `CI_PIPELINE_SOURCE == "schedule"` - which is how a
job says "only me, only at night":

```yaml
nightly-e2e:
  script: npm run test:e2e
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule" && $NIGHTLY == "true"

unit-tests:
  script: npm test
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
      when: never                          # do not waste the nightly on these
    - when: on_success
```

Typical uses: nightly end-to-end or performance suites, dependency
refreshes, cleanup of old review environments, re-building base images
weekly so security patches land without a code change.

Cron is in the schedule's timezone (set it explicitly); schedules can be
paused, run on demand with **Play**, and their variables show up in the
job like any pipeline variable.

## Skipping a pipeline on purpose

Sometimes a push should *not* run anything - a typo fix in a README on a
branch with no MR:

```bash
git commit -m "docs: fix typo [skip ci]"    # or [ci skip], in the commit message
git push -o ci.skip                          # push option, no commit message change
```

Both create **no pipeline** (a skipped one appears in the list for
traceability). Use them sparingly: a pipeline that did not run is a change
that was not verified, and "Pipelines must succeed" will block an MR whose
last commit skipped CI.

The structured alternative is `rules:changes` - "do not run the build if
only docs changed" - which keeps the decision in the YAML where it is
reviewed, rather than in somebody's commit message.

## Self-check

- A push to a branch with an open MR creates two pipelines. Which four
  `workflow:rules` lines fix that?
- How does a job know it was started by a schedule?
- Name one risk of `[skip ci]`.
