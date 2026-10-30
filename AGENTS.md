# Working on Agora

Agora is a runtime for the Pydantic ecosystem, not affiliated with or endorsed by Pydantic.

## General principles

- Follow the latest user guidance when it differs from an issue description. Ask when the intended behavior is unclear.
- Agree on the smallest user-visible outcome. Confirm any scope additions before implementing them.
- Check official documentation for the installed libraries. Prefer native implementation before building custom integrations.

## Architecture

- Follow the service responsibilities in [architecture.md](docs/architecture.md). Keep services independently deployable.
- API and worker must not import each other's internals.

## Coding standards

- Follow [compose.yaml](compose.yaml) for the running stack and [compose.dev.yaml](compose.dev.yaml) for development overrides.

### Backend

- Use [.python-version](.python-version) runtime versions. 
- Follow [pyproject.toml](pyproject.toml) for shared Python tools and rules, and [api/pyproject.toml](api/pyproject.toml) and [worker/pyproject.toml](worker/pyproject.toml) for service dependencies.
- Keep dependency declarations consistent with [uv.lock](uv.lock).
- Follow [FastAPI's larger-application guidance](https://fastapi.tiangolo.com/tutorial/bigger-applications/) and the [official FastAPI template](https://github.com/fastapi/full-stack-fastapi-template/tree/master/backend/app) as a reference for API organization.
- Use Pydantic models for HTTP contracts and settings. Keep API dependencies in `api/deps.py`, business logic in `services/`, and route schemas in the central `models.py` for now.

### Frontend

- Use [.nvmrc](.nvmrc) for runtime versions. 
- Follow [package.json](package.json), [frontend/package.json](frontend/package.json), and [tests/package.json](tests/package.json) for workspace dependencies and scripts; use [tsconfig.json](frontend/tsconfig.json) and [eslint.config.mjs](frontend/eslint.config.mjs) for frontend code rules.
- Keep dependency declarations consistent with [package-lock.json](package-lock.json).
- Follow [Next.js project structure](https://nextjs.org/docs/app/getting-started/project-structure) and existing component and styling conventions.
- Use Server Components by default; add Client Components where browser APIs or interaction require them.

### Documentation

- Prefer concise, human-written documentation. LLM-generated text should be brief, reviewed, and written for people. Use plain language and Mermaid diagrams where you see fit.
- Keep task docstrings brief: explain behavior beyond the signature, including useful assumptions, side effects, or failures. Avoid repeating types and obvious names. Exempt simple data models with `noqa: D101`; use `@typing.override` for trivial overrides that inherit their documentation.
- Document implemented behavior. Remove repetition and historical discussion that merely narrates the code.
- Keep setup and development instructions in [README.md](README.md) and architecture in [architecture.md](docs/architecture.md). Reference these instead of duplicating them.

### Git and GitHub

- Give each feature issue its own branch and pull request. Use conventional branch prefixes such as `feat/<name>`, `fix/<name>`, or `docs/<name>` or similar, do not use `codex/`.
- Wait for explicit final user approval of the current PR before merging or enabling auto-merge.

### Testing

- Keep service tests with their service.
- Use Bruno for API checks and Playwright for browser and user scenario tests in root `tests/`, without application imports.
- Database integration tests must use real PostgreSQL and fail when credentials are missing. Do not report skipped tests or mocked checks as successful database integration.
- Reuse existing test commands and keep the scenario README index current.
- Use [Makefile](Makefile) targets for setup, development, and verification; see the README for usage.
- Run checks appropriate to the change and report commands, results, and anything unverified in the PR.
- After rebuilding the stack, run `make test-bruno` to verify workflows complete. 
- For observability changes, also verify a fresh API-to-worker trace through Logfire's read API.

### Configuration and secrets

- For our development work, keep only `op://` secret references in `.env`; do not write resolved secrets to it. This does not restrict the user configuration options documented in the README.
- For remote work, start `make dev` while the user is available to approve 1Password and keep the watcher running. Do not add a secrets cache or a credential-recovery wrapper.
- Never print resolved secrets or resolved Compose configuration. Keep credentials out of images, logs, tests, and browser bundles.
- Run locally or in controlled private development environments. Expose local Docker services only on localhost so other computers on the network cannot connect directly.
- Keep generated artifacts, virtual environments, and local plans untracked.
