.PHONY: install up down check test-api test-e2e smoke

install:
	uv sync --all-packages --locked
	npm --prefix frontend ci
	npm --prefix tests ci

up:
	docker compose up --build --detach --wait

down:
	docker compose down

check:
	uv run --all-packages --locked ruff check .
	uv run --all-packages --locked ruff format --check .
	uv run --all-packages --locked pyright
	uv run --all-packages --locked pytest -m "not integration"
	npm --prefix frontend run lint
	npm --prefix frontend run typecheck
	npm --prefix frontend run test
	npm --prefix tests run typecheck

test-api:
	npm --prefix tests run test:api

test-e2e:
	npm --prefix tests run test:e2e

smoke: test-api test-e2e
