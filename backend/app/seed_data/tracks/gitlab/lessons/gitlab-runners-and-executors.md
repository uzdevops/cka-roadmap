## Who runs your job

A **runner** is a process - `gitlab-runner` - that polls GitLab over HTTPS,
asks "any jobs for me?", receives one, executes it, and streams the log
back. GitLab never pushes to a runner; the runner pulls. That is why a
runner can sit behind a NAT in your office and still serve gitlab.com.

Runners are registered at one of three scopes, and a job is offered to
every runner whose scope includes the project:

| Scope | Registered at | Typical use |
|---|---|---|
| **instance** (shared) | the whole GitLab instance | gitlab.com's SaaS runners; your company's default fleet |
| **group** | a group and all its projects | a team's own machines, shared across its repos |
| **project** | one project | a special box - GPU, a licence, a deploy host |

On gitlab.com the **shared runners** are enabled per project under
*Settings → CI/CD → Runners*. They are Linux VMs (with Windows and macOS
variants) created per job and destroyed afterwards - which is the strongest
isolation a runner can offer and the reason a job can never "leave
something behind" for the next one.

## Executors - how a job is isolated

The runner decides *where* a job is offered; its **executor** decides
*how* the job's shell is created.

| Executor | A job runs in | When you would pick it |
|---|---|---|
| `shell` | a shell on the runner host itself | one machine, trusted jobs, tools already installed |
| `docker` | a fresh container from `image:` | the default - clean, reproducible, any toolchain |
| `docker+machine` / autoscaler | a container on a VM created for the job | the SaaS runners; big fleets |
| `kubernetes` | a Pod in a cluster | you already operate Kubernetes |
| `ssh`, `virtualbox`, `parallels`, `custom` | a remote host / VM / your own script | edge cases |

The executor is a property of the runner, not of the job: you cannot ask
for `docker` from the YAML. What you *can* do - and must, on `docker` -
is choose the **image**:

```yaml
job-on-node:
  image: node:20-alpine      # the container this job's shell starts in
  script: node --version

job-on-python:
  image: python:3.12-slim
  script: python --version
```

With the `shell` executor `image:` is ignored and both jobs would run
whatever `node`/`python` the host happens to have - the most common reason
a pipeline behaves differently on a self-managed runner than on gitlab.com.

## The SaaS architecture, end to end

```text
developer ──push──► gitlab.com ──job queued──► runner manager (GitLab-owned)
                                                 │ creates VM, starts docker
                                                 ▼
                                          ephemeral VM ── runs job in `image`
                                                 │ streams log, uploads artifacts
                                                 ▼
                                             destroyed
```

Consequences you will meet this week: pulls of big images cost time on
every job (VM is new → no image cache); anything installed in `script` is
gone by the next job; network egress from the VM is what your job sees as
"the internet".

## Self-check

- A project in group `xyz-team` has one project runner and the group has
  two. How many runners can pick up its jobs (ignoring shared ones)?
- Why does `image:` change nothing on a `shell` executor?
- Why is an image pulled again on every SaaS job?
