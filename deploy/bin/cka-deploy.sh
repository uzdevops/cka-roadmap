#!/bin/bash
# Fast-forwards to origin/main, rebuilds the images and waits for the stack to
# come back healthy. Triggered by cka-check-updates, or by hand:
#
#     sudo systemctl start cka-deploy
#     journalctl -u cka-deploy -f
#
# The whole body sits in main() so bash has parsed the entire file before the
# first line runs - this script updates itself from the repo, and bash reads
# scripts lazily by byte offset.
set -euo pipefail

REPO="${CKA_REPO:-/opt/projects/cka-roadmap}"
CONTAINERS="cka-db cka-backend cka-frontend"
HEALTH_TIMEOUT=300

log() { printf '%s  %s\n' "$(date '+%H:%M:%S')" "$1"; }

check_clean() {
    local dirty
    dirty=$(git status --porcelain)
    [ -z "$dirty" ] && return 0

    log "ERROR: working tree has local changes - refusing to deploy."
    log "A deploy target has to mirror the remote; fast-forwarding over local"
    log "edits would either fail or throw them away silently. Commit and push"
    log "them, or discard them with 'git checkout -- <file>', then retry."
    printf '%s\n' "$dirty"
    return 1
}

wait_healthy() {
    local waited=0 bad
    while [ "$waited" -lt "$HEALTH_TIMEOUT" ]; do
        bad=""
        for name in $CONTAINERS; do
            status=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
                "$name" 2>/dev/null || echo missing)
            [ "$status" = "healthy" ] || bad="$bad $name=$status"
        done
        if [ -z "$bad" ]; then
            log "all containers healthy"
            return 0
        fi
        sleep 5
        waited=$((waited + 5))
    done
    log "ERROR: not healthy after ${HEALTH_TIMEOUT}s:$bad"
    docker compose logs --tail 40
    return 1
}

# Copies these scripts and units out of the repo into their system locations,
# so a commit can change the pipeline itself. Runs last, and never fails the
# deploy - the app being up matters more than the automation being current.
install_self() {
    local changed=0
    for src in "$REPO"/deploy/bin/*.sh; do
        [ -e "$src" ] || continue
        dest="/usr/local/bin/$(basename "$src" .sh)"
        if ! cmp -s "$src" "$dest"; then
            install -m 0755 "$src" "$dest" && changed=1
            log "updated $dest"
        fi
    done
    for src in "$REPO"/deploy/systemd/*; do
        [ -e "$src" ] || continue
        dest="/etc/systemd/system/$(basename "$src")"
        if ! cmp -s "$src" "$dest"; then
            install -m 0644 "$src" "$dest" && changed=1
            log "updated $dest"
        fi
    done
    [ "$changed" = 1 ] && systemctl daemon-reload && log "systemd reloaded"
    return 0
}

main() {
    cd "$REPO"

    check_clean

    local before after
    before=$(git rev-parse HEAD)
    git fetch --quiet origin
    after=$(git rev-parse '@{u}')

    if [ "$before" = "$after" ]; then
        log "already at ${before:0:8} - nothing to deploy"
        exit 0
    fi

    log "deploying ${before:0:8} -> ${after:0:8}"
    git merge --ff-only '@{u}'

    # --build because NEXT_PUBLIC_* values are compiled into the client bundle;
    # restarting a stale image would serve the old ones.
    log "building and starting"
    docker compose up -d --build --remove-orphans

    wait_healthy

    # Only dangling layers from the build we just did. Never touches volumes.
    docker image prune -f >/dev/null 2>&1 || true

    install_self || true

    log "deployed ${after:0:8}"
}

main "$@"
