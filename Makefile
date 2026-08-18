# Two ways to run this platform, and the everyday commands for each.
#
#   make up             docker compose - local development, zero config
#   make stack-deploy   docker swarm  - a single node with restart policies
#
# `make help` lists everything.

STACK ?= cka
COMPOSE ?= docker compose
STACK_FILE ?= docker-stack.yml

# The database name is needed by `psql` and lives in .env when there is one.
POSTGRES_USER ?= $(shell sed -n 's/^POSTGRES_USER=//p' .env 2>/dev/null | tail -1)
POSTGRES_DB   ?= $(shell sed -n 's/^POSTGRES_DB=//p' .env 2>/dev/null | tail -1)
POSTGRES_USER := $(if $(POSTGRES_USER),$(POSTGRES_USER),cka)
POSTGRES_DB   := $(if $(POSTGRES_DB),$(POSTGRES_DB),cka_prep)

.DEFAULT_GOAL := help
.PHONY: help build up down logs ps test swarm-init stack-deploy stack-rm \
        stack-logs stack-ps migrate seed psql

help: ## Show this help
	@printf '\nUsage: make <target>\n\n'
	@awk 'BEGIN {FS = ":.*?## "} \
		/^[a-zA-Z0-9_-]+:.*?## / {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2} \
		/^## / {printf "\n\033[1m%s\033[0m\n", substr($$0, 4)}' $(MAKEFILE_LIST)
	@printf '\nSTACK=%s\n\n' '$(STACK)'

## Compose (local)

build: ## Build both images
	$(COMPOSE) build

up: ## Start the stack in the background
	$(COMPOSE) up -d

down: ## Stop the stack (the database volume survives)
	$(COMPOSE) down

logs: ## Follow the logs
	$(COMPOSE) logs -f

ps: ## Show container status
	$(COMPOSE) ps

test: ## Run the backend test suite
	# No migration, no seed: entrypoint.sh skips both when it is handed a
	# command, so this cannot touch the deployment's own database.
	$(COMPOSE) run --rm backend pytest

## Swarm

swarm-init: ## Initialise a single-node Swarm (install.sh does this for you)
	@docker info --format '{{.Swarm.LocalNodeState}}' | grep -qx active \
		&& echo "Swarm is already active." \
		|| docker swarm init

stack-deploy: build ## Build, then deploy the stack to Swarm
	# `set -a` because `docker stack deploy` does not read .env itself, and
	# --resolve-image never because there is no registry: the tags exist only
	# on this node and Docker would otherwise try to pull them.
	@set -a; [ -f .env ] && . ./.env; set +a; \
	docker stack deploy -c $(STACK_FILE) --resolve-image never $(STACK)

stack-rm: ## Remove the stack (volumes and secrets survive)
	docker stack rm $(STACK)

stack-ps: ## Show services and their tasks
	@docker service ls --filter label=com.docker.stack.namespace=$(STACK)
	@echo
	@docker stack ps $(STACK) --no-trunc

stack-logs: ## Follow the backend service log
	docker service logs -f $(STACK)_backend

## Database

migrate: ## Apply migrations against the running stack
	$(COMPOSE) exec backend alembic upgrade head

seed: ## Run the idempotent seed
	$(COMPOSE) exec backend python -m app.seed

psql: ## Open a psql shell on the database
	# Through `docker exec` rather than a published port: the Swarm path does
	# not publish Postgres at all, and this works the same either way.
	@docker exec -it $$(docker ps -q -f name=cka-db -f name=$(STACK)_db | head -1) \
		psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)
