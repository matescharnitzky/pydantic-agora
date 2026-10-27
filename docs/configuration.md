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

Keep credentials in a 1Password Developer Environment. Your ignored `.env` contains its ID and non-secret local settings:

```dotenv
OP_ENVIRONMENT_ID=your-environment-id
```

Keep `POSTGRES_USER`, `POSTGRES_PASSWORD`, `PGADMIN_EMAIL`, `PGADMIN_PASSWORD`, `OPENAI_API_KEY`, and `LOGFIRE_TOKEN` in the Environment. Preserve existing database and pgAdmin credentials when switching configuration providers. Keep `POSTGRES_DB` in `.env` rather than duplicating it in 1Password.

Install 1Password CLI and enable its integration in the desktop app. Load credentials once into a new development shell:

```sh
make env
make up
make pgadmin
make smoke
# Run other commands in the same shell as needed.
exit
```

`make env` opens a child shell with credentials loaded. `make up`, `make pgadmin`, and `make down` run Docker Compose directly; they do not fetch credentials themselves. Contributors using ordinary `.env` credentials skip `make env`.

`scripts/1password.sh` reads one unquoted `OP_ENVIRONMENT_ID=your-id` line and loads the Environment through `op run --env-file .env --environment ID`. It passes the variables directly to the new shell, with output masking disabled to preserve terminal behavior. It does not source `.env` as shell code or write resolved credentials to disk. Environment values take precedence over local dotenv values and inherited shell values.

1Password may request authorization when the session starts; prompt frequency depends on its settings and lock state. Subsequent commands reuse the loaded credentials. If values change in 1Password, exit and start a new session. Locking 1Password does not revoke variables already loaded into running processes.

Credentials remain available to every process started inside that shell, including coding agents, until those processes exit. Exiting the shell leaves the original terminal unchanged; already-started containers retain their configured credentials until recreated or removed. Compose has its normal terminal display and no output masking. Avoid commands that print the environment or resolved Compose configuration.

A Make command cannot change its parent terminal's environment, which is why `make env` starts a child shell. No direnv, `.envrc`, or mounted file is needed. If a coding agent uses fresh shells for each tool call, load credentials and run its command in one invocation:

```sh
./scripts/1password.sh uv run --all-packages --locked pytest -m integration
```

The helper also supports ordinary commands when no Environment ID is configured; it runs them directly. CI disables dotenv loading and supplies its own disposable credentials.

See [1Password's op run reference](https://www.1password.dev/cli/reference/commands/run).

## Variables

| Variable | Requirement | Purpose / default |
|---|---|---|
| `OP_ENVIRONMENT_ID` | Optional | 1Password Environment ID; not a credential |
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

PostgreSQL and pgAdmin initialize credentials only when their data volumes are first created. Updating `.env` or a 1Password Environment does not change an existing database role or pgAdmin account password; rotate those separately if needed.

CI uses explicit disposable test credentials and disables automatic `.env` loading. It requires neither 1Password nor direnv.
