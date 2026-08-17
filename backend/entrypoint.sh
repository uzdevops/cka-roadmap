#!/bin/sh
# Container entrypoint: wait for the database, migrate, seed, then serve.
#
# Passing a command overrides the server start, so that
#   docker compose run --rm backend pytest
# still gets a migrated database to work against.
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
# On Kubernetes these two steps run once in a Job and every app Pod sets
# RUN_MIGRATIONS=false, so replicas never race on the same DDL.
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    log "running alembic upgrade head"
    alembic upgrade head
else
    log "RUN_MIGRATIONS=false - skipping migrations"
fi

# --- 3. Seed (idempotent) -----------------------------------------------
if [ "${SEED_ON_START:-true}" = "true" ]; then
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
