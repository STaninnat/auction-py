DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_TEST = docker-compose -f docker-compose.test.yml --env-file .env.test

.PHONY: help \
        up down restart build logs logs-core logs-worker logs-realtime shell-core shell-realtime migrate makemigrations superuser clean pre-commit format \
        test test-build test-down test-core test-realtime

help:
	@echo "==================================================================="
	@echo "  		AUCTION PLATFORM MAKEFILE HELP"
	@echo "==================================================================="
	@echo "DEVELOPMENT Environment:"
	@echo "  make up              : Start all dev containers (background)"
	@echo "  make down            : Stop and remove all dev containers"
	@echo "  make restart         : Restart all dev containers"
	@echo "  make build           : Rebuild dev images and start"
	@echo "  make logs            : Follow logs of all dev containers"
	@echo ""
	@echo "  make logs-core       : Follow logs for Core service only"
	@echo "  make logs-worker     : Follow logs for Worker service only"
	@echo "  make logs-realtime   : Follow logs for Realtime service only"
	@echo "  make shell-core      : Access Django container shell"
	@echo "  make shell-realtime  : Access FastAPI container shell"
	@echo "  make migrate         : Run Django migrations"
	@echo "  make makemigrations  : Create new migrations"
	@echo "  make superuser       : Create a Django superuser"
	@echo ""
	@echo "TESTING Environment (Isolated):"
	@echo "  make test            : Run ALL tests (builds, runs, downs)"
	@echo "  make test-build      : Build test images only"
	@echo "  make test-core       : Run Core tests only"
	@echo "  make test-realtime   : Run Realtime tests only"
	@echo "  make test-down       : Tear down test environment"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean           : Remove pycache and orphan containers"
	@echo "  make pre-commit      : Run pre-commit hooks"
	@echo "  make format          : Run Ruff formatter"
	@echo "==================================================================="

# ==============================================================================
# DEVELOPMENT PROFILE
# ==============================================================================
up:
	$(DOCKER_COMPOSE) up -d

down:
	$(DOCKER_COMPOSE) down

restart:
	$(DOCKER_COMPOSE) restart

build:
	$(DOCKER_COMPOSE) up --build -d

logs:
	$(DOCKER_COMPOSE) logs -f

logs-core:
	$(DOCKER_COMPOSE) logs -f core

logs-worker:
	$(DOCKER_COMPOSE) logs -f worker

logs-realtime:
	$(DOCKER_COMPOSE) logs -f realtime

shell-core:
	$(DOCKER_COMPOSE) exec core /bin/bash

shell-realtime:
	$(DOCKER_COMPOSE) exec realtime /bin/bash

migrate:
	$(DOCKER_COMPOSE) run --rm core python manage.py migrate

makemigrations:
	$(DOCKER_COMPOSE) run --rm core python manage.py makemigrations

superuser:
	$(DOCKER_COMPOSE) run --rm core python manage.py createsuperuser

# ==============================================================================
# TESTING PROFILE (ISOLATED)
# ==============================================================================
test: test-build test-core test-realtime test-down

test-build:
	$(DOCKER_COMPOSE_TEST) build

test-core:
	$(DOCKER_COMPOSE_TEST) run --rm core pytest

test-realtime:
	$(DOCKER_COMPOSE_TEST) run --rm realtime pytest

test-down:
	$(DOCKER_COMPOSE_TEST) down -v

# ==============================================================================
# MAINTENANCE
# ==============================================================================
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	$(DOCKER_COMPOSE) down -v --remove-orphans
	$(DOCKER_COMPOSE_TEST) down -v --remove-orphans

pre-commit:
	pre-commit run --all-files

format:
	ruff format .
	ruff check --fix .
