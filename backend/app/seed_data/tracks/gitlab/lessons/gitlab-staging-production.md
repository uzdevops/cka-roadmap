## The promotion path

```text
main commit ──► deploy-dev (auto) ──► deploy-staging (manual) ──► deploy-prod (manual, protected)
tag v1.4.0  ───────────────────────► deploy-staging (auto)   ──► deploy-prod (manual, protected)
```

One image, built once, **promoted** by SHA through three environments.
Two of the three are gated; the last one is also *guarded*: only certain
people may press the button, and only from certain refs.

## Protected environments

*Settings → CI/CD → Protected environments*: pick `production`, choose
**who can deploy** (a group, a role, specific users) and optionally
**required approvals** (N people must approve the deployment before the
job can even be played). A job targeting a protected environment from an
unprotected branch is **blocked** - which closes the hole where a feature
branch pipeline could "deploy to production" because its YAML said so.

Pair this with a **protected branch** `main` (*Settings → Repository →
Protected branches*: nobody pushes directly, merges need an MR with a
green pipeline) and protected tags `v*`. Protected variables - the
production secrets - are then only exposed to pipelines on those refs.

## Production job

```yaml
deploy-prod:
  extends: .deploy
  environment:
    name: production
    url: https://xyz.example.com
  variables: { DEPLOY_HOST: prod.xyz.example.com }
  resource_group: production
  rules:
    - if: $CI_COMMIT_TAG
      when: manual
      allow_failure: false
```

Production deploys only from **tags** - an explicit "this is a release"
act, with a name you can read in the environment history - while `main`
feeds dev and staging continuously.

## Rollback and re-deploy

*Operate → Environments → production* lists every deployment. **Rollback**
on an older row re-runs that deployment's job with **its** commit and
image - it is not a new pipeline, it is the old one replayed, which is why
deploying by immutable SHA matters: the rollback deploys exactly what was
live then.

The other rollback is a forward one - revert the commit, let the pipeline
run. Prefer it when the bad change was in code; prefer the button when you
need the old version back *now* and will investigate after.

## Safety valves

| Problem | Keyword / setting |
|---|---|
| two deploys to production at once | `resource_group: production` |
| a deploy that should wait, say, 10 minutes after staging | `when: delayed` + `start_in: 10 minutes` |
| a stuck deploy holding the runner | `timeout: 15 minutes` |
| the wrong person pressing play | protected environment + approvals |
| a deploy from a feature branch | protected environment + protected branches/tags |

```yaml
deploy-prod:
  when: delayed
  start_in: 10 minutes          # a bake window after staging; cancellable from the UI
```

## Self-check

- What stops a feature-branch pipeline from deploying to `production` even if its YAML has such a job?
- Why does Rollback need immutable image tags to be trustworthy?
- Which mechanism makes "N people must approve before production" a rule rather than a habit?
