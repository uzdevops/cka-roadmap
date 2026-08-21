## Letting a job fail without failing the pipeline

Some checks are advisory: a new linter rule the team has not cleaned up
for yet, an experimental test, a "nice to know" scan. They should run,
report, and **not** block the merge while the team catches up.

```yaml
lint:
  stage: test
  script:
    - npm ci
    - npm run lint
  allow_failure: true
```

The job still goes red; the pipeline shows a **yellow warning** icon and is
treated as passed; later stages run. The MR says "passed with warnings".
Be deliberate about removing `allow_failure` once the backlog is clear -
an advisory check that stays advisory forever is noise people learn to
ignore.

`allow_failure` can also be narrowed to specific exit codes, which is how
you distinguish "found issues" from "the tool crashed":

```yaml
lint:
  script: npm run lint
  allow_failure:
    exit_codes: [1]           # eslint "problems found" is advisory…
                              # …any other code (tool broken, 2+) fails the job for real
```

## ESLint with a report that the MR understands

```yaml
lint:
  stage: test
  script:
    - npm ci
    - npx eslint . --format gitlab --output-file gl-codequality.json
  artifacts:
    when: always
    reports:
      codequality: gl-codequality.json
  allow_failure: true
```

With `eslint-formatter-gitlab` installed (`npm i -D eslint-formatter-gitlab`)
the `codequality` report shows new and fixed issues in the MR widget, and
the diff gets inline annotations - the same machinery GitLab's own Code
Quality scanner uses.

## The quiet trap: `allow_failure` and `needs`

A job that `needs:` an allowed-to-fail job starts **as soon as it
finishes, green or red**. That is normally what you want (the gate is
advisory) - but make sure such a job does not silently depend on the
failed job's artifacts existing.

## Manual jobs are allowed to fail by default

```yaml
deploy-prod:
  script: ./deploy.sh prod
  when: manual                     # implies allow_failure: true …
  allow_failure: false             # … unless you say otherwise: now the pipeline BLOCKS here
```

Remember this pair from week 3; it is the single most common "why did my
pipeline continue past the manual gate" question.

## Exit codes, once more, with feeling

Every tool in the pipeline talks to GitLab through one integer. Know your
tools' conventions:

| Tool | 0 | 1 | 2+ |
|---|---|---|---|
| `eslint` | clean | problems found | config / crash |
| `jest` | all passed | tests failed | config error |
| `npm audit` | no issues at/above level | vulnerabilities found | - |
| `trivy --exit-code 1` | clean | findings | error |

Design `allow_failure:exit_codes` around those - advisory on "found
something", hard failure on "the tool could not run".

## Self-check

- A job with `allow_failure: true` fails. What colour is the pipeline and
  do later stages run?
- How do you let a linter's findings be advisory but still fail when the
  linter itself crashes?
- A manual deploy job should stop the pipeline until clicked. What two
  keys do you set?
