FROM ghcr.io/astral-sh/uv:0.13.5 AS uv

FROM python:3.13-slim-bookworm AS build
WORKDIR /app
ENV UV_LINK_MODE=copy
COPY --from=uv /uv /usr/local/bin/uv

# Cache dependencies separately from application source.
COPY pyproject.toml uv.lock ./
COPY worker/pyproject.toml ./worker/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package agora-worker \
        --no-dev --no-install-workspace

# Install the service as a non-editable package.
COPY worker/src ./worker/src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package agora-worker \
        --no-dev --no-editable

FROM build AS development
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/worker/src" \
    PYTHONUNBUFFERED=1
RUN useradd --uid 10001 --create-home agora \
    && chown -R agora:agora /app/worker/src
USER agora
CMD ["python", "-m", "agora_worker"]

FROM python:3.13-slim-bookworm AS runtime
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN useradd --uid 10001 --create-home agora
COPY --from=build /app/.venv /app/.venv

USER agora
CMD ["python", "-m", "agora_worker"]
