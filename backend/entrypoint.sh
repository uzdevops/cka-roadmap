#!/bin/sh
# Container entrypoint: wait for the database, migrate, seed, then serve.
#
# Migrations and seeding run ONLY when this container is starting the server.
# Passing a command (docker compose run --rm backend pytest) skips both, because
# that command carries the production .env: an operator "just checking the tests
# pass" on the deploy host would otherwise perform the migration and a full seed
# against the live database before pytest even started. The test suite does not
# need them - tests build their own schema in a separate <db>_test database.
#
# Override deliberately if you do want them for a one-off command:
#   docker compose run --rm -e RUN_MIGRATIONS=true backend alembic upgrade head
set -e

DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
MAX_WAIT="${DB_WAIT_SECONDS:-60}"

log() { printf '%s  entrypoint: %s\n' "$(date '+%H:%M:%S')" "$1"; }

# --- 1. Wait for the database (retry loop, hard cap) ---------------------
log "waiting for postgres at ${DB_HOST}:${DB_PORT} (up to ${MAX_WAIT}s)"
elapsed=0
until python -c "
import socket, sys
s = socket.socket()
s.settimeout(2)
try:
    s.connect(('${DB_HOST}', ${DB_PORT}))
except OSError:
    sys.exit(1)
finally:
    s.close()
" 2>/dev/null; do
    elapsed=$((elapsed + 1))
    if [ "$elapsed" -ge "$MAX_WAIT" ]; then
        log "ERROR: database not reachable after ${MAX_WAIT}s - giving up"
        exit 1
    fi
    sleep 1
done
log "database is accepting connections (${elapsed}s)"

# --- 2. Migrations ------------------------------------------------------
# An override command means someone is running a one-off (pytest, a shell, a
# psql poke) with this container's environment - which on the deploy host is
# the production .env. Neither step runs then, whatever the compose file sets:
# docker-compose.yml passes SEED_ON_START=true unconditionally, so "unset means
# skip" would never fire. FORCE_LIFECYCLE is the deliberate way back in.
if [ "$#" -gt 0 ] && [ "${FORCE_LIFECYCLE:-false}" != "true" ]; then
    RUN_MIGRATIONS=false
    SEED_ON_START=false
    log "override command given - skipping migrations and seed"
    log "  (run with -e FORCE_LIFECYCLE=true if you really want them)"
else
    RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"
    SEED_ON_START="${SEED_ON_START:-true}"
fi

# On Kubernetes these two steps run once in a Job and every app Pod sets
# RUN_MIGRATIONS=false, so replicas never race on the same DDL.
if [ "$RUN_MIGRATIONS" = "true" ]; then
    log "running alembic upgrade head"
    alembic upgrade head
else
    log "RUN_MIGRATIONS=false - skipping migrations"
fi

# --- 3. Seed (idempotent) -----------------------------------------------
if [ "$SEED_ON_START" = "true" ]; then
    log "running idempotent seed"
    python -m app.seed
else
    log "SEED_ON_START=false - skipping seed"
fi

# --- 4. Hand over -------------------------------------------------------
if [ "$#" -gt 0 ]; then
    log "running override command: $*"
    exec "$@"
fi

log "starting uvicorn on 0.0.0.0:8000"
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --proxy-headers \
    --forwarded-allow-ips '*' \
    --workers "${UVICORN_WORKERS:-1}"
