## Branch pipeline vs merge request pipeline

A push to a branch runs a **branch pipeline** on that branch's commit. If
the branch has an open MR, GitLab can *also* run a **merge request
pipeline** - `CI_PIPELINE_SOURCE == "merge_request_event"` - which carries
MR-specific variables (`CI_MERGE_REQUEST_IID`, target branch, labels…) and
whose results attach to the MR.

With week 3's `workflow:rules` the branch pipeline is suppressed when an
MR exists, so every push shows **one** pipeline in the MR. That is the
baseline; two refinements make it better.

## Merged results pipelines

A plain MR pipeline tests the **source branch** as it is. It can be green
while `main` has moved on in a way that breaks it - the merge would be
red after the fact. *Settings → Merge requests → Merge options → Enable
merged results pipelines* makes the MR pipeline run against the **result
of merging** source into target, on an internal ref. Same YAML, no changes
needed; `CI_MERGE_REQUEST_EVENT_TYPE` becomes `merged_result`.

## Merge trains

With several MRs racing into `main`, even merged-results can be stale by
the time you click Merge. A **merge train** queues MRs and runs the
pipeline for each *on top of the ones ahead of it in the queue*; the merge
happens automatically when its pipeline passes. Enable under the same
setting; a job that should run on trains checks
`$CI_MERGE_REQUEST_EVENT_TYPE == "merge_train"`.

Deploy jobs do **not** belong in MR pipelines or trains - they belong on
`main`/tags. Keep the `rules:` from week 4: test everywhere, build/publish
on `main` and tags, deploy from there.

## Only run what changed

```yaml
unit-tests:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        - "src/**/*"
        - "tests/**/*"
        - package-lock.json
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

On an MR pipeline `changes:` compares against the target branch, so a
docs-only MR skips the tests honestly. On `main` it would compare with
the previous commit - which is why the second rule has no `changes:`.

## Badges and the MR widget, assembled

Everything this week feeds one place. On a healthy MR you now see:

- pipeline status and duration, with the **Test summary** (JUnit) and
  **Coverage** delta (regex / Cobertura);
- **Code Quality** findings (ESLint report), inline in the diff;
- the container image built from `main` after merge, in the registry;

and in the README:

```markdown
[![pipeline](https://gitlab.com/xyz-team/nodejs-app/badges/main/pipeline.svg)](https://gitlab.com/xyz-team/nodejs-app/-/pipelines)
[![coverage](https://gitlab.com/xyz-team/nodejs-app/badges/main/coverage.svg)](https://gitlab.com/xyz-team/nodejs-app/-/graphs/main/charts)
```

## Self-check

- What does a merged results pipeline test that a plain MR pipeline does not?
- Why must deploy jobs stay out of merge request pipelines?
- On an MR pipeline, `changes:` is compared against what?
