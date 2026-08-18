#!/usr/bin/env bash
# Bring the platform up on a single-node Docker Swarm.
#
#     ./install.sh                  # deploy, and PRINT the firewall commands
#     ./install.sh --with-firewall  # deploy, and APPLY them
#     ./install.sh --help
#
# Idempotent: run it twice and the second run changes nothing it does not have
# to. Swarm is not re-initialised, existing secrets are left alone, and the
# stack is updated rather than recreated.
#
# `docker compose up` still works and is still the right way to run this
# locally. This is the other path: Swarm gives restart policies, rolling
# updates and resource limits without pulling in an orchestrator.
#
# nginx stays on the host. It terminates TLS and proxies to the published
# container ports over the loopback interface - see deploy/nginx/.
set -euo pipefail

STACK="${STACK:-cka}"
COMPOSE_PROJECT="${COMPOSE_PROJECT:-cka}"
STACK_FILE="docker-stack.yml"
ENV_FILE=".env"
ENV_TEMPLATE=".env.production.example"

SECRET_KEY_NAME="cka_secret_key"
POSTGRES_PASSWORD_NAME="cka_postgres_password"

WAIT_SECONDS="${WAIT_SECONDS:-300}"
APPLY_FIREWALL=false

cd "$(dirname "$0")"

# --- output ------------------------------------------------------------------

if [ -t 1 ]; then
    BOLD=$'\033[1m'; DIM=$'\033[2m'; RED=$'\033[31m'
    GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RESET=$'\033[0m'
else
    BOLD=''; DIM=''; RED=''; GREEN=''; YELLOW=''; RESET=''
fi

step() { printf '\n%s==>%s %s%s%s\n' "$GREEN" "$RESET" "$BOLD" "$1" "$RESET"; }
info() { printf '    %s\n' "$1"; }
warn() { printf '%s !! %s%s\n' "$YELLOW" "$1" "$RESET"; }
die()  { printf '%s !! %s%s\n' "$RED" "$1" "$RESET" >&2; exit 1; }

usage() {
    sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
}

for arg in "$@"; do
    case "$arg" in
        --with-firewall) APPLY_FIREWALL=true ;;
        -h|--help)       usage ;;
        *)               die "Unknown argument: $arg (try --help)" ;;
    esac
done

# --- 1. Docker ---------------------------------------------------------------

step "Checking Docker"

command -v docker >/dev/null 2>&1 || die "Docker is not installed. See https://docs.docker.com/engine/install/"
docker info >/dev/null 2>&1 || die "Cannot talk to the Docker daemon. Is it running, and are you in the 'docker' group?"

DOCKER_VERSION="$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo unknown)"
info "Docker ${DOCKER_VERSION}"

# `docker compose` (v2) is what builds the images; the v1 `docker-compose`
# binary cannot read this compose file's build args the same way.
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 is required ('docker compose', not 'docker-compose')."

# --- 2. Swarm ----------------------------------------------------------------

step "Checking Swarm"

SWARM_STATE="$(docker info --format '{{.Swarm.LocalNodeState}}' 2>/dev/null || echo unknown)"

case "$SWARM_STATE" in
    active)
        info "Swarm is already active - leaving it alone."
        ;;
    inactive)
        # --advertise-addr is required as soon as the host has more than one
        # address, and guessing wrong makes the node unreachable to itself.
        ADVERTISE="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}')"
        [ -n "$ADVERTISE" ] || ADVERTISE="$(hostname -I 2>/dev/null | awk '{print $1}')"
        [ -n "$ADVERTISE" ] || die "Could not determine an IP to advertise. Run: docker swarm init --advertise-addr <ip>"
        info "Initialising a single-node Swarm on ${ADVERTISE}"
        docker swarm init --advertise-addr "$ADVERTISE" >/dev/null
        ;;
    pending|locked)
        die "Swarm is '${SWARM_STATE}'. Resolve that first (docker swarm unlock), then re-run."
        ;;
    *)
        die "Unexpected Swarm state: ${SWARM_STATE}"
        ;;
esac

# --- 3. .env -----------------------------------------------------------------

step "Checking ${ENV_FILE}"

# openssl, not base64 or /dev/urandom piped through tr: the password goes
# straight into a DSN (postgresql+asyncpg://user:PASSWORD@db:5432/name), so a
# '/', '+', '@' or ':' silently produces a wrong DSN, and a '$' is expanded by
# Compose while it reads the file. Hex has none of those characters.
random_hex() { openssl rand -hex "$1"; }

if [ -f "$ENV_FILE" ]; then
    info "${ENV_FILE} exists - not touching it."
else
    [ -f "$ENV_TEMPLATE" ] || die "Neither ${ENV_FILE} nor ${ENV_TEMPLATE} exists."
    command -v openssl >/dev/null 2>&1 || die "openssl is required to generate secrets."

    info "Creating ${ENV_FILE} from ${ENV_TEMPLATE} with generated secrets"
    cp "$ENV_TEMPLATE" "$ENV_FILE"

    GENERATED_SECRET_KEY="$(random_hex 32)"
    GENERATED_DB_PASSWORD="$(random_hex 24)"

    # `|` as the sed delimiter - hex cannot contain it, and a '/' in a
    # replacement would end the expression.
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${GENERATED_SECRET_KEY}|" "$ENV_FILE"
    sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${GENERATED_DB_PASSWORD}|" "$ENV_FILE"

    chmod 600 "$ENV_FILE"
    warn "${ENV_FILE} still has placeholder values for the demo accounts and the"
    warn "domain. Review it before exposing this to the internet."
fi

set -a
# shellcheck disable=SC1090
. "./$ENV_FILE"
set +a

: "${SECRET_KEY:?SECRET_KEY is empty in $ENV_FILE}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is empty in $ENV_FILE}"

if [ "$SECRET_KEY" = "CHANGE_ME_64_hex_chars" ] || [ "$POSTGRES_PASSWORD" = "CHANGE_ME_48_hex_chars" ]; then
    die "${ENV_FILE} still holds the template placeholders. Replace them (openssl rand -hex 32) and re-run."
fi

# --- 4. Secrets --------------------------------------------------------------

step "Checking Docker secrets"

# A Swarm secret is immutable. Rotating one means creating a new name and
# updating the service, so this only ever creates a missing secret - it never
# silently replaces a live one under a running stack.
ensure_secret() {
    local name="$1" value="$2"
    if docker secret inspect "$name" >/dev/null 2>&1; then
        info "${name} exists - left as is."
        return 0
    fi
    printf '%s' "$value" | docker secret create "$name" - >/dev/null
    info "${name} created."
}

ensure_secret "$SECRET_KEY_NAME" "$SECRET_KEY"
ensure_secret "$POSTGRES_PASSWORD_NAME" "$POSTGRES_PASSWORD"

# --- 5. Images ---------------------------------------------------------------

step "Building images"

# NEXT_PUBLIC_* are baked into the client bundle at build time, so changing the
# domain needs a rebuild - a restart is not enough. That is why this runs on
# every install rather than only when an image is missing.
info "NEXT_PUBLIC_SITE_URL=${NEXT_PUBLIC_SITE_URL:-<unset>}"
info "NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL-<unset>} (empty means same-origin)"
docker compose -p "$COMPOSE_PROJECT" build

# --- 6. Deploy ---------------------------------------------------------------

step "Deploying stack '${STACK}'"

# --resolve-image never is required, not an optimisation: there is no registry,
# the tags exist only on this node, and the default would send Docker looking
# for them upstream and fail.
docker stack deploy -c "$STACK_FILE" --resolve-image never "$STACK"

# --- 7. Wait -----------------------------------------------------------------

step "Waiting for services"

services_ready() {
    local line name replicas running wanted
    while read -r line; do
        name="${line%% *}"
        replicas="${line##* }"
        running="${replicas%%/*}"
        wanted="${replicas##*/}"
        [ "$running" = "$wanted" ] && [ "$running" != "0" ] || return 1
    done < <(docker service ls --filter "label=com.docker.stack.namespace=${STACK}" \
                --format '{{.Name}} {{.Replicas}}')
    return 0
}

waited=0
until services_ready; do
    if [ "$waited" -ge "$WAIT_SECONDS" ]; then
        warn "Services did not converge within ${WAIT_SECONDS}s."
        docker service ls --filter "label=com.docker.stack.namespace=${STACK}"
        for svc in $(docker service ls --filter "label=com.docker.stack.namespace=${STACK}" --format '{{.Name}}'); do
            printf '\n%s--- %s ---%s\n' "$DIM" "$svc" "$RESET"
            docker service logs --tail 40 "$svc" 2>&1 || true
        done
        die "Deploy did not come up. See the logs above."
    fi
    sleep 5
    waited=$((waited + 5))
done
info "All services report their desired replica count (${waited}s)."

step "Checking health endpoints"

BACKEND_URL="http://127.0.0.1:${BACKEND_PORT:-8000}/healthz"
FRONTEND_URL="http://127.0.0.1:${FRONTEND_PORT:-3000}/healthz"

check_url() {
    local url="$1" name="$2" tries=0
    # The backend does not bind until migrations and the seed have finished, so
    # "replicas 1/1" is not the same as "answering".
    until curl -fsS --max-time 5 "$url" >/dev/null 2>&1; do
        tries=$((tries + 1))
        if [ "$tries" -ge 60 ]; then
            warn "${name} did not answer at ${url}"
            docker service logs --tail 40 "${STACK}_${name}" 2>&1 || true
            return 1
        fi
        sleep 5
    done
    info "${name} is answering at ${url}"
}

FAILED=0
check_url "$BACKEND_URL" backend || FAILED=1
check_url "$FRONTEND_URL" frontend || FAILED=1
[ "$FAILED" -eq 0 ] || die "The stack is up but not healthy."

# --- 8. Firewall -------------------------------------------------------------

step "Firewall"

# Swarm cannot bind a published port to a single interface (no host_ip in the
# long port syntax), so 8000 and 3000 are on 0.0.0.0. On a server that means the
# raw API and the un-proxied frontend are reachable from the internet, bypassing
# nginx and TLS. The firewall is what closes them.
FW_PORTS=("${BACKEND_PORT:-8000}" "${FRONTEND_PORT:-3000}")

print_firewall_commands() {
    printf '\n    %swith nftables:%s\n' "$BOLD" "$RESET"
    for port in "${FW_PORTS[@]}"; do
        printf '      sudo nft add rule inet filter input iif != "lo" tcp dport %s drop\n' "$port"
    done
    printf '\n    %swith ufw:%s\n' "$BOLD" "$RESET"
    for port in "${FW_PORTS[@]}"; do
        printf '      sudo ufw deny %s/tcp\n' "$port"
    done
    printf '\n    Verify from ANOTHER machine:\n'
    for port in "${FW_PORTS[@]}"; do
        printf '      nc -zv <this-host> %s   # should be refused or time out\n' "$port"
    done
}

port_is_open_externally() {
    ss -ltn 2>/dev/null | awk -v p=":$1\$" '$4 ~ p && $4 !~ /^127\.|^\[::1\]/ {found=1} END {exit !found}'
}

OPEN_PORTS=()
for port in "${FW_PORTS[@]}"; do
    port_is_open_externally "$port" && OPEN_PORTS+=("$port")
done

if [ "$APPLY_FIREWALL" = true ]; then
    if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
        for port in "${FW_PORTS[@]}"; do
            sudo ufw deny "${port}/tcp" >/dev/null && info "ufw: denied ${port}/tcp"
        done
    elif command -v nft >/dev/null 2>&1; then
        for port in "${FW_PORTS[@]}"; do
            sudo nft add rule inet filter input iif != "lo" tcp dport "$port" drop \
                && info "nftables: dropped ${port} from non-loopback"
        done
    else
        warn "Neither an active ufw nor nft was found - nothing applied."
        print_firewall_commands
    fi
elif [ ${#OPEN_PORTS[@]} -gt 0 ]; then
    warn "Ports ${OPEN_PORTS[*]} are listening on all interfaces."
    warn "On a public server that exposes the raw API and the un-proxied frontend,"
    warn "bypassing nginx and TLS. Close them, or re-run with --with-firewall."
    print_firewall_commands
else
    info "No stack port is listening on a public interface."
fi

# --- 9. Summary --------------------------------------------------------------

step "Done"

docker service ls --filter "label=com.docker.stack.namespace=${STACK}"

cat <<EOF

    ${BOLD}URLs${RESET}
      frontend   http://127.0.0.1:${FRONTEND_PORT:-3000}
      backend    http://127.0.0.1:${BACKEND_PORT:-8000}/healthz
      public     ${NEXT_PUBLIC_SITE_URL:-<set NEXT_PUBLIC_SITE_URL>}

    ${BOLD}Next${RESET}
      make stack-ps                  service and task status
      make stack-logs                follow the logs
      make psql                      a shell on the database
      deploy/README.md               nginx, TLS and the firewall rules

    ${DIM}Re-running this script is safe: Swarm stays initialised, secrets are
    kept, and the stack is updated in place.${RESET}
EOF
