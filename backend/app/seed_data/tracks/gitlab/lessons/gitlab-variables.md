## Variables at every level

A CI/CD variable is an environment variable the runner sets before your
`script` runs. The same name can be defined in several places; the most
specific one wins.

```text
instance  ─► group ─► project ─► pipeline (run pipeline form / API / schedule)
                                   ─► .gitlab-ci.yml  variables:  (global)
                                        ─► job-level variables:
                                             ─► exported inside script
   least specific ───────────────────────────────────────► most specific
```

```yaml
variables:                       # global - every job sees these
  NODE_ENV: test
  DEPLOY_REGION: eu-central-1

build:
  variables:
    NODE_ENV: production         # job-level overrides global for this job
  script:
    - echo "$NODE_ENV in $DEPLOY_REGION"
    - export BUILD_ID="$CI_PIPELINE_IID-$CI_COMMIT_SHORT_SHA"
    - echo "$BUILD_ID"
```

Project, group and instance variables are set in the UI (*Settings →
CI/CD → Variables*) and **never appear in the repository** - which is the
whole point: the YAML says `$DB_PASSWORD`, the value lives in GitLab, and
the same file deploys to three customers with three different project
variables.

## Variable options in the UI

Each UI variable has four switches that matter:

| Option | Effect |
|---|---|
| **Type: Variable / File** | *File* writes the value to a temp file and puts its **path** in the variable - the right shape for a kubeconfig, an SSH key, a `.npmrc` |
| **Protect variable** | only exposed to pipelines on **protected** branches/tags - a production secret never reaches a feature-branch job |
| **Mask variable** | the value is replaced with `[MASKED]` in job logs (next section) |
| **Expand variable reference** | whether `$OTHER_VAR` inside the value is resolved |
| **Environment scope** | `*`, `production`, `review/*` - the same name with different values per environment (week 6) |

```yaml
deploy:
  script:
    - ssh -i "$SSH_PRIVATE_KEY" deploy@server 'echo hi'   # File-type variable: a path
    - kubectl --kubeconfig="$KUBECONFIG_FILE" get nodes
```

## Masking - and its limits

Masking is a **log filter**, not encryption: the runner replaces any
occurrence of the value with `[MASKED]` before the line is streamed. For it
to work the value must be a single line, 8+ characters, and from a
restricted character set - the UI refuses to mask anything else.

Masking does not stop a job from `echo`-ing a secret in pieces, base64-ing
it, or uploading it as an artifact. Treat it as a seatbelt: always on,
never the thing that keeps you safe. Protection and scoping are what keep
a secret from the wrong pipeline in the first place.

## Precedence bites

```yaml
variables:
  TARGET: staging

deploy-prod:
  variables:
    TARGET: production
  script: echo "$TARGET"        # production
```

Now someone sets a **project** variable `TARGET=dev` in the UI. Job-level
YAML still wins over project-level UI - the *YAML file* is more specific
than the project. But a value typed into the **Run pipeline** form or sent
by the API beats everything in the file. Remember the ladder; when a
variable "has the wrong value", walk it.

## Self-check

- A secret must be available to `main` deploys but not to feature-branch
  jobs. Which switch?
- What does a *File*-type variable actually put in `$VAR`?
- A job-level `variables:` entry and a project variable share a name. Which
  value does `script` see?
