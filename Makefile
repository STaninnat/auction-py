DOCKER_COMPOSE = docker-compose

.PHONY: help up down restart build logs logs-core logs-realtime shell-core shell-realtime migrate makemigrations superuser test clean

help:
	@echo "==================================================================="
	@echo "  		AUCTION PLATFORM MAKEFILE HELP"
	@echo "==================================================================="
	@echo "Common Commands:"
	@echo "  make up              : Start all containers (background)"
	@echo "  make down            : Stop and remove all containers"
	@echo "  make restart         : Restart all containers"
	@echo "  make build           : Rebuild images and start containers"
	@echo "  make logs            : Follow logs of all containers"
	@echo ""
	@echo "Django (Core) Commands:"
	@echo "  make migrate         : Run Django database migrations"
	@echo "  make makemigrations  : Create new migrations based on models"
	@echo "  make superuser       : Create a Django superuser"
	@echo "  make shell-core      : Access Django container shell (bash)"
	@echo "  make logs-core       : Follow logs for Core service only"
	@echo ""
	@echo "FastAPI (Realtime) Commands:"
	@echo "  make shell-realtime  : Access FastAPI container shell (bash)"
	@echo "  make logs-realtime   : Follow logs for Realtime service only"
	@echo ""
	@echo "Testing & Maintenance:"
	@echo "  make test            : Run tests (Pytest)"
	@echo "  make clean           : Remove pycache and orphan containers"
	@echo "==================================================================="

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

test:
	$(DOCKER_COMPOSE) run --rm core pytest
	$(DOCKER_COMPOSE) run --rm realtime pytest
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	$(DOCKER_COMPOSE) down -v --remove-orphans