## Building an image inside a pipeline

The `build` stage turns the tested code into a container image. The job
needs a Docker daemon to talk to, and a job on a `docker` executor is
*itself* a container - so where does the daemon come from? Three answers,
in order of how often you will use them.

## 1. Docker-in-Docker (`dind`) as a service

```yaml
build-image:
  stage: build
  image: docker:27
  services:
    - docker:27-dind
  variables:
    DOCKER_HOST: tcp://docker:2376          # the service's hostname
    DOCKER_TLS_CERTDIR: "/certs"            # dind generates certs here…
    DOCKER_TLS_VERIFY: 1                    # …and the client verifies them
    DOCKER_CERT_PATH: "/certs/client"
  before_script:
    - docker info                           # proves the daemon is reachable
  script:
    - docker build --pull -t "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA" .
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_COMMIT_TAG
```

The `docker:27-dind` service runs a real daemon next to the job; the
`docker:27` image gives the job the CLI. It needs the runner to allow
**privileged** containers - the gitlab.com shared runners do; a
self-managed docker runner needs `privileged = true` in its `config.toml`
(week 8). The three TLS variables are not decoration: without them the
client and daemon fail to agree on a socket and you get the classic
*"Cannot connect to the Docker daemon at tcp://docker:2375"*.

## 2. Kaniko - no daemon, no privilege

```yaml
build-image:
  stage: build
  image:
    name: gcr.io/kaniko-project/executor:v1.23.2-debug
    entrypoint: [""]
  script:
    - /kaniko/executor
        --context "$CI_PROJECT_DIR"
        --dockerfile "$CI_PROJECT_DIR/Dockerfile"
        --destination "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
```

Kaniko builds and pushes in userspace; it reads registry credentials from
`/kaniko/.docker/config.json`, which on GitLab you can populate with the
predefined registry variables (next lesson). Pick kaniko (or buildah) when
privileged containers are not allowed - common in regulated environments
and on Kubernetes executors.

## 3. The shell executor's own daemon

On a self-managed `shell` runner the job simply runs `docker build` against
the host daemon. Simple, fast (layer cache survives between jobs), and the
least isolated: every job can see and remove every other job's containers.
Fine for one team's box, wrong for a shared fleet.

## Make the build reproducible and quick

```dockerfile
# Dockerfile - XYZ nodejs-app
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev

FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
USER node
CMD ["node", "server.js"]
```

- `COPY package*.json` **before** `COPY . .` so the dependency layer is
  cached as long as the lock file does not change.
- `--pull` on `docker build` so the base image is refreshed.
- `--cache-from "$CI_REGISTRY_IMAGE:latest"` (with `BUILDKIT_INLINE_CACHE=1`)
  lets a fresh dind daemon reuse layers from the last pushed image - the
  dind cure for "every job starts with an empty cache".

## Self-check

- Why does a `docker` executor job need a `dind` service to run `docker build`?
- Name the three TLS-related variables and what goes wrong without them.
- When would you choose kaniko over dind?
