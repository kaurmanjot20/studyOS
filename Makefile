# Convenience targets. On Windows, run these from Git Bash or WSL, or use the
# underlying commands directly.

.PHONY: up down build logs migrate revision fmt

up:            ## Start the full stack
	docker compose up --build

down:          ## Stop the stack
	docker compose down

build:         ## Build images
	docker compose build

logs:          ## Tail logs
	docker compose logs -f

migrate:       ## Apply migrations inside the backend container
	docker compose exec backend alembic upgrade head

revision:      ## Autogenerate a migration: make revision m="message"
	docker compose exec backend alembic revision --autogenerate -m "$(m)"

fmt:           ## Format backend (ruff) — added with tooling in a later phase
	@echo "formatting not configured yet"
