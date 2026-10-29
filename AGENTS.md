# Working on Agora

Agora is a runtime for the Pydantic ecosystem, not affiliated with or endorsed by Pydantic.

Follow the latest user guidance when it differs from an issue description; ask when the intended behavior is unclear.

## Architecture

- Follow the service responsibilities in [architecture.md](docs/architecture.md). Keep services independently deployable.
- API and worker must not import each other's internals. Introduce shared packages or infrastructure only when there is a demonstrated need and an agreed design.

## Coding standards

### Backend

- Follow [pyproject.toml](pyproject.toml) for shared Python tools and rules, and [api/pyproject.toml](api/pyproject.toml) and [worker/pyproject.toml](worker/pyproject.toml) for service dependencies.
- Follow [FastAPI's larger-application guidance](https://fastapi.tiangolo.com/tutorial/bigger-applications/) and the [official FastAPI template](https://github.com/fastapi/full-stack-fastapi-template/tree/master/backend/app) as a reference for API organization.
- Use Pydantic models for HTTP contracts and settings. Keep API dependencies in `api/deps.py`, business logic in `services/`, and route schemas in the central `models.py` for now.

### Frontend

- Follow [package.json](package.json), [frontend/package.json](frontend/package.json), and [tests/package.json](tests/package.json) for workspace dependencies and scripts; use [tsconfig.json](frontend/tsconfig.json) and [eslint.config.mjs](frontend/eslint.config.mjs) for frontend code rules.
- Follow [Next.js project structure](https://nextjs.org/docs/app/getting-started/project-structure) and existing component and styling conventions.
- Use Server Components by default; add Client Components where browser APIs or interaction require them.

### Documentation

- Prefer concise, human-written documentation. LLM-generated text should be brief, reviewed, and written for people. Use plain language and Mermaid diagrams where you see fit.
- Document implemented behavior. Remove repetition and historical discussion that merely narrates the code.
- Keep setup and development instructions in [README.md](README.md) and architecture in [architecture.md](docs/architecture.md). Reference these instead of duplicating them.

## Development and testing

- Give each feature issue its own branch and pull request. Use conventional branch prefixes such as `feat/<name>`, `fix/<name>`, or `docs/<name>`; do not use `codex/`.
- Use [.python-version](.python-version) and [.nvmrc](.nvmrc) for runtime versions. Keep dependency declarations consistent with [uv.lock](uv.lock) and [package-lock.json](package-lock.json).
- Use [Makefile](Makefile) targets for setup, development, and verification; see the README for usage.
- Keep service tests with their service. Use Bruno for focused API checks and Playwright for user scenarios through the browser or HTTP in root `tests/`, without importing application internals. Share service lifecycle control through Playwright fixtures, run disruptive scenarios after browser tests, and use existing test commands rather than adding per-feature Make targets.
- Database integration tests must use real PostgreSQL and fail when credentials are missing. Do not report skipped tests or mocked checks as successful database integration.
- Run checks appropriate to the change and report commands, results, and anything unverified in the PR.

## Configuration and secrets

- Follow the README and [.env.example](.env.example) for local `.env` setup. Keep local configuration ignored and examples free of real credentials.
- Follow [compose.yaml](compose.yaml) for the running stack and [compose.dev.yaml](compose.dev.yaml) for development overrides.
- For our development work, keep only `op://` secret references in `.env`; do not write resolved secrets to it. This does not restrict the user configuration options documented in the README.
- For remote work, start `make dev` while the user is available to approve 1Password and keep the watcher running. Do not add a secrets cache or a credential-recovery wrapper.
- Never print resolved secrets or resolved Compose configuration. Keep credentials out of images, logs, tests, and browser bundles.
- Run locally or in controlled private development environments. Expose local Docker services only on localhost so other computers on the network cannot connect directly.
- Keep generated artifacts, virtual environments, and local plans untracked.
