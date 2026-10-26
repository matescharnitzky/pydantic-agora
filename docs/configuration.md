# Configuration

Secrets live in **1Password → Development → pydantic-agora**. `.envrc` fetches that item once, then explicitly lists each required field using `export_secret NAME`.

The helper looks up the field by its exact label and exports its value. Loading stops with an error naming the field if it is missing, empty, or duplicated. Secret values are never included in the error. Quotes, spaces, and multiline values are exported literally, without evaluating their contents.

Use the exact names below: the OpenAI field is `OPENAI_API_KEY`, not `OPENAI_APY_KEY`. To introduce another required field, add its explicit export line to `.envrc` and document it here.

## Setup

1. Install the tools:

   ```sh
   brew install direnv jq
   brew install --cask 1password-cli
   ```

2. Enable **Settings → Developer → Integrate with 1Password CLI** in the 1Password desktop app. Sign in and ensure the item and fields above exist.
3. Add `eval "$(direnv hook zsh)"` to the end of `~/.zshrc`, then restart the shell.
4. Review `.envrc` and run `direnv allow` in the repository. Approve the 1Password access prompt. Run `make up` once the variables have loaded.

Use `direnv reload` after changing values in 1Password. direnv unloads the project variables when you leave the directory. For a shell without the hook, use `direnv exec . make up` after allowing the file. Resolved secrets are available to processes launched from that shell; do not print the environment or resolved Compose configuration into logs.

`.envrc` and the Makefile set `COMPOSE_DISABLE_ENV_FILE=1` to disable Compose's automatic `.env` loading. Application settings read process environment variables, not dotenv files. The root `.env` file is neither required nor used by these commands; remove any old local copy yourself once no longer needed.

## Variables

Credentials and other secrets are fetched from **Development → pydantic-agora**. Public defaults are defined directly in `.envrc` and mirrored by application defaults where needed.

| Variable | Source | Purpose / default |
|---|---|---|
| `OPENAI_API_KEY` | 1Password, required | Credential for future model integrations |
| `LOGFIRE_TOKEN` | 1Password, required | Write token for future instrumentation |
| `POSTGRES_PASSWORD` | 1Password, required | PostgreSQL password, including local test credentials |
| `PGADMIN_PASSWORD` | 1Password, required | pgAdmin web login password |
| `POSTGRES_HOST` | `.envrc` | `localhost` locally; Compose sets `postgres` inside API/worker containers |
| `POSTGRES_PORT` | `.envrc` | `5432` |
| `POSTGRES_DB` | `.envrc` | `agora` |
| `POSTGRES_USER` | 1Password, required | PostgreSQL username; use the existing local role (`agora`) |
| `PGADMIN_EMAIL` | 1Password, required | pgAdmin login email; use the existing local account |
| `COMPOSE_DISABLE_ENV_FILE` | `.envrc` and Makefile | `1` disables automatic `.env` loading |
| `API_BASE_URL` | Optional override | Defaults to `http://127.0.0.1:8000`; Compose uses `http://api:8000` |
| `FRONTEND_BASE_URL` | Optional override | Browser test target; defaults to `http://127.0.0.1:3000` |

API and worker construct their PostgreSQL connection strings from `POSTGRES_*` settings and escape special characters in credentials. No `DATABASE_URL` or `COMPOSE_DATABASE_URL` fields are needed; existing fields with those names in 1Password are ignored. The host is the only connection setting that changes between native processes and containers.

The helper exports each explicitly requested secret unchanged. Unlisted fields in the item are not exported. PostgreSQL and pgAdmin credentials need to be added to the existing item once; the repository has not changed real 1Password values. OpenAI and Logfire secrets are loaded in preparation for future integrations and are not consumed by the current application.

Compose maps `PGADMIN_EMAIL` and `PGADMIN_PASSWORD` to the `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD` names required by the pgAdmin image. The project and 1Password use the shorter names.

## Existing data and CI

PostgreSQL and pgAdmin initialize passwords only when their data volumes are first created. When adopting 1Password for an existing local stack, store the passwords already in use. Changing a field in 1Password does not change the corresponding database or pgAdmin account password; rotate the account password separately before reloading the environment.

CI creates a disposable PostgreSQL instance with job-local test credentials declared in its workflow. It does not read your personal 1Password vault. No production or model credentials are needed for the current tests.

Logfire remains the observability service. Its managed variables can later hold prompts and feature configuration; database and account passwords stay in 1Password.
