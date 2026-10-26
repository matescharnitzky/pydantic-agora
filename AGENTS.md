# Working on Agora

Agora is an independent open-source playground for the Pydantic ecosystem, not affiliated with or endorsed by Pydantic.

## Architecture

- Keep the flat service-oriented monorepo: `frontend`, `api`, and `worker` are independent deployables with their own dependencies and Dockerfiles. API and worker share a root uv workspace, lockfile, and development environment; each container installs only its selected service and runtime dependencies.
- The frontend owns presentation. FastAPI owns HTTP contracts and validation. The worker owns execution. PostgreSQL stores application and, later, DBOS state.
- Do not import API internals into the worker or worker internals into the API. Do not introduce a shared package, an `apps` wrapper, a message broker, or a plugin framework without a demonstrated need and an explicit decision.
- Reuse upstream Pydantic functionality through thin adapters. Follow the current issue scope; durable execution feasibility comes after the foundation.
- Keep user authentication and authorization implementation in Phase 7. Before then, run only locally or inside controlled private development infrastructure. Bind local published ports to loopback. Never expose an unauthenticated execution service publicly.
- Do not equate sandboxing with authorization, DBOS durability with exactly-once external effects, or a healthy worker shell with a validated execution runtime.

## Development and verification

- Use Python 3.13 with the root uv workspace, Ruff, Pyright strict mode, and pytest. Commit the root uv lockfile. Declare runtime dependencies in each service’s `pyproject.toml` and common development tools/configuration at the root.
- Use Node 24 and its bundled npm. Keep TypeScript strict, ESLint, Vitest, and the two JavaScript lockfiles reproducible.
- `make install` installs dependencies. `make check` runs static checks and unit tests. `make up` builds and starts the full stack; `make smoke` runs black-box tests against it.
- Run Python checks from the root with `uv run --all-packages --locked`. Use `uv run --package agora-api` or `uv run --package agora-worker` for a service command. Black-box commands run from `tests` and must use only HTTP/browser interfaces.
- Run selected PostgreSQL integration checks with `DATABASE_URL` set; see the README. Do not silently substitute mocks when claiming a live integration passed.
- CI runs deterministic checks on pull requests. Keep expensive live-model evaluations separately invoked when introduced.
- Do not add model credentials or production secrets to examples, tests, logs, or browser bundles. Keep local environment files ignored.

## Changes

Read the issue and relevant architecture decisions before implementing. Add focused verification for observable behavior. Record commands run and any unverified limitations in the PR. Keep generated artifacts, virtual environments, and local plans untracked.
