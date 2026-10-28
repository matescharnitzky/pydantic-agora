.PHONY: install up down reset check test-db test-recovery test-bruno test-playwright smoke dev

UV_ENV_FILE := $(if $(wildcard .env),--env-file .env)

install:
	uv sync --all-packages --locked
	npm ci
	npm exec --workspace tests -- playwright install chromium

up:
	@./scripts/1password.sh docker compose up --build --detach --wait

down:
	@./scripts/1password.sh docker compose down

reset:
	@./scripts/1password.sh docker compose down --volumes

dev:
	@./scripts/1password.sh docker compose -f compose.yaml -f compose.dev.yaml up --build --watch

check:
	uv run --all-packages --locked ruff check .
	uv run --all-packages --locked ruff format --check .
	uv run --all-packages --locked pyright
	uv run --all-packages --locked pytest -m "not integration"
	npm run --workspace frontend lint
	npm run --workspace frontend typecheck
	npm run --workspace frontend test
	npm run --workspace tests typecheck

test-db:
	@./scripts/1password.sh uv run $(UV_ENV_FILE) --all-packages --locked pytest -m "integration and not recovery"

test-recovery:
	@./scripts/1password.sh uv run $(UV_ENV_FILE) --all-packages --locked pytest worker/tests/test_recovery.py -v -s

test-bruno:
	npm run --workspace tests test:bruno

test-playwright:
	npm run --workspace tests test:playwright

smoke: test-bruno test-playwright
