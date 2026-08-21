## Measure before you optimise

*Build → Pipelines → a pipeline → the **Duration** and the stage graph*,
and *Analyze → CI/CD analytics* for the trend. Three numbers to read:

- **total duration** - what developers wait for;
- **critical path** - the longest chain of dependent jobs (the Needs view
  shows it); nothing else you speed up will shorten the pipeline;
- **queued time** per job - if jobs wait for a runner, the fix is runners,
  not YAML.

## The tools, roughly in order of payoff

### 1. Run less

`rules:changes`, `workflow:rules`, and `interruptible:`:

```yaml
default:
  interruptible: true      # a newer pipeline on the same ref cancels this one's running jobs
```

Enable *Settings → CI/CD → General pipelines → Auto-cancel redundant
pipelines* and pushes in quick succession stop piling up. Mark deploy jobs
`interruptible: false` - a half-run deploy is worse than a slow one.

### 2. Start sooner

`needs:` (week 2) so fast jobs do not wait for a whole stage. Typical win:
lint and unit tests no longer wait for a 4-minute integration suite to
finish before `build` starts.

### 3. Do less per job

- cache dependencies (`.npm/`, `.m2/`, pip cache) keyed on the lock file;
- `GIT_DEPTH: 1` (shallow clone) for jobs that do not need history;
- `GIT_STRATEGY: none` for jobs that only consume artifacts;
- small images (`alpine`, `-slim`), and a purpose-built image instead of
  `apk add` in every job.

```yaml
variables:
  GIT_DEPTH: 1
  FF_USE_FASTZIP: "true"                 # faster artifact/cache archiving
  ARTIFACT_COMPRESSION_LEVEL: fast
  CACHE_COMPRESSION_LEVEL: fast
```

### 4. Split what is slow

`parallel:` to shard tests; `parallel:matrix` for builds; a **child
pipeline** (next lesson) for a slow, independent part.

### 5. Fail fast

Put the cheap checks first and let them kill the pipeline early: a 20 s
lint in `.pre` that stops a 10-minute build is minutes saved on every bad
push. `retry:` only for infrastructure failures, never for flaky tests -
fix the tests.

```yaml
default:
  retry:
    max: 2
    when: [runner_system_failure, api_failure, stuck_or_timeout_failure]
```

## A before/after worth writing down

```text
before: test(4m, waits)  → build(3m) → publish(1m) → deploy(1m)   = 9m critical path
after : lint 20s ─┐
        unit 1m  ─┼─ needs → build(3m, cached deps 1m) → publish → deploy = ~3.5m
        integ 4m ─┘ (runs alongside build; blocks only deploy)
```

## Self-check

- Which number tells you whether to optimise YAML or add runners?
- Why should deploy jobs be `interruptible: false`?
- Name two ways to shorten a job's checkout.
