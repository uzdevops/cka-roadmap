## The pipeline is production code

A job runs with the project's registry, its variables and whatever
credentials you hand it. Anyone who can change `.gitlab-ci.yml` on a ref
that runs with secrets can read those secrets. The protections below keep
that sentence from being true for feature branches and strangers.

## Protected refs, protected variables

- **Protected branches/tags** (*Settings → Repository*): `main` and `v*`
  - who may push (nobody; merge via MR), who may merge (maintainers).
- **Protected variables**: every production secret. Exposed only to jobs
  on protected refs. A feature-branch pipeline that prints `$PROD_TOKEN`
  sees an empty string.
- **Protected environments**: who may deploy to `production`, with
  required approvals.

Together: the only way code reaches a pipeline that can touch production
is through a reviewed MR into a protected branch - and the secrets are not
there until it does.

## Least privilege for tokens

| Token | Lives | Use it for |
|---|---|---|
| `CI_JOB_TOKEN` | one job | registry, package registry, API reads, artifacts of allowed projects; **Job token permissions** lists which projects may use it |
| project / group **access token** | until expiry (set one!) | automation that needs more than the job token, with a role (Reporter/Developer) and scopes |
| **deploy token** | until expiry | read-only pulls from a cluster or server |
| personal access token | a person | never in a pipeline |

Prefer the job token; scope the rest to the minimum role; set expiry on
everything; rotate when someone leaves.

## Approvals and code owners

- **Merge request approvals** (*Settings → Merge requests*): require N
  approvals, reset on new commits, forbid author self-approval.
- **`CODEOWNERS`** in the repo: `/.gitlab-ci.yml @platform-team` - changes
  to the pipeline itself require the platform team's approval. This is the
  single most effective control on CI/CD supply-chain risk.

```text
# CODEOWNERS
/.gitlab-ci.yml       @xyz-team/platform
/ci/                  @xyz-team/platform
/deploy/              @xyz-team/platform @xyz-team/sre
```

## Pipelines for forks and external contributors

A fork's MR runs its pipeline **in the fork** with the fork's (empty)
variables - your secrets never reach it. If maintainers want the parent
project's runners for a fork MR, GitLab asks them to confirm explicitly
("Run pipeline") after reading the diff. Never automate that.

## Audit

Every variable change, protected-branch change, deploy and token creation
is in the **audit events** log (group/instance). Deployment history per
environment shows who pressed what, when, for which commit.

## Checklist for the XYZ pipeline

- [ ] `main` and `v*` protected; direct pushes off
- [ ] production secrets **protected** and **environment-scoped**
- [ ] `production` is a protected environment with approvals
- [ ] `.gitlab-ci.yml` and `ci/` have code owners
- [ ] access tokens have expiry and minimal role; no personal tokens in variables
- [ ] scanners enforced by a group policy, not just by include lines

## Self-check

- A feature branch job echoes a protected variable. What does it print?
- Why is `CODEOWNERS` on `.gitlab-ci.yml` a security control?
- Why does a fork's MR pipeline not see the parent project's variables?
