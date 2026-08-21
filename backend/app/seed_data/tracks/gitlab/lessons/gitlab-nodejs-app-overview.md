## Project status meeting

Three weeks in, the XYZ team can write pipelines. Now they need one for a
real thing: their **Node.js web application** - an Express server with a
few routes, a test suite in Jest, and a Dockerfile nobody has used in CI
yet. From here on every lesson works on this application; the YAML you
write this week is the pipeline the team ships with.

## The application, in five minutes

```text
nodejs-app/
├── app.js              # Express app: routes /, /healthz, /api/todos
├── server.js           # starts app.js on $PORT (default 3000)
├── package.json        # scripts: start, test, lint, build
├── package-lock.json   # pinned dependency tree - npm ci needs it
├── tests/
│   └── app.test.js     # Jest + supertest: request the routes, assert
├── Dockerfile
└── .gitlab-ci.yml      # empty for now - that is this week's work
```

```json
{
  "scripts": {
    "start": "node server.js",
    "test": "jest --ci --coverage",
    "lint": "eslint .",
    "build": "echo 'nothing to compile - static assets are served as-is'"
  }
}
```

## Run it on your machine first

A pipeline is a script of what you would do by hand. Do it by hand once,
so you know what "working" looks like:

```bash
git clone git@gitlab.com:xyz-team/nodejs-app.git && cd nodejs-app
node --version                 # the app pins Node 20 in package.json "engines"
npm ci                         # exact versions from the lock file
npm test                       # Jest runs tests/, prints a coverage table
npm start &                    # listens on :3000
curl -s localhost:3000/healthz # {"status":"ok"}
```

Note what the test output looks like - the `Tests: 6 passed` line and the
coverage table - because the pipeline will need to **find those numbers**
in the log and turn them into reports.

```text
PASS tests/app.test.js
  GET /healthz
    ✓ returns ok (31 ms)
  ...
----------|---------|----------|---------|---------|
File      | % Stmts | % Branch | % Funcs | % Lines |
All files |   92.15 |    83.33 |     100 |   92.15 |
```

## What "ready for CI" means for an app

Before automating, check the three things that make an app pipeline-able:

1. **Reproducible install** - a lock file and `npm ci`. Without it, CI
   installs a slightly different tree than you did.
2. **Non-interactive test command** - `jest --ci` never waits for a key
   press; tests that need a browser or a database say so in a way a
   machine can provide (week 3's `services:`).
3. **An exit code that means something** - `npm test` exits non-zero when
   a test fails. That exit code *is* the red/green of the job.

If any of the three is missing, fix the application before the pipeline.
A pipeline cannot make an untestable app testable; it can only tell you
faster that it is not.

## Self-check

- Why run the app locally before writing the pipeline?
- Which of the three "ready for CI" properties does `jest --ci` provide?
- Where will the coverage percentage come from in a pipeline?
