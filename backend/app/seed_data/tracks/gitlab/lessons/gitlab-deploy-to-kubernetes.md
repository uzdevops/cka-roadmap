## Two ways to reach a cluster

A pipeline deploys to Kubernetes either by **pushing** (the job runs
`kubectl`/`helm` with credentials) or by **pulling** (an agent in the
cluster watches the repo - GitOps with Flux/Argo CD, outside this track's
scope). GitLab's push path has two flavours.

## A: kubeconfig as a File variable (quick, explicit)

```yaml
deploy-staging:
  stage: deploy
  image: bitnami/kubectl:1.30
  environment: { name: staging, url: https://staging.xyz.example.com }
  variables:
    KUBECONFIG: "$KUBECONFIG_FILE"          # File-type variable: a path
    IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
  script:
    - kubectl config current-context
    - kubectl -n xyz set image deployment/nodejs-app app="$IMAGE"
    - kubectl -n xyz rollout status deployment/nodejs-app --timeout=120s
```

Works anywhere, needs a cluster reachable from the runner, and puts a
credential in a variable - scope it to the environment, protect it, and
prefer a short-lived service-account token over an admin kubeconfig.

## B: the GitLab agent for Kubernetes (recommended)

The **agent** (`agentk`) runs *inside* the cluster and keeps an outbound
connection to GitLab; pipelines then reach the cluster through GitLab with
no inbound firewall hole and no kubeconfig to leak.

1. In the cluster's config repo: `.gitlab/agents/<name>/config.yaml`
   ```yaml
   ci_access:
     projects:
       - id: xyz-team/nodejs-app        # which projects' pipelines may use this agent
   ```
2. *Operate → Kubernetes clusters → Connect a cluster (agent)* - gives you
   a `helm upgrade --install` command that deploys `agentk` with a token.
3. In the app pipeline, select the agent's context and deploy:

```yaml
deploy-staging:
  image: bitnami/kubectl:1.30
  environment: { name: staging, url: https://staging.xyz.example.com }
  script:
    - kubectl config use-context xyz-team/infra:staging-agent     # <project>:<agent name>
    - kubectl -n xyz set image deployment/nodejs-app app="$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
    - kubectl -n xyz rollout status deployment/nodejs-app
```

`KUBECONFIG` is injected by GitLab for jobs with access to the agent; the
only thing you write is `use-context`.

## Helm instead of `set image`

```yaml
deploy-staging:
  image: alpine/helm:3.15
  script:
    - kubectl config use-context xyz-team/infra:staging-agent
    - helm upgrade --install nodejs-app ./chart
        --namespace xyz --create-namespace
        --set image.repository="$CI_REGISTRY_IMAGE"
        --set image.tag="$CI_COMMIT_SHORT_SHA"
        --wait --timeout 3m
```

`--wait` makes the job's exit code mean "pods are ready", which is the
deploy-time health check in one flag. Pair with `environment:url` and
`kubectl rollout undo` (or `helm rollback`) for the rollback button.

## Image pull from the GitLab registry

The cluster needs credentials to pull `registry.gitlab.com/...`. Create a
**deploy token** (*Settings → Repository → Deploy tokens*, read_registry)
and a pull secret:

```bash
kubectl -n xyz create secret docker-registry gitlab-registry \
  --docker-server=registry.gitlab.com --docker-username=<token user> --docker-password=<token> \
  --docker-email=ci@xyz.example.com
# then imagePullSecrets: [{name: gitlab-registry}] in the Deployment
```

## Self-check

- What does the agent remove from the pipeline compared with a kubeconfig variable?
- Which line in a job selects the cluster when using an agent?
- Why `helm --wait` / `kubectl rollout status` rather than just `apply`?
