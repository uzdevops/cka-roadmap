## Why this track exists

Meet the XYZ team. They have a Node.js application, a handful of developers,
and a release process that lives in one engineer's head: pull the code,
run the tests by hand, build an image, copy it to a server, hope. Every
release takes an afternoon and every second release breaks something that
the tests would have caught - if anyone had run them.

That is the **problem statement** this whole track works against. By the
end of it the same team has a pipeline that runs on every push, tests
every change, builds and publishes an image, deploys to staging on its
own and to production on a button - and does all of that in a few minutes,
the same way every time.

## What CI/CD actually means

- **Continuous Integration** - every change is merged often and verified
  automatically: build, unit tests, linting, security checks. The goal is
  that `main` is always in a known-good state.
- **Continuous Delivery** - every verified change is *deployable*: packaged,
  versioned and pushed through staging automatically, with a human deciding
  when it reaches production.
- **Continuous Deployment** - the human is removed from that last step too:
  a green pipeline on `main` *is* a production release.

GitLab CI/CD covers all three with one file in your repository:

```yaml
# .gitlab-ci.yml - the entire pipeline lives next to the code it builds
stages: [test, build, deploy]

unit-tests:
  stage: test
  image: node:20-alpine
  script:
    - npm ci
    - npm test
```

Commit that file and GitLab runs it. No server to set up, no separate
configuration UI to click through - the pipeline is versioned, reviewed
and rolled back exactly like the application code.

## How the track is built

| Weeks | Phase | You will be able to |
|---|---|---|
| 1-2 | Foundations | explain runners, stages, jobs and artifacts, and write a multi-job pipeline |
| 3 | Pipeline configuration | control *when* and *how* jobs run: variables, rules, schedules, matrices |
| 4-5 | Continuous integration | test, report on, build and publish the XYZ Node.js application |
| 6 | Continuous deployment | deploy to environments with manual gates, review apps and Kubernetes |
| 7 | Optimisation & security | make pipelines fast, modular and safe - caching, child pipelines, scanning |
| 8 | Runners & Auto DevOps | run your own runners and let GitLab generate a pipeline for you |

Each week: five lessons, one lab that you run against a real GitLab
project, and a review quiz. Keep a GitLab project open in a second tab
from day one - every YAML snippet in this track is meant to be pasted
and run, not read.

## Self-check

- In one sentence each: what is the difference between continuous
  delivery and continuous deployment?
- Where does a GitLab pipeline definition live, and why is that a good thing?
