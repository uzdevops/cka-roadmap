# Kubernetes manifests

Production-shaped manifests for the same two images `docker compose` builds.
They are also a decent CKA practice target: a StatefulSet with a PVC, a
migration Job, probes, an HPA, a PDB, an Ingress and a NetworkPolicy.

## What is here

| File | Contains |
| --- | --- |
| `00-namespace.yaml` | Namespace with the `restricted` Pod Security Standard enforced |
| `01-config.yaml` | ConfigMap (non-secret config) + Secret (credentials, demo accounts) |
| `02-postgres.yaml` | Headless Service + StatefulSet with a `volumeClaimTemplate` |
| `03-migrate-job.yaml` | Runs `alembic upgrade head` + the idempotent seed, once |
| `04-backend.yaml` | Deployment, ClusterIP Service, PodDisruptionBudget, HPA |
| `05-frontend.yaml` | Deployment, ClusterIP Service, PodDisruptionBudget |
| `06-ingress.yaml` | Ingress (path split) + NetworkPolicy for the database |
| `kustomization.yaml` | Applies everything in order and pins image tags |

## Deploying to a local cluster

```bash
# 1. Build the images (identical to what compose builds)
docker build -t cka-prep-backend:latest ./backend
docker build -t cka-prep-frontend:latest \
  --build-arg NEXT_PUBLIC_API_URL=https://cka.example.com ./frontend

# 2. Make them reachable from the cluster
kind load docker-image cka-prep-backend:latest cka-prep-frontend:latest --name cka
#   ... or: minikube image load cka-prep-backend:latest

# 3. Replace the placeholder secrets
kubectl create namespace cka-prep --dry-run=client -o yaml | kubectl apply -f -
kubectl -n cka-prep create secret generic cka-prep-secrets \
  --from-literal=POSTGRES_USER=cka \
  --from-literal=POSTGRES_PASSWORD="$(openssl rand -base64 24)" \
  --from-literal=SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=GOOGLE_CLIENT_ID="" \
  --from-literal=GOOGLE_CLIENT_SECRET="" \
  --from-literal=DEMO_STUDENT_EMAIL=student@demo.local \
  --from-literal=DEMO_STUDENT_PASSWORD='DemoPass123!' \
  --from-literal=DEMO_ADMIN_EMAIL=admin@demo.local \
  --from-literal=DEMO_ADMIN_PASSWORD='AdminPass123!' \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Apply
kubectl apply -k k8s/
#   (the Secret above wins because kubectl apply merges by name)

# 5. Watch it come up
kubectl -n cka-prep get pods -w
kubectl -n cka-prep logs job/cka-migrate
```

## Before deploying anywhere real

1. **Set the hostname.** `cka.example.com` appears in `01-config.yaml`
   (`FRONTEND_ORIGIN`, `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SITE_URL`, the OAuth
   URLs) and in `06-ingress.yaml`. `NEXT_PUBLIC_API_URL` is compiled into the
   client bundle, so changing it means rebuilding the frontend image, not just
   editing the ConfigMap.
2. **Replace every `CHANGE_ME`.** The committed Secret is a placeholder. Use
   External Secrets, Sealed Secrets or SOPS rather than committing real values.
3. **Reconsider the database.** The StatefulSet is durable across Pod restarts
   but is a single replica: no failover, no PITR. For production use a managed
   Postgres or an operator such as CloudNativePG, then delete
   `02-postgres.yaml` and point `POSTGRES_HOST` at the managed endpoint.
4. **Rotate the demo accounts.** The seed creates `student@demo.local` and
   `admin@demo.local` with known passwords. Change them in the Secret, or set
   `SEED_ON_START=false` on the Job and seed content another way.
5. **Install metrics-server**, or the HPA will sit at `<unknown>/70%`.

## Design notes

**Migrations run in a Job, not in the app Pods.** The container entrypoint
migrates and seeds by default, which is what makes `docker compose up` a single
command. On Kubernetes that would mean every replica racing on the same DDL, so
the Deployments set `RUN_MIGRATIONS=false` and `SEED_ON_START=false`, and
`03-migrate-job.yaml` does the work once. The Job passes `true` as its command:
the entrypoint waits for the database, migrates, seeds, then execs `true`.

**Probes are split by meaning.** `/healthz` is liveness and never touches the
database - restarting a Pod because Postgres blipped would turn a database
outage into a cluster-wide restart storm. `/readyz` is readiness and does check
the database, so traffic drains from a Pod that cannot serve. The frontend's
`/readyz` checks the backend for the same reason.

**maxUnavailable: 0.** Rollouts add a Pod before removing one, so capacity
never dips. Combined with the readiness probes, a broken image stalls the
rollout instead of taking the service down.

**readOnlyRootFilesystem.** Both app containers run with a read-only root and
an `emptyDir` at `/tmp` (plus `/app/.next/cache` for Next.js). Postgres needs a
writable data directory, so it is the one exception.
