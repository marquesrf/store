# syntax=docker/dockerfile:1

# ---- builder: resolve and install deps into a self-contained venv ----
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install deps first (cached layer) using only the lockfiles, so app code
# changes don't bust the dependency cache.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Then install the project itself.
COPY src ./src
COPY README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---- runtime: slim image with just the venv + source ----
FROM python:3.14-slim-bookworm

WORKDIR /app

# Run as non-root.
RUN useradd --create-home --uid 1000 app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/src /app/src

ENV PATH="/app/.venv/bin:$PATH"
USER app
EXPOSE 8000

CMD ["uvicorn", "store.entrypoints.api:app", "--host", "0.0.0.0", "--port", "8000"]
