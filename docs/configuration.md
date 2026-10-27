---
title: Configuration
---

Agora reads standard environment variables. Docker Compose also reads a regular root `.env` file and passes each service only the variables declared in `compose.yaml`. A secret manager is optional.

## Local configuration without 1Password

```sh
cp .env.example .env
```

Replace the credential placeholders with your own local values, then run `make up`. Keep `.env` ignored by Git. Model and Logfire credentials are optional and are not consumed by the current foundation.

Exported shell variables take precedence over `.env`. Native Python processes do not automatically read it; use `uv run --env-file .env --all-packages --locked ...` for commands outside Compose.

## Local configuration with 1Password

Keep credentials in a 1Password vault item. Your ignored `.env` contains secret references instead of secret values. For example, using the `pydantic-agora` item in the `Development` vault:

```dotenv
POSTGRES_USER=op://Development/pydantic-agora/POSTGRES_USER
POSTGRES_PASSWORD=op://Development/pydantic-agora/POSTGRES_PASSWORD
PGADMIN_EMAIL=op://Development/pydantic-agora/PGADMIN_EMAIL
PGADMIN_PASSWORD=op://Development/pydantic-agora/PGADMIN_PASSWORD
OPENAI_API_KEY=op://Development/pydantic-agora/OPENAI_API_KEY
LOGFIRE_TOKEN=op://Development/pydantic-agora/LOGFIRE_TOKEN
```

Use your own vault, item, and field names. The last two fields are optional for the current foundation; omit them or leave them empty if unused. `POSTGRES_DB` defaults to `postgres` and needs no entry.

Install 1Password CLI and enable its desktop app integration, then use the ordinary commands:

```sh
make up
make pgadmin
make down
```

These targets call `scripts/1password.sh`. When `.env` contains secret references, it runs `op run --env-file .env --no-masking -- command args...`. Otherwise, it runs the command directly without requiring 1Password. CI bypasses reference detection with `COMPOSE_DISABLE_ENV_FILE=1`.

Credentials are available only to the command and its child processes; your terminal's environment stays unchanged. The helper does not write resolved credentials to disk. Already-started containers retain their configured credentials until recreated or removed.

Output masking is disabled so Compose keeps its normal terminal display. Avoid commands that print the environment or resolved Compose configuration. 1Password may request authorization; prompt frequency depends on its settings and lock state. Each invocation fetches the current values without opening a credential-loaded shell.

For native commands requiring credentials, use the same helper:

```sh
./scripts/1password.sh uv run --all-packages --locked pytest -m integration
```

No direnv, `.envrc`, mounted file, or Developer Environment is required. Preserve existing database and pgAdmin credentials when switching configuration providers.

See [1Password's op run reference](https://www.1password.dev/cli/reference/commands/run).

## Variables

| Variable | Requirement | Purpose / default |
|---|---|---|
| `POSTGRES_USER` | Required by Compose | Database role; initializes it on first startup |
| `POSTGRES_PASSWORD` | Required by Compose | Database password |
| `PGADMIN_EMAIL` | Required by Compose | Initial pgAdmin login email |
| `PGADMIN_PASSWORD` | Required by Compose | Initial pgAdmin login password |
| `POSTGRES_HOST` | Optional for native processes | `localhost`; Compose sets `postgres` inside API/worker containers |
| `POSTGRES_PORT` | Optional for native processes | `5432`; Compose uses the container port `5432` |
| `POSTGRES_DB` | Optional | `postgres` |
| `OPENAI_API_KEY` | Optional; future integrations | Model credential; not consumed yet |
| `LOGFIRE_TOKEN` | Optional; future integrations | Observability credential; not consumed yet |
| `API_BASE_URL` | Optional | `http://localhost:8000`; Compose uses `http://api:8000` |
| `FRONTEND_BASE_URL` | Optional | Browser test target; `http://localhost:3000` |

Compose currently validates pgAdmin credentials even when its optional profile is not started, so provide all four required variables. Additional variables in `.env` are not automatically passed into containers.

API and worker construct PostgreSQL connection strings from `POSTGRES_*` settings and escape special characters in credentials. No `DATABASE_URL` or `COMPOSE_DATABASE_URL` fields are needed.

Compose maps `PGADMIN_EMAIL` and `PGADMIN_PASSWORD` to the `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD` names required by the official pgAdmin image.

## Existing data and CI

PostgreSQL and pgAdmin initialize credentials only when their data volumes are first created. Updating `.env` or a 1Password vault item does not change an existing database role or pgAdmin account password; rotate those separately if needed.

CI uses explicit disposable test credentials and disables automatic `.env` loading. It requires neither 1Password nor direnv.
