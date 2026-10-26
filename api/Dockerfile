FROM ghcr.io/astral-sh/uv:0.13.5 AS uv
FROM python:3.13-slim-bookworm
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
COPY api/pyproject.toml ./api/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --package agora-api --no-dev --no-install-workspace
COPY api/src ./api/src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --package agora-api --no-dev --no-editable
RUN useradd --uid 10001 --create-home agora
USER agora
EXPOSE 8000
CMD ["uvicorn", "agora_api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
