FROM ghcr.io/astral-sh/uv:0.13.5 AS uv

FROM python:3.13-slim-bookworm AS build
WORKDIR /app
ENV UV_LINK_MODE=copy
COPY --from=uv /uv /usr/local/bin/uv

# Cache dependencies separately from application source.
COPY pyproject.toml uv.lock ./
COPY api/pyproject.toml ./api/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package agora-api \
        --no-dev --no-install-workspace

# Install the service as a non-editable package.
COPY api/src ./api/src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package agora-api \
        --no-dev --no-editable

FROM build AS development
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/api/src" \
    PYTHONUNBUFFERED=1
RUN useradd --uid 10001 --create-home agora \
    && chown -R agora:agora /app/api/src
USER agora
CMD ["uvicorn", "agora_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app/api/src"]

FROM python:3.13-slim-bookworm AS runtime
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN useradd --uid 10001 --create-home agora
COPY --from=build /app/.venv /app/.venv

USER agora
EXPOSE 8000
CMD ["uvicorn", "agora_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
