# Architecture

Agora uses a flat service-oriented monorepo. There is no shared application package or `apps` wrapper. Each deployable owns its dependency configuration, container, entry point, and tests. API and worker share a root uv workspace, Python version, lockfile, development environment, and tooling configuration. The frontend and black-box test projects each retain a pnpm lockfile.

| Service | Owns | Current boundary |
| --- | --- | --- |
| Frontend | Next.js/TypeScript presentation | Reads API readiness on the server; renders an accessible local shell |
| API | FastAPI/Pydantic HTTP validation and contracts | `/health` liveness and `/ready` PostgreSQL connectivity |
| Worker | Python execution process | Verifies PostgreSQL, stays alive until signalled; `--check` probes the database |
| PostgreSQL | Persistent application and future DBOS state | One local instance backed by a named Compose volume |

## Communication and deployment

The browser talks to the frontend. The frontend server talks to FastAPI through `API_BASE_URL`; this address is not bundled into browser code. The API and worker each independently connect to PostgreSQL. The frontend is on a network with the API; only the API, worker, and database join the backend network. The database has a loopback host port for native development and integration tests. Each process runs in a separate container; application containers run as non-root users. API and worker can evolve and scale independently.

The worker shell intentionally has no queue, job dispatcher, or execution HTTP endpoint. The next feasibility slice must validate a supported DBOS mechanism for API submission to the separate worker, Monty host calls, persistence, and status retrieval. Crash/restart and external-side-effect tests must establish recovery semantics before expanding capabilities. A running shell does not prove DBOS/Monty compatibility, and durability does not establish exactly-once external effects.

## Health and failure behavior

- API `/health`: process liveness, HTTP 200, independent of PostgreSQL.
- API `/ready`: a bounded PostgreSQL `SELECT 1`; HTTP 503 on connection/query failure with no DSN or credentials in the response.
- Frontend `/health`: frontend process liveness. The home page separately fetches API readiness and renders an unavailable state on failure.
- Worker: logs startup only after connecting, exits nonzero on failed startup or periodic database probes, and handles SIGINT/SIGTERM for clean shutdown. Compose checks the running container plus an independent `--check` database probe.
- Compose waits for PostgreSQL and API readiness before starting their dependants. Readiness is continuously checked after startup as well.

## Dependency rules

The root workspace resolves compatible Python dependencies together. Each Python service declares its runtime dependencies in its own `pyproject.toml`; common development dependencies live at the root. Developers install both services with `uv sync --all-packages --locked`. Python containers build from the repository-root context and install only their selected package and runtime dependencies with `--package` and `--no-dev`. A shared development environment does not create a runtime dependency between the services. Verify dependency boundaries in the separate containers because the local environment can mask undeclared imports.

Do not import worker modules from the API or API modules from the worker. Keep HTTP contracts and execution responsibilities explicit. Add a shared contract package only after a concrete duplication or compatibility problem justifies it. Reuse official Pydantic ecosystem functionality through thin adapters rather than implementing substitute demo applications.

## Security before authentication

This phase implements no authentication, sessions, authorization abstractions, or execution endpoint. Compose publishes frontend, API, and PostgreSQL only on `127.0.0.1`; the worker is not published. Run only locally or in controlled private infrastructure. Do not override these bindings to expose the stack publicly. Internal container listeners bind on all container interfaces so services can communicate; host bindings remain loopback.

When execution is introduced, enforce typed allowlisted host capabilities, resource budgets, and isolation of host credentials. Never treat Monty sandboxing as a replacement for access control. GitHub OAuth, numeric-ID allowlisting, independent API authorization, and frontend/API/worker trust are Phase 7 work. Public execution is gated on their completion and validation.

## Verification and future decisions

Python unit tests verify liveness, failure responses, and worker failure handling. Explicit integration tests require real PostgreSQL. Bruno and Playwright use the running public service interfaces, not Python imports. CI builds all service images from their frozen lockfiles and verifies service health and the complete browser-to-API-to-database path. No model credential is required.

Future architecture decisions belong in the decisions directory when validated: cross-process DBOS submission, Monty replay/recovery, composition persistence, external idempotency, adapter hosting constraints, justified shared contracts, Render operations, and Phase 7 trust. Reuse Logfire and DBOS Conductor for observability and Pydantic Evals/Logfire for evaluations; do not build replacement dashboards in the foundation.
