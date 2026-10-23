.PHONY: install up down check test-api test-e2e smoke

install:
	uv sync --all-packages --locked
	pnpm --dir frontend install --frozen-lockfile
	pnpm --dir tests install --frozen-lockfile

up:
	docker compose up --build --detach --wait

down:
	docker compose down

check:
	uv run --all-packages --locked ruff check .
	uv run --all-packages --locked ruff format --check .
	uv run --all-packages --locked pyright
	uv run --all-packages --locked pytest -m "not integration"
	pnpm --dir frontend lint
	pnpm --dir frontend typecheck
	pnpm --dir frontend test
	pnpm --dir tests typecheck

test-api:
	pnpm --dir tests test:api

test-e2e:
	pnpm --dir tests test:e2e

smoke: test-api test-e2e
