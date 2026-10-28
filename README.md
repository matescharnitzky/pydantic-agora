# Agora

Agora is a runtime for the Pydantic ecosystem. Not affiliated with or endorsed by Pydantic.

## Tech stack

### Services

| Component | Technology |
| --------- | ---------- |
| Frontend service | [Next.js](https://nextjs.org/), [React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Tailwind CSS](https://tailwindcss.com/), [shadcn/ui](https://ui.shadcn.com/) (configured) |
| API service | [FastAPI](https://fastapi.tiangolo.com/), [Pydantic](https://docs.pydantic.dev/), [Uvicorn](https://www.uvicorn.org/) |
| Worker service | [Python](https://www.python.org/), [DBOS](https://docs.dbos.dev/) (planned) |
| Database | [PostgreSQL](https://www.postgresql.org/), [pgAdmin](https://www.pgadmin.org/) |
| Documentation | [Fumadocs](https://www.fumadocs.dev/), Markdown, [Mermaid](https://mermaid.js.org/) |

### Development tooling

| Component | Technology |
| --------- | ---------- |
| Coding agent | gpt-6.1-sol via [Codex](https://openai.com/codex/) |
| Secrets | [1Password CLI](https://www.1password.dev/cli/) |
| Containerization | [Docker](https://www.docker.com/), [Docker Compose](https://docs.docker.com/compose/) |
| Tests | [pytest](https://docs.pytest.org/), [Vitest](https://vitest.dev/), [Playwright](https://playwright.dev/), [Bruno](https://www.usebruno.com/) |
| Code quality | [Ruff](https://docs.astral.sh/ruff/), [Pyright](https://github.com/microsoft/pyright), [ESLint](https://eslint.org/), [TypeScript strict mode](https://www.typescriptlang.org/tsconfig/strict.html) |
| CI | [GitHub Actions](https://docs.github.com/en/actions) |
| Package managers | [uv](https://docs.astral.sh/uv/) (Python), [npm](https://docs.npmjs.com/) (JavaScript) |
| Node version manager | [nvm](https://github.com/nvm-sh/nvm) |

## Configuration

### Prerequisites

Follow the official setup instructions for each tool:

- [uv](https://docs.astral.sh/uv/getting-started/installation/) for Python development.
- [nvm](https://github.com/nvm-sh/nvm#installing-and-updating) to manage Node.js including npm.
- [1Password CLI](https://www.1password.dev/cli/get-started) (optional) for `op://` secret references.
- [Docker Desktop](https://docs.docker.com/desktop/setup/install/) with Compose 2.32+ for running the application.

### Environment variables

The application works with the following environment variables.

| Variable | Value |
|---|---|
| `OPENAI_API_KEY` | Optional; not used yet |
| `LOGFIRE_TOKEN` | Optional; not used yet |
| `POSTGRES_USER` | Required: database role |
| `POSTGRES_PASSWORD` | Required: database password |
| `PGADMIN_EMAIL` | Required: pgAdmin login |
| `PGADMIN_PASSWORD` | Required: pgAdmin password |
| `POSTGRES_DB` | `postgres` |
| `POSTGRES_HOST` | `localhost` natively; `postgres` inside Compose |
| `POSTGRES_PORT` | `5432` |

There are two ways to set them: either you can add them to a .env file
or you can fetch them from a password manager like 1password.

#### .env

Copy `.env.example` to `.env` and set the required credentials.

#### 1password

Install [1Password CLI](https://www.1password.dev/cli/get-started) and enable its desktop app integration.
Replace values in `.env` with references to your vault item.
For example, if you have a `Development` vault with a `my-project` item, your dotenv would look like:

```dotenv
OPENAI_API_KEY=op://Development/my-project/OPENAI_API_KEY
LOGFIRE_TOKEN=op://Development/my-project/LOGFIRE_TOKEN
...
```

## Run locally

Once the environment variables are configured, you can start the application with:

```sh
make up
```

This gives you the following:

* [Application](http://localhost:3000)
* [Documentation](http://localhost:3000/docs)
* [API documentation](http://localhost:8000/docs)
* [Postgres observability](http://localhost:5050). In pgAdmin, sign in with `PGADMIN_EMAIL` and `PGADMIN_PASSWORD`, then connect to **Agora local** with `POSTGRES_PASSWORD`.

You can stop the docker stack with:

```sh
make down
```

This preserves volumes. To delete local PostgreSQL data and saved pgAdmin accounts and connections:

```sh
make reset
```

## Development

Use Python 3.13 and Node 24. Install host dependencies for checks and tests:

```sh
make install  # Dependencies and Chromium for browser tests
make check    # Lint, type checks, and unit tests
make test-db  # Database integration tests; requires PostgreSQL
make smoke    # API and browser tests; requires the running stack
```

Run development mode in Docker:

```sh
make dev  # Start the stack and watch for changes; keep this terminal open
```
