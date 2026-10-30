# Agora

Agora is a runtime for the Pydantic ecosystem. Not affiliated with or endorsed by Pydantic.

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
| `OPENAI_API_KEY` | Required in the worker for model generation; optional for dummy workflows |
| `LOGFIRE_TOKEN` | Optional; sends API and worker traces to Logfire |
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
make test-db  # Database/worker integration tests; requires the running stack
make smoke    # Bruno API checks and Playwright user scenarios; requires the running stack
make test-models  # Explicit live OpenAI checks and Pydantic Evals; incurs model usage
```

Run development mode in Docker:

```sh
make dev  # Start the stack and watch for changes; keep this terminal open
```

### Model generation

`GET /capabilities` lists the available capability and its schemas. Submit generation through
`POST /workflows`, then retrieve its status/result from `GET /workflows/{id}`:

```json
{
  "operation": "generate",
  "inputs": {
    "prompt": "Extract the name from: Ada Lovelace.",
    "instructions": "Extract only the requested information.",
    "model": "gpt-5-mini",
    "output_schema": {
      "type": "object",
      "properties": {"name": {"type": "string"}},
      "required": ["name"],
      "additionalProperties": false
    }
  }
}
```

Omit `output_schema` for plain text. Schemas use JSON Schema draft 2020-12 without references;
object, array, and scalar results are validated in the worker. Provider-specific model/schema
restrictions can still fail execution. Results contain `output` and the responding `model`.
The API never receives the provider key. Model requests use OpenAI Responses and default to
`gpt-5-mini`; set `inputs.model` to choose another compatible model.

`make check` and `make smoke` do not call a live model. `make test-models` runs the live Bruno
workflow checks and three Pydantic Evals cases (text, extraction, classification). Keep generated
evaluation reports untracked. Service responsibilities and recovery behavior are in
[architecture.md](docs/architecture.md).

### Remote development

Run `make dev`, approve 1Password, and keep the laptop awake with the process running.
