# Agora

An independent playground for exploring the Pydantic AI ecosystem. Not affiliated with or endorsed by Pydantic.

## Run locally

Install Docker with Compose. Create your local configuration:

```sh
cp .env.example .env
```

Set the four credential values in `.env`, then start the stack:

```sh
make up
```

If you use 1Password, put `op://` secret references in `.env` instead of credential values. The same Make commands resolve them automatically for each Compose command. See [configuration setup](docs/configuration.md).

- [Application](http://localhost:3000)
- [API docs](http://localhost:8000/docs)
- [pgAdmin](http://localhost:5050)

Stop everything with `make down`. Database data is preserved. This is a local development stack; published ports bind to localhost.

## Development

Use Python 3.13, uv, and Node 24 with npm. Python requirements are declared in the services' `pyproject.toml` files.

```sh
make install
make check
make smoke  # Requires the running stack and Playwright Chromium
```

See [development commands and pgAdmin login](docs/development.md), [architecture](docs/architecture.md), and [contributor guidance](AGENTS.md). Planned work is tracked in [GitHub issues](https://github.com/matescharnitzky/pydantic-agora/issues).

Browse the rendered [documentation](http://localhost:3000/docs) while the stack is running. Sources live in `docs/`.
