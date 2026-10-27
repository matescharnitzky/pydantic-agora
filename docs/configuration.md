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

Install 1Password CLI and enable its integration in the desktop app, then use the same commands as everyone else:

```sh
make up
make pgadmin
make down
make smoke
```

The Compose targets (`up`, `pgadmin`, and `down`) call `scripts/with-env.sh`. If a non-empty `OP_ENVIRONMENT_ID` is present in `.env`, the script uses `op run --env-file .env --environment ID` to inject secrets into the command. Otherwise, it runs Compose directly, which reads ordinary dotenv values or exported variables. Only users who configure an Environment ID need 1Password CLI.

Write the ID as one unquoted `OP_ENVIRONMENT_ID=your-id` line. 1Password parses the rest as dotenv data; the script does not source `.env` as shell code. Environment values take precedence over `.env` and inherited shell values. CI disables automatic dotenv loading, which also skips 1Password detection.

The wrapper preserves exit status and never prints resolved variables. 1Password may reuse authorization, but prompt frequency depends on its settings and lock state, not the terminal session. Do not run commands that dump the environment or resolved Compose configuration.

`make smoke` tests the already-running services and needs no credentials. For a native command that needs the database credentials, use the helper directly:

```sh
./scripts/with-env.sh uv run --all-packages --locked pytest -m integration
```

Secrets are scoped to the command and its subprocesses; they do not remain in your terminal afterward. Coding agents use the same Make commands and may need you to approve a 1Password prompt. This is a convenience, not an access barrier: an injected command can access its environment. No direnv, `.envrc`, or mounted file is needed.

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
