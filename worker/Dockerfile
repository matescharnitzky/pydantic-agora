FROM ghcr.io/astral-sh/uv:0.13.5 AS uv
FROM python:3.13-slim-bookworm
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock .python-version ./
COPY api/pyproject.toml ./api/pyproject.toml
COPY worker/pyproject.toml ./worker/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --package agora-worker --no-dev --no-install-workspace
COPY worker/src ./worker/src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --package agora-worker --no-dev --no-editable
RUN useradd --uid 10001 --create-home agora
USER agora
CMD ["python", "-m", "agora_worker"]
