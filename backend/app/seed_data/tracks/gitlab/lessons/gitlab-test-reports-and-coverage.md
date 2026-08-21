## From log lines to merge request widgets

GitLab can read structured test and coverage output and show it **in the
MR** - which test failed, how coverage changed - without anyone opening a
log. Two artifacts do it: a **JUnit** report and a **coverage** report.

## JUnit test report

Jest needs a reporter that writes JUnit XML:

```bash
npm install --save-dev jest-junit
```

```json
{
  "scripts": {
    "test": "jest --ci --coverage --reporters=default --reporters=jest-junit"
  },
  "jest-junit": { "outputDirectory": "reports", "outputName": "junit.xml" }
}
```

```yaml
unit-tests:
  stage: test
  script:
    - npm ci
    - npm test
  artifacts:
    when: always                       # the report matters MOST when tests fail
    paths:
      - reports/junit.xml
    reports:
      junit: reports/junit.xml
    expire_in: 1 week
```

`artifacts:reports:junit` is the magic key. After the next MR pipeline
the MR page shows a **Test summary** - "6 tests, 1 failed" - and clicking
it names the failing test and its message. The pipeline page gains a
**Tests** tab with every test's duration.

## Coverage from the log

The simplest coverage integration is a regular expression over the job
log. Jest's table has an `All files | 92.15 |` line; tell GitLab where the
number is:

```yaml
unit-tests:
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
```

The first capture group becomes the job's coverage, shown next to the job,
on the MR as **"Coverage 92.15%"** with the delta against the target
branch, and usable in a README badge
(`/badges/main/coverage.svg`). *Settings → CI/CD → General pipelines →
Test coverage parsing* can hold the same regex project-wide.

## Coverage in the diff

For line-level highlighting in the MR diff, publish a **Cobertura** report:

```json
{ "jest": { "coverageReporters": ["text", "cobertura"] } }
```

```yaml
unit-tests:
  artifacts:
    reports:
      junit: reports/junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
```

Now the MR diff marks each changed line green/red by whether a test
touched it - the fastest way to see a change shipped without a test.

## Archive the rest

Keep the human-readable HTML report too - reviewers like it, and it costs
nothing once the job already produced it:

```yaml
  artifacts:
    paths:
      - reports/
      - coverage/               # includes lcov-report/index.html
```

**Browse** on the job page opens `coverage/lcov-report/index.html` right
in the browser.

## Self-check

- Which artifact key turns test results into an MR widget?
- Why must the report artifact use `when: always`?
- What is the difference between the `coverage:` regex and a
  `coverage_report`?
