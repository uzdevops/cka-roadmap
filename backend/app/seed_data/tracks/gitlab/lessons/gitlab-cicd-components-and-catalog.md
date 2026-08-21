## `include:` with a contract

`include:project` (week 5) shares YAML, but the consumer has no idea what
variables the template expects, and a variable typo fails at run time.
**CI/CD components** add the missing piece: a template with a declared
**spec** of inputs, published to a **catalog**, included by version.

## Writing a component

A component project is an ordinary GitLab project with this layout:

```text
ci-components/
├── templates/
│   └── node-test/
│       └── template.yml
└── README.md
```

```yaml
# templates/node-test/template.yml
spec:
  inputs:
    node_version:
      default: "20"
      description: Node.js major version
    stage:
      default: test
    coverage_regex:
      default: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
---
"$[[ inputs.stage ]]-node":
  stage: $[[ inputs.stage ]]
  image: node:$[[ inputs.node_version ]]-alpine
  script:
    - npm ci
    - npm test
  coverage: $[[ inputs.coverage_regex ]]
  artifacts:
    reports: { junit: reports/junit.xml }
```

Everything above `---` is the contract; below it, plain pipeline YAML with
`$[[ inputs.x ]]` substituted **at include time** - unknown inputs and
type mismatches fail the pipeline *creation*, with a message naming the
input. Tag the project (`1.0.0`, `1.1.0`) - tags are the versions.

## Using it

```yaml
include:
  - component: gitlab.com/xyz-team/ci-components/node-test@1.1.0
    inputs:
      node_version: "22"
      stage: verify
```

`@1.1.0` pins an exact release; `@~latest` follows the newest; `@main`
tracks a branch (for development only). A **CI/CD Catalog** entry
(*Settings → General → Visibility → CI/CD Catalog project*) makes the
component discoverable under *Explore → CI/CD Catalog* with its README and
inputs rendered.

## Inputs are not variables

| | `spec:inputs` | CI/CD variables |
|---|---|---|
| resolved | when the pipeline is created, in the YAML | when the job runs, in the shell |
| typed / validated | yes (string, number, boolean, array, options) | no |
| can change job names, stages, rules | yes | no |
| visible to `script:` | only where you wrote them in | yes, as `$VAR` |

Use inputs for **structure** (which stage, which image, how many shards),
variables for **runtime values** (credentials, hosts, toggles).

## Migrating the XYZ pipeline

The `.node` template, the docker-build job and the SSH deploy job from
weeks 5-6 are the three components the team publishes first. The app's
`.gitlab-ci.yml` shrinks to `include:` lines plus the deploy `rules:` -
and a security fix in the build component ships to every project with a
version bump, not a dozen MRs.

## Self-check

- When are `$[[ inputs.x ]]` substituted, and what happens with an unknown input?
- What does the version after `@` refer to?
- Give one thing inputs can do that variables cannot.
