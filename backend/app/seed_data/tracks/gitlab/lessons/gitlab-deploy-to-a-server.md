## The simplest real deployment

The XYZ team's dev server is a single Linux VM running Docker. Deploying
means: SSH in, pull the image, restart the container. That is four lines -
and a handful of things to get right around them.

## 1. Credentials: an SSH key as a File variable

Generate a deploy key on your machine, put the **public** half in the
server's `~deploy/.ssh/authorized_keys`, and store the **private** half as
a project variable `SSH_PRIVATE_KEY` of type **File**, *protected* and
*masked off* (a multi-line key cannot be masked - protection and scope are
what guard it).

```bash
ssh-keygen -t ed25519 -N '' -f deploy_key -C "gitlab-ci xyz-team"
ssh-copy-id -i deploy_key.pub deploy@dev.xyz.example.com
```

Also store `SSH_KNOWN_HOSTS` (File) with the output of
`ssh-keyscan dev.xyz.example.com`, so the job **verifies** the host instead
of blindly accepting - `StrictHostKeyChecking=no` in a pipeline is how a
man-in-the-middle gets your deploy credentials.

## 2. The job

```yaml
deploy-dev:
  stage: deploy
  image: alpine:3.20
  environment:
    name: dev
    url: http://dev.xyz.example.com:3000
  variables:
    IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
  before_script:
    - apk add --no-cache openssh-client
    - chmod 600 "$SSH_PRIVATE_KEY"                      # File variable = a path
    - mkdir -p ~/.ssh && cp "$SSH_KNOWN_HOSTS" ~/.ssh/known_hosts
  script:
    - |
      ssh -i "$SSH_PRIVATE_KEY" deploy@dev.xyz.example.com "
        set -e
        echo '$CI_REGISTRY_PASSWORD' | docker login -u '$CI_REGISTRY_USER' --password-stdin '$CI_REGISTRY'
        docker pull '$IMAGE'
        docker rm -f nodejs-app || true
        docker run -d --name nodejs-app --restart unless-stopped -p 3000:3000 '$IMAGE'
        docker logout '$CI_REGISTRY'
      "
    - sleep 3 && wget -qO- "$CI_ENVIRONMENT_URL/healthz"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

Read the quoting carefully: the outer `"…"` is expanded **by the job**
before SSH, so `$IMAGE` and the registry variables reach the server as
values; the server never needs a long-lived token - it logs in with the
job's token for the length of one pull and logs out.

## 3. Manual gates

Dev deploys on every `main` commit. Staging should wait for a human:

```yaml
deploy-staging:
  extends: deploy-dev
  environment: { name: staging, url: https://staging.xyz.example.com }
  variables: { DEPLOY_HOST: staging.xyz.example.com }     # …and use $DEPLOY_HOST in the ssh line
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
      allow_failure: false        # block the pipeline here until somebody clicks
```

In the pipeline view the job shows a ▶ button; the environment page
shows it too. Who may press it is decided by the next lesson's
**protected environments**.

## Secrets hygiene checklist

- Key is a File variable, protected, scoped to the environment.
- Host key is verified (`known_hosts`), never `StrictHostKeyChecking=no`.
- The server logs in to the registry with the job token, then logs out.
- `set -e` inside the remote script, so a failed pull stops the restart.
- The job ends with a health check against `$CI_ENVIRONMENT_URL`.

## Self-check

- Why is the private key a *File*-type variable, and what is in `$SSH_PRIVATE_KEY`?
- What does `SSH_KNOWN_HOSTS` protect against?
- Which two keys turn a deploy job into a blocking manual gate?
