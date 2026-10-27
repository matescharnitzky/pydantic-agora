export COMPOSE_DISABLE_ENV_FILE := 1

.PHONY: install up pgadmin down check test-api test-e2e smoke

install:
	uv sync --all-packages --locked
	npm ci

up:
	docker compose up --build --detach --wait

pgadmin:
	docker compose up --detach --wait pgadmin

down:
	docker compose --profile tools down

check:
	uv run --all-packages --locked ruff check .
	uv run --all-packages --locked ruff format --check .
	uv run --all-packages --locked pyright
	uv run --all-packages --locked pytest -m "not integration"
	npm run --workspace frontend lint
	npm run --workspace frontend typecheck
	npm run --workspace frontend test
	npm run --workspace tests typecheck

test-api:
	npm run --workspace tests test:bruno

test-e2e:
	npm run --workspace tests test:playwright

smoke: test-api test-e2e
