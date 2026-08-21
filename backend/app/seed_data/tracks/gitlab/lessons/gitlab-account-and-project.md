## Create the account and the project

Everything in this track runs on **gitlab.com** (the SaaS edition) - the
free tier includes shared runners and a monthly compute quota that is more
than enough for learning. Self-managed GitLab behaves identically; only the
hostname changes.

1. Sign up at <https://gitlab.com/users/sign_up>, verify the e-mail, and
   enable two-factor authentication (Preferences → Account).
2. Create a **group** - for example `xyz-team` - so projects can share
   variables and runners later.
3. Inside it create a blank **project** `pipeline-basics` with a README.
4. Add an SSH key (Preferences → SSH Keys) or use a **personal access
   token** for HTTPS pushes:

```bash
git clone git@gitlab.com:xyz-team/pipeline-basics.git
cd pipeline-basics
git config user.email you@example.com
```

## Course resources

The KodeKloud course ships a resources repository with every YAML and
the Node.js application used from week 4. Import it once so it sits under
your own group - **Project → New project → Import project → Repository by
URL** - and keep it separate from the project you experiment in. The
original stays untouched; you break your copy.

```text
xyz-team/
├── pipeline-basics      ← scratch project for weeks 1-3
├── gitlab-cicd-resources← imported course code, read-only reference
└── nodejs-app           ← the application you will ship (week 4 onwards)
```

## The two places a pipeline shows up

- **Build → Pipelines** lists every pipeline with its status, trigger
  (branch, merge request, schedule, manual) and duration.
- **Build → Jobs** lists every job across pipelines. Open one to read the
  log - the runner name, the image that was pulled, every `script` line
  echoed before its output.

Learn to read a job log early. The first 30 lines tell you *where* it ran
and *what* it started from; that is where nine out of ten pipeline
questions are answered.

## The pipeline editor

**Build → Pipeline editor** opens `.gitlab-ci.yml` with live validation,
a **Visualize** tab that draws the stages, a **Full configuration** tab
that shows the YAML *after* includes and templates are expanded, and a
**Validate** tab that simulates a run. Use it for every change in this
track - a syntax error caught in the editor is a pipeline that never
wastes runner minutes.

## Self-check

- Why create a group before creating projects?
- Where do you look first when a job fails, and what do the first lines of
  a log tell you?
