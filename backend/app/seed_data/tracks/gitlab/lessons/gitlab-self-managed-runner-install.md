## When the shared runners are not enough

Reasons the XYZ team installs its own runner: jobs need to reach a
private network (the dev server, an internal registry), compute minutes
on SaaS are running out, builds need a GPU or a big cache, or policy says
code may not execute on someone else's VM. The YAML does not change; only
where it runs does.

## Install `gitlab-runner`

On a Linux host (Ubuntu/Debian shown; RPM and binaries exist):

```bash
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash
sudo apt-get install gitlab-runner
sudo gitlab-runner --version
```

This creates a `gitlab-runner` system user and a systemd service. The
runner needs **Docker** for the `docker` executor:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker gitlab-runner
```

## Register it

In GitLab, create the runner first - *Settings → CI/CD → Runners → New
project runner* (or group / instance) - choose tags, "run untagged jobs"
if you want, and copy the **authentication token** (`glrt-…`). Then:

```bash
sudo gitlab-runner register \
  --non-interactive \
  --url https://gitlab.com \
  --token glrt-XXXXXXXXXXXXXXXXXXXX \
  --executor docker \
  --docker-image alpine:3.20 \
  --description "xyz-build-01"
```

The runner appears **online** within seconds. Registration writes a
`[[runners]]` block to `/etc/gitlab-runner/config.toml` (next lesson); the
service picks it up automatically.

> The old flow - a *registration* token shared across runners - is
> deprecated. Create each runner in the UI and register with its own
> authentication token; that is also what makes the token revocable per
> runner.

## Tags: routing jobs to runners

A runner with tags `docker`, `linux`, `internal` only takes jobs that
request a subset of them (unless "run untagged" is on). Jobs ask with
`tags:`:

```yaml
deploy-dev:
  tags: [internal]            # must run on the runner that can see the dev server
  script: ./deploy.sh dev

unit-tests:
  tags: [docker, linux]       # any of the team's docker runners
  script: npm test
```

Untagged jobs go to runners that accept untagged work - on gitlab.com,
that is the shared fleet. Make your private runner **tagged and
untagged-off**, or every job in the project will land on it.

## Scope and who may use it

- **Project runner**: only this project.
- **Group runner**: the group's projects - the usual choice for a team.
- **Instance runner**: everyone (self-managed GitLab only, admin).

A runner can be **paused** (takes no new jobs), **locked** to its project,
and **protected** (runs jobs only from protected refs - pair with
production deploy runners).

## Self-check

- What is the difference between the runner's *scope* and its *tags*?
- Why should a private runner not accept untagged jobs?
- What makes the new authentication-token registration better than the old shared token?
