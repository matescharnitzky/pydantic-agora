# Agora

An independent playground for exploring, composing, observing, and evaluating the Pydantic AI ecosystem. Not affiliated with or endorsed by Pydantic.

This foundation starts three separate services and PostgreSQL. The frontend displays live API/database readiness; the worker verifies its database connection and shuts down cleanly. Capability execution, DBOS, Monty, and model integrations are introduced by subsequent issues.

## Start locally

Install Docker with the Compose plugin, then run:

```sh
cp .env.example .env
docker compose up --build --detach --wait
```

Open [Agora](http://127.0.0.1:3000) or [API documentation](http://127.0.0.1:8000/docs). Check services with:

```sh
docker compose ps
docker compose logs worker
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/ready
docker compose exec worker python -m agora_worker --check
```

Published ports bind only to `127.0.0.1`. The worker publishes no port. This is an unauthenticated local development stack; keep it off the public internet. Default database credentials are disposable development values, not production secrets. PostgreSQL data persists in a named volume. `docker compose down` stops services and keeps that data. API/worker readiness fails if PostgreSQL becomes unavailable; API liveness stays independent of the database.

## Develop and test

Use Python 3.13 (uv can install it), Node 24 with its bundled npm. API and worker are members of a root uv workspace with one `uv.lock` and `.venv`. Their `pyproject.toml` files declare their own runtime dependencies; shared development tools and configuration live in the root `pyproject.toml`. The frontend and black-box tests have separate npm projects, each with a `package-lock.json`.

```sh
make install
# Run from the repository root:
uv run --all-packages --locked ruff check .
uv run --all-packages --locked ruff format --check .
uv run --all-packages --locked pyright
uv run --all-packages --locked pytest -m 'not integration'
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run test
npm --prefix tests run typecheck
```

Or run all the above checks with `make check`.

With the Compose stack running, install the Playwright browser once and run black-box tests:

```sh
npm --prefix tests exec -- playwright install chromium
make smoke
```

Bruno requests run against the live FastAPI service. Playwright verifies the browser shell, API, and database readiness together. Neither test suite imports application internals. Override browser targets with `FRONTEND_BASE_URL` and `API_BASE_URL`. For Bruno use `npm --prefix tests run test:api -- --env-var baseUrl=http://127.0.0.1:8000`.

Run the Python database integration tests against local PostgreSQL:

```sh
DATABASE_URL=postgresql://agora:agora-local@127.0.0.1:5432/agora uv run --all-packages --locked pytest -m integration
```

If you changed `.env`, use the corresponding database credentials above. To develop services without rebuilding containers, start just PostgreSQL, then run each process in a separate terminal:

```sh
docker compose up --detach --wait database
uv run --all-packages --locked uvicorn agora_api.main:create_app --factory --reload --host 127.0.0.1
uv run --all-packages --locked python -m agora_worker
npm --prefix frontend run dev
```

The native service defaults target localhost PostgreSQL. Set `DATABASE_URL` when using different credentials. `API_BASE_URL` is a server-only frontend setting; it defaults to localhost for native development and points to the API container in Compose.

The commands above keep both packages installed in the shared development environment, which is useful when running the two services concurrently. For a single-service environment, use `uv sync --package agora-api` or `uv sync --package agora-worker`. Container builds use these package selections with `--no-dev`, so development tools and the other service are excluded from each runtime image. Build the Python images from the repository root: `docker build -f api/Dockerfile .` or `docker build -f worker/Dockerfile .`.

## Contributing

Start from a [scoped issue](https://github.com/matescharnitzky/pydantic-agora/issues), read [architecture](docs/architecture.md) and [agent/contributor guidance](AGENTS.md), and open a focused PR using the template. Run applicable checks and describe the behavior they verify. PR CI builds the real containers and runs the integration, Bruno, and browser smoke tests. Main-branch and scheduled runs use the same complete foundation suite; broader recovery suites will be added when the runtime exists. Live-model evaluations are outside routine CI.

The roadmap is maintained in GitHub issues. Local planning material is not part of the tracked source.
