# CKA Prep

A learning platform for the **Certified Kubernetes Administrator** exam: a
20-week roadmap, written lessons, server-graded quizzes, hands-on labs and a
progress dashboard whose readiness estimate is weighted by the real exam
domains.

## Quickstart

```bash
git clone <repo> && cd <repo>
docker compose up
```

That is the whole setup. No `.env` to copy, no migrations to run, no seed step,
nothing installed on the host but Docker.

| | |
| --- | --- |
| Frontend | http://localhost:3000 (redirects to `/en` or `/uz`) |
| API | http://localhost:8000 |
| API docs (OpenAPI) | http://localhost:8000/docs |

Sign in immediately with either demo account:

| Role | Email | Password |
| --- | --- | --- |
| Student | `student@demo.local` | `DemoPass123!` |
| Admin | `admin@demo.local` | `AdminPass123!` |

**Host requirements:** Docker and Docker Compose v2. No Python, Node.js or
PostgreSQL. Cold start after the images are built is about 25 seconds.

## What you get

- **A 20-week roadmap** in six phases weighted like the exam — Foundations,
  Workloads & Scheduling (15%), Networking & Storage (30%), Cluster
  Architecture (25%), Troubleshooting (30%), Mock Exams. Lessons run Monday to
  Friday, Saturday is lab day, Sunday is review.
- **Lessons** rendered from Markdown with syntax-highlighted `bash`/`YAML`
  blocks, copy buttons, and tip/warning/exam-tip callouts. Phase 1 ships ten
  full lessons; phases 2–6 ship the complete structure with drafts, so
  navigation works end to end.
- **Quizzes** with single-choice, multi-select, and fill-in-the-command
  questions. Commands are graded server-side with fuzzy matching, so
  `kubectl get po -A` scores the same as `kubectl get pods --all-namespaces`.
- **Labs** with kind/minikube setup, staged tasks with hidden solutions, and
  verification commands.
- **A dashboard** with per-phase progress, a quiz score trend, a study streak,
  and an exam-readiness estimate weighted by CKA domain percentages.
- **An admin panel** with a Markdown editor and live preview that renders
  through the exact pipeline students see, plus per-lesson Uzbek translation
  fields.
- **English and Uzbek**, switchable from the header. See below.

## Languages

The site is bilingual: **English (`/en/...`)** and **Uzbek (`/uz/...`)**. Use the
`UZ`/`EN` switcher in the header, or go straight to a locale URL.

- A visitor with no saved choice is redirected by `Accept-Language`, then by
  `NEXT_PUBLIC_DEFAULT_LOCALE` (default `en`). The choice is remembered in a
  cookie.
- Each page carries `<html lang>`, a canonical URL and `hreflang` alternates,
  and the sitemap lists every URL in both languages - so both are indexed
  separately.
- The API takes `?lang=uz` (or an `Accept-Language` header) and returns
  localised content.

**What is translated today.** The whole interface, every phase, week, lesson
title and summary, both quizzes (all 20 questions, options and explanations),
both labs (scenarios and task instructions), and the lesson bodies for week 1
plus `kubectl-fundamentals`. Anything without a translation **falls back to
English field by field**, and a lesson whose body fell back says so in a notice
above the text - the reader is never left guessing why the language changed.

**Adding translations.** Either drop files into
`backend/app/seed_data/i18n/uz/` (`structure.json` for titles and summaries,
`lessons/<slug>.md` for bodies, `quizzes/<slug>.json`, `labs/<slug>.json`) and
restart, or edit them directly in the admin panel's lesson editor. The seeder
only ever fills in fields that are still empty, so it never overwrites an
admin's edit.

**Adding a third language.** Add the code to `LOCALES` in
`frontend/src/i18n/config.ts` and `SUPPORTED_LOCALES` in `backend/app/i18n.py`,
copy `frontend/src/i18n/dictionaries/en.ts` to the new code, and add a
`backend/app/seed_data/i18n/<code>/` directory. Nothing else changes.

## Everyday commands

```bash
docker compose up                 # start everything
docker compose up --build         # rebuild after changing source
docker compose down               # stop, keep the database
docker compose down -v            # stop and wipe the database (clean re-seed)
docker compose logs -f backend    # follow the API logs
docker compose run --rm backend pytest   # 73 backend tests
docker compose exec db psql -U cka -d cka_prep   # a psql shell
```

All three services sit on a dedicated bridge network (`k8s` by default, set
`DOCKER_NETWORK` to rename it) and reach each other by service name. Postgres is
published on the host as well; if 5432 is already taken there, set
`POSTGRES_PORT_HOST=5433` - the container port never changes, so nothing inside
the stack is affected.

## Configuration

Everything has a working default baked into `docker-compose.yml`, so a `.env`
file is optional. `cp .env.example .env` and edit if you want to override
something — every variable is documented there.

**Google OAuth is optional.** Leave `GOOGLE_CLIENT_ID` and
`GOOGLE_CLIENT_SECRET` empty and the app works fully on email/password; the
"Continue with Google" button is hidden automatically because the frontend asks
`/api/v1/auth/config` what is enabled. Fill them in and the button appears — no
code change.

## Repository layout

```
.
├── docker-compose.yml          # the only entrypoint for a local run
├── .env.example                # every variable, documented; works as-is
├── backend/                    # FastAPI + SQLAlchemy 2.0 (async) + Alembic
│   ├── Dockerfile              # multi-stage, non-root, 263 MB
│   ├── entrypoint.sh           # wait-for-db → migrate → seed → uvicorn
│   ├── alembic/                # migrations (the only way schema changes)
│   ├── app/
│   │   ├── routers/            # HTTP layer
│   │   ├── services/           # business logic
│   │   ├── repositories/       # data access
│   │   ├── models/  schemas/   # ORM models and Pydantic schemas, kept apart
│   │   ├── i18n.py             # locale negotiation + per-field fallback
│   │   ├── seed.py             # idempotent, runs on every start
│   │   └── seed_data/          # phases.json, lessons/*.md, quizzes/*.json
│   │       └── i18n/uz/        # Uzbek overrides, same shape
│   └── tests/                  # pytest: auth, quiz scoring, progress
├── frontend/                   # Next.js 14 App Router + TypeScript + Tailwind
│   ├── Dockerfile              # multi-stage, standalone output, non-root
│   └── src/
│       ├── middleware.ts       # locale negotiation + /{locale} redirect
│       ├── i18n/               # dictionaries (en, uz) + provider
│       └── app/[locale]/       # every page, under its locale segment
└── k8s/                        # production manifests (see k8s/README.md)
```

## Architecture

**Backend** — FastAPI with a three-layer split: routers call services, services
call repositories, repositories own the SQL. Pydantic schemas are separate from
ORM models, so the answer key never reaches a student: `QuizDetail` simply has
no field for it. Alembic from the first commit; migrations are the only way the
schema changes.

**Frontend** — Every page lives under a `/{locale}` segment, so both languages
have their own indexable URLs. Public content (landing, roadmap, lesson pages)
is server rendered, with per-page metadata, JSON-LD, hreflang alternates and a
generated sitemap. Lesson Markdown is compiled to HTML on the server with Shiki, so code
highlighting costs the browser nothing; only the copy buttons are client-side.
Authenticated views are client components against a fetch wrapper that refreshes
expired access tokens transparently.

**Auth** — JWT access + refresh tokens. Roles are `student` and `admin`, and
**every** admin endpoint re-checks the role server-side. Hiding the admin nav is
cosmetic, not access control.

**Charts** — Hand-built SVG and CSS against a colour palette validated for
colour-blind separation and contrast in both light and dark mode. Every chart
has a table view, so nothing depends on colour alone.

### A note on the stack

The spec named `fastapi-users` for auth and shadcn/ui for components. Both were
substituted, deliberately:

- **Auth** is implemented directly on PyJWT + bcrypt. `fastapi-users` has no
  first-class refresh-token flow, and the spec requires access **and** refresh
  tokens. Rolling the two endpoints directly is about 80 lines and removes a
  dependency that would have needed working around. Everything the spec asked
  for — JWT pairs, roles, optional Google OAuth via Authlib — is present.
- **UI components** follow the shadcn/ui structure (`components/ui/*`,
  `class-variance-authority` variants, a `cn()` helper) but are written by hand
  rather than pulled with the shadcn CLI, which needs network access at build
  time and would have added Radix for primitives this app does not use.

## Testing

```bash
docker compose run --rm backend pytest
```

73 tests covering the auth flow (registration, login, refresh-token rejection of
access tokens, role enforcement), quiz scoring (command normalisation, fuzzy
matching, exact-set multi-select grading, points weighting, answer-key leakage),
progress logic (streak arithmetic across gaps, readiness weighting, lesson
completion idempotence) and localisation (locale negotiation, per-field English
fallback, and that translating a quiz never changes which answers are correct). They run against a dedicated `cka_prep_test` database
on the same server, so your development data is never touched.

## Deploying to Kubernetes

`k8s/` holds production-shaped manifests for the same images compose builds:
StatefulSet + PVC for Postgres, a migration Job, Deployments with liveness
(`/healthz`) and readiness (`/readyz`) probes, resource requests and limits,
non-root `restricted`-compliant security contexts, an HPA, PodDisruptionBudgets,
an Ingress and a NetworkPolicy. See [k8s/README.md](k8s/README.md).

```bash
kubectl apply -k k8s/
```

## Roadmap

Labs are instructions-only in v1 and run against your own cluster. The lab model
already stores tasks as structured steps with verification commands, so a v2
browser terminal (WebSocket + an ephemeral cluster backend) can be added without
touching existing content.

---

Not affiliated with the CNCF or the Linux Foundation. Exam domain weightings
follow the published CKA curriculum.
# cka-roadmap
