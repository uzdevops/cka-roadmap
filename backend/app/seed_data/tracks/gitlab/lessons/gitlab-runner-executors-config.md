## `config.toml`, the file that matters

```toml
# /etc/gitlab-runner/config.toml
concurrent = 4                      # jobs this host runs at once, across all [[runners]]
check_interval = 3
log_level = "warning"

[[runners]]
  name = "xyz-build-01"
  url = "https://gitlab.com"
  token = "glrt-…"
  executor = "docker"
  limit = 4                         # max concurrent jobs for THIS runner entry
  environment = ["DOCKER_TLS_CERTDIR=/certs"]
  [runners.cache]
    Type = "s3"                     # shared cache across runners (optional)
    Shared = true
    [runners.cache.s3]
      ServerAddress = "minio.internal:9000"
      BucketName = "runner-cache"
      Insecure = true
  [runners.docker]
    image = "alpine:3.20"           # default image when the job sets none
    privileged = true               # needed for docker:dind services
    volumes = ["/cache", "/certs/client"]
    pull_policy = ["if-not-present", "always"]
    shm_size = 0
```

Edit, then `sudo gitlab-runner restart` (or it reloads on change). Keys
worth knowing:

| Key | Why you would touch it |
|---|---|
| `concurrent` | total parallelism of the host - CPU/RAM bound |
| `limit` | cap one runner entry (e.g. a deploy runner at 1) |
| `privileged` | `docker:dind` needs it; it is root on the host - only for trusted projects |
| `volumes` | persistent `/cache`; mounting `/var/run/docker.sock` is the *other* way to give jobs docker (shared daemon, no dind) |
| `pull_policy` | `if-not-present` keeps images local between jobs - big speed-up; `always` for images that move |
| `[runners.cache]` | move cache off the host so every runner sees it |

## Choosing the executor

| Executor | Isolation | Speed | Notes |
|---|---|---|---|
| `shell` | none - jobs share the host user | fastest, caches everything | only for one trusted team; `gitlab-runner` user needs the tools |
| `docker` | container per job | image pulls cost; cache via volumes | the default choice |
| `docker` + socket mount | container per job, **shared** daemon | fast builds (layer cache) | jobs can see each other's containers |
| `docker` + dind service | container per job, daemon per job | slower builds | clean, needs `privileged` |
| `kubernetes` | Pod per job | scales with the cluster | config via `[runners.kubernetes]`; the cluster needs image pull creds |
| `docker-autoscaler` / `instance` | VM per job (fleeting plugin) | elastic | replaces docker+machine |

## Operating it

```bash
sudo gitlab-runner list                 # registered runners on this host
sudo gitlab-runner verify               # can each one reach GitLab?
sudo gitlab-runner status
sudo journalctl -u gitlab-runner -f     # the runner's own log (not job logs)
sudo gitlab-runner unregister --name xyz-build-01
```

Upgrade the runner with the package manager; keep it within one or two
minor versions of the GitLab server. Put `gitlab-runner` behind a proxy
with `environment = ["HTTPS_PROXY=…"]` if the host has no direct egress.

## A deploy runner, done properly

One runner entry, `limit = 1`, tag `deploy`, **protected** (only protected
refs), `executor = "shell"` on a hardened host that holds the SSH keys or
kubeconfig as files - and *no* secrets in GitLab variables at all. Jobs
on it `tags: [deploy]` and are `resource_group`-ed. The blast radius of a
compromised feature branch is zero.

## Self-check

- `concurrent = 4` and a runner with `limit = 1` - how many deploy jobs run at once? How many total jobs?
- What is the trade-off between dind and mounting the docker socket?
- Why `pull_policy = ["if-not-present", "always"]` in that order?
