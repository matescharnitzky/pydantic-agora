# Development

Requirements: Docker with Compose, Python 3.13, uv, Node 24 with npm, direnv, and 1Password CLI. Follow [configuration setup](configuration.md) before starting services. Both Python services declare `requires-python = ">=3.13,<3.14"`; the root `.python-version` selects Python 3.13 for uv. The root uv workspace shares one development environment and lockfile.

## Source layout

The API follows [FastAPI’s larger-application guidance](https://fastapi.tiangolo.com/tutorial/bigger-applications/) and the [official full-stack template](https://github.com/fastapi/full-stack-fastapi-template/tree/master/backend/app): `main.py` creates the app, `core/config.py` holds settings, `api/main.py` combines routers, `api/routes/` defines endpoints, and `models.py` defines response models. Route dependencies live in `api/deps.py`; route tests mirror the route directory.

The frontend follows [Next.js project structure](https://nextjs.org/docs/app/getting-started/project-structure): routes live in `src/app`, page-specific components in `src/app/_components`, and reusable helpers in `src/lib`. Shared UI components can live in `src/components` when needed.

The worker uses `__main__.py` for `python -m agora_worker`, including startup, database checks, and shutdown. Settings live in `config.py`. DBOS is not installed yet; its [integration guide](https://docs.dbos.dev/python/integrating-dbos) initializes DBOS in the application entry point without prescribing a directory layout.

## Install and check

```sh
make install
make check
```

`make check` runs Ruff, Pyright, Python unit tests, ESLint, TypeScript, and frontend unit tests. Run individual JavaScript commands with `npm --prefix frontend run lint` or `npm --prefix tests run typecheck`.

## Running stack

```sh
make up
docker compose ps
docker compose logs -f
make down
```

`make up` starts the frontend, API, worker, and PostgreSQL. `make down` also removes the optional pgAdmin container and preserves data volumes. The API's `/health` endpoint checks process liveness; `/ready` checks PostgreSQL. The worker verifies connectivity and handles shutdown; it does not execute capabilities yet.

## Database browser

```sh
make pgadmin
```

Open [pgAdmin](http://127.0.0.1:5050) and sign in with `PGADMIN_EMAIL` and the pgAdmin password stored in 1Password. Expand **Servers → Agora → Agora local** and enter the PostgreSQL password from 1Password.

For an existing pgAdmin connection created before the Compose rename, change its Host from `database` to `postgres`. New connections use `postgres`.

The server connection is imported on first startup with the configured `POSTGRES_DB` and `POSTGRES_USER`. If these change later, update the saved pgAdmin connection too. pgAdmin sign-in credentials also initialize on first startup; change an existing account's password within pgAdmin.

Browse **Databases → agora → Schemas → public → Tables**, or open Query Tool. There are no application tables until Phase 2. Settings persist in a separate volume. Use `docker compose stop pgadmin` to stop only this tool.

## API, browser, and database tests

Install the browser once, then test the running stack:

```sh
npm --prefix tests exec -- playwright install chromium
make smoke
```

Bruno checks the running API; Playwright checks browser-to-database readiness. Neither imports application internals. Override test targets with `FRONTEND_BASE_URL` and `API_BASE_URL`. For Bruno, use `npm --prefix tests run test:api -- --env-var baseUrl=http://127.0.0.1:8000`.

Run Python integration tests against local PostgreSQL, using the matching credentials if overridden:

```sh
uv run --all-packages --locked pytest -m integration
```

## Native development

Start PostgreSQL, then run each application in a separate terminal:

```sh
docker compose up --detach --wait postgres
uv run --all-packages --locked uvicorn agora_api.main:create_app --factory --reload --host 127.0.0.1
uv run --all-packages --locked python -m agora_worker
npm --prefix frontend run dev
```

direnv supplies the `POSTGRES_*` settings for local PostgreSQL; Compose overrides the host to `postgres`. Each Python service constructs its connection URL from these settings. Frontend `API_BASE_URL` is server-only and defaults to `http://127.0.0.1:8000`. Compose sets it to `http://api:8000`.

## Containers and CI

Build Python images from the repository root: `docker build -f api/Dockerfile .` or `docker build -f worker/Dockerfile .`. Each image uses `uv sync --frozen` to install its selected service and runtime dependencies from the shared lockfile, and copies only its own dependency declaration and source. CI validates the full workspace lockfile separately with `--locked`. Hatchling builds each service's installable Python package from its `src/` directory. Python runtime images copy only the installed virtual environment from the build stage; uv, source trees, and dependency files stay in the build stage. The frontend runtime similarly copies only Next.js build output.

GitHub Actions reports five checks: **Repo Checks** runs shared Python linting and type checks; **API** and **Worker** run their own unit tests with service-specific dependencies; **Frontend** runs its lint, type, and unit checks; **End-to-End** starts the application and runs database, API, and browser tests. Live-model evaluations remain separately invoked.
