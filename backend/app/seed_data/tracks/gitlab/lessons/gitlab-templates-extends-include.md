## The same six lines, eight times

By now `nodejs-app/.gitlab-ci.yml` repeats `image: node:20-alpine`, the
cache block and `npm ci` in every job. Three tools remove the repetition,
in increasing power: YAML anchors, `extends`, `include`.

## Hidden jobs and `extends`

A job whose name starts with `.` is **not run** - it is a template. Other
jobs inherit it with `extends:` (a deep merge: maps merge, lists are
replaced):

```yaml
.node:
  image: node:20-alpine
  cache:
    key: { files: [package-lock.json] }
    paths: [.npm/]
    policy: pull
  before_script:
    - npm ci --prefer-offline

lint:
  extends: .node
  stage: test
  script: npm run lint

unit-tests:
  extends: .node
  stage: test
  script: npm test
  artifacts:
    reports: { junit: reports/junit.xml }
```

`extends` can take a list (`extends: [.node, .on-mr]`) - later entries
override earlier ones. Use `extends` for everything you would have
copy-pasted; it reads as intent ("this is a node job").

## `default:` for the truly global

```yaml
default:
  image: node:20-alpine
  interruptible: true            # cancel me if a newer pipeline starts (week 7)
  retry:
    max: 1
    when: [runner_system_failure, stuck_or_timeout_failure]
```

`default:` applies to every job that does not override the key. Good for
`image`, `retry`, `interruptible`, `tags`; bad for `script` (jobs are too
different).

## YAML anchors - when you only need plain YAML

```yaml
.cache-node: &cache-node
  key: { files: [package-lock.json] }
  paths: [.npm/]

unit-tests:
  cache: *cache-node
```

Anchors are pure YAML, resolved before GitLab sees the file, and cannot
cross `include` boundaries. Prefer `extends` in GitLab YAML; reach for an
anchor only for a fragment that is not a whole job.

## `include:` - pipelines made of files

```yaml
include:
  - local: ci/test.yml                      # same repo
  - local: ci/deploy.yml
  - project: xyz-team/ci-templates         # another project in the instance
    ref: v2.1.0                            # pin it!
    file: /templates/docker-build.yml
  - remote: https://example.com/ci/lint.yml
  - template: Security/SAST.gitlab-ci.yml  # shipped with GitLab
```

Included files are merged into one configuration; the **Full
configuration** tab in the pipeline editor shows the result, which is
where you debug "where does this job come from". A project of templates
(`ci-templates`) with versioned refs is how a platform team gives twenty
repos one `docker-build` job and upgrades them deliberately, not
accidentally. Week 7 turns this into **CI/CD components** with typed
inputs.

## `!reference` - reuse a fragment

```yaml
.setup:
  script:
    - echo "setting up"

deploy:
  script:
    - !reference [.setup, script]
    - ./deploy.sh
```

Unlike `extends`, `!reference` splices a specific key's value into a
list - the tool for "run these lines *and* mine".

## Self-check

- Two jobs extend `.node`; one sets its own `before_script`. Does the
  template's run too?
- What does the Full configuration tab show that the file itself does not?
- Why pin `ref:` on a `project:` include?
